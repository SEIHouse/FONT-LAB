/* Display terminal construction; shared by every live cut and glyph. */

/** Decode engine paths as native Bezier segments, retaining their centerlines. */
function displaySegments(d){
  const tokens = d.match(/[MLCZ]|-?\d+(?:\.\d+)?/g) || [], paths = [];
  let i = 0, point, path;
  const pt = () => [+tokens[i++], +tokens[i++]];
  while(i < tokens.length){
    const verb = tokens[i++];
    if(verb === 'M'){ point = pt(); path = {segments:[], closed:false}; paths.push(path); }
    else if(verb === 'Z'){ path.closed = true; }
    else {
      const points = verb === 'C' ? [pt(), pt(), pt()] : [pt()];
      path.segments.push([point, ...points]); point = points[points.length-1];
    }
  }
  return paths;
}

/** Evaluate a Bezier without changing the glyph's drawing. */
function displaySample(segment, t){
  let points = segment;
  while(points.length > 1) points = points.slice(1).map((b,i) =>
    [points[i][0]*(1-t)+b[0]*t, points[i][1]*(1-t)+b[1]*t]);
  return points[0];
}

/** Resolve repeated endpoint controls and return the inward terminal tangent. */
function displayTangent(segment, end){
  const points = end ? [...segment].reverse() : segment;
  for(const point of points.slice(1)){
    const v = [point[0]-points[0][0], point[1]-points[0][1]], length = Math.hypot(...v);
    if(length > 1e-7) return v.map(x => x/length);
  }
  return [0,0];
}

/** Get the oval-pen matrices in SVG coordinates. */
function displayPen(contrast, angle){
  const t = -angle*Math.PI/180, c = Math.cos(t), s = Math.sin(t);
  const matrix = k => [c*c+k*s*s, (1-k)*c*s, (1-k)*c*s, s*s+k*c*c];
  return {into:matrix(contrast), out:matrix(1/contrast)};
}

/** Construct a flat face perpendicular to the final, slanted stroke. */
function displayCap(point, inward, width, matrix, shear){
  let [tx,ty] = inward.map(x => -x);
  tx += shear*ty;
  const norm = Math.hypot(tx,ty); tx /= norm; ty /= norm;
  const nx = -ty, ny = tx, radius = width/2;
  const [a,b,c,d] = matrix, fa = a+shear*c, fb = b+shear*d;
  const xx = fa*fa+fb*fb, xy = fa*c+fb*d, yy = c*c+d*d;
  const hn = Math.sqrt(nx*(xx*nx+xy*ny)+ny*(xy*nx+yy*ny));
  const ht = Math.sqrt(tx*(xx*tx+xy*ty)+ty*(xy*tx+yy*ty));
  const vx = radius*(xx*nx+xy*ny)/hn, vy = radius*(xy*nx+yy*ny)/hn;
  const px = point[0]+shear*point[1], py = point[1];
  const ex = px+radius*ht*tx, ey = py+radius*ht*ty;
  return [[px+vx,py+vy], [ex+radius*hn*nx,ey+radius*hn*ny],
    [ex-radius*hn*nx,ey-radius*hn*ny], [px-vx,py-vy]].map(([x,y]) => [x-shear*y,y]);
}

/** Emit a Boolean-safe stroke preview with terminal joins and perpendicular caps. */
function displayPenBody(g, cut){
  const matrix = displayPen(cut.contrast || 1, cut.penAngle || 0);
  const shear = -Math.tan((cut.slant || 0)*Math.PI/180), flat = cut.ends === 'flat';
  const transform = ([x,y]) => [matrix.into[0]*x+matrix.into[1]*y, matrix.into[2]*x+matrix.into[3]*y];
  const coord = p => p.map(x => x.toFixed(5)).join(' ');
  const svg = (paths, width, cap) => {
    const d = paths.map(path => path.segments.map((s,i) =>
      (i === 0 ? 'M'+coord(transform(s[0])) : '') +
      (s.length === 2 ? 'L' : 'C') + s.slice(1).map(p => coord(transform(p))).join(' ')
    ).join('') + (path.closed ? 'Z' : '')).join('');
    return `<path d="${d}" fill="none" stroke="currentColor" stroke-width="${width}" stroke-linecap="${cap}" stroke-linejoin="${cut.joins === 'sharp' ? 'miter' : 'round'}" stroke-miterlimit="2"/>`;
  };
  const strokes = [], terminals = [];
  let rest = g.body.replace(/<path d="([^"]+)" fill="none"[^>]*stroke-width="([^"]+)"[^>]*\/>/g, (tag,d,width) => {
    const owner = strokes.length, paths = displaySegments(d);
    for(const path of paths){
      if(!path.segments.length) continue;
      const first = path.segments[0][0], lastSegment = path.segments[path.segments.length-1];
      const last = lastSegment[lastSegment.length-1];
      if(Math.hypot(first[0]-last[0], first[1]-last[1]) < 1e-7) path.closed = true;
      if(!path.closed) for(const [point,segment,end] of [[first,path.segments[0],false],[last,lastSegment,true]]){
        terminals.push({owner,point,inward:displayTangent(segment,end),width:+width,path,end});
      }
    }
    strokes.push({paths,width:+width}); return '';
  });
  rest = rest.replace(/<path data-fill="1" d="([^"]+)"[^>]*stroke-width="([^"]+)"[^>]*\/>/g, (tag,d,width) => {
    if(+width > 0) strokes.push({paths:displaySegments(d),width:+width});
    return tag.replace(/stroke-width="[^"]+"/, 'stroke-width="0"');
  });
  let caps = '', joins = '';
  if(flat){
    // Keep dots in the same (circular) coordinates used by the font builder.
    const dots = [...rest.matchAll(/<circle cx="([^"]+)" cy="([^"]+)" r="([^"]+)"/g)].map(m => m.slice(1).map(Number));
    const distance = (p,a,b) => {
      const vx = b[0]-a[0], vy = b[1]-a[1], q = Math.max(0,Math.min(1,
        ((p[0]-a[0])*vx+(p[1]-a[1])*vy)/(vx*vx+vy*vy || 1)));
      return Math.hypot(p[0]-a[0]-q*vx, p[1]-a[1]-q*vy);
    };
    for(const terminal of terminals){
      const {owner,point,inward,width,path,end} = terminal;
      const knot = terminals.some(t => t.owner !== owner && Math.hypot(t.point[0]-point[0],t.point[1]-point[1]) <= 2);
      let attached = knot || dots.some(([x,y,r]) => Math.hypot(x-point[0],y-point[1]) <= r);
      for(let j = 0; !attached && j < strokes.length; j++){
        for(const otherPath of strokes[j].paths){
          let segments = otherPath.segments;
          if(j === owner && otherPath === path) segments = end ? segments.slice(0,-1) : segments.slice(1);
          const query = j === owner ? point : transform(point);
          for(const segment of segments){
            const steps = Math.max(1,Math.ceil(segment.slice(1).reduce((sum,p,i) =>
              sum+Math.hypot(p[0]-segment[i][0],p[1]-segment[i][1]),0)));
            let a = j === owner ? segment[0] : transform(segment[0]);
            for(let i=1; i<=steps; i++){
              const sample = displaySample(segment,i/steps), b = j === owner ? sample : transform(sample);
              if(distance(query,a,b) <= (j === owner ? 2 : strokes[j].width/2)){ attached = true; break; }
              a = b;
            }
            if(attached) break;
          }
          if(attached) break;
        }
      }
      if(!attached && Math.hypot(...inward)){
        const points = displayCap(point,inward,width,matrix.out,shear);
        // SVG paints the body and cap separately. Overlap their contact edge
        // inside the stroke so antialiasing cannot leave a hairline at the seam.
        for(const i of [0,3]) points[i] = points[i].map((x,k) => x+3*inward[k]);
        caps += `<path d="M${points.map(coord).join('L')}Z" fill="currentColor"/>`;
      }
    }
    terminals.forEach((t,i) => terminals.slice(i+1).forEach(other => {
      if(t.owner === other.owner || Math.hypot(t.point[0]-other.point[0],t.point[1]-other.point[1]) > 2) return;
      const p = t.point.map((x,k) => (x+other.point[k])/2);
      // Let the join overlap both terminal bodies for the same antialiasing reason.
      const points = [p.map((x,k) => x+4*t.inward[k]),p,p.map((x,k) => x+4*other.inward[k])];
      joins += svg([{segments:[[points[0],points[1]],[points[1],points[2]]],closed:false}],Math.min(t.width,other.width),'butt');
    }));
  }
  const into = strokes.map(s => svg(s.paths,s.width,flat ? 'butt' : 'round')).join('') + joins;
  return `<g transform="matrix(${matrix.out.join(' ')} 0 0)">${into}</g>`+caps+rest;
}
