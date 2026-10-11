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

/** Split a segment where its tangent runs parallel to d; there the nib sweep folds over. */
function displayNibSplit(segment, d){
  if(segment.length === 2) return [segment];
  const cross = (a,b) => (a[0]-b[0])*d[1]-(a[1]-b[1])*d[0];
  const q0 = cross(segment[1],segment[0]), q1 = cross(segment[2],segment[1]), q2 = cross(segment[3],segment[2]);
  // cross(B'(t), d)/3 = q0(1-t)^2 + 2 q1 (1-t) t + q2 t^2
  const a = q0-2*q1+q2, b = 2*(q1-q0), c = q0, roots = [];
  if(Math.abs(a) < 1e-12){ if(Math.abs(b) > 1e-12) roots.push(-c/b); }
  else { const disc = b*b-4*a*c; if(disc >= 0) roots.push((-b-Math.sqrt(disc))/(2*a), (-b+Math.sqrt(disc))/(2*a)); }
  const pieces = []; let rest = segment, used = 0;
  for(const t of roots.filter(t => t > 1e-6 && t < 1-1e-6).sort((x,y) => x-y)){
    const local = (t-used)/(1-used);
    let points = rest;
    // de Casteljau: the left edge becomes the first piece, the right edge the remainder.
    const left = [points[0]], right = [points[3]];
    while(points.length > 1){
      points = points.slice(1).map((p,i) => [points[i][0]*(1-local)+p[0]*local, points[i][1]*(1-local)+p[1]*local]);
      left.push(points[0]); right.unshift(points[points.length-1]);
    }
    pieces.push(left); rest = right; used = t;
  }
  pieces.push(rest);
  return pieces;
}

/** Contours of a skeleton swept by the flat nib, as exact shifted copies of each curve piece.
    For a convex nib K and a connected path C: C+K = (C + each edge of K) ∪ (start of C + K). */
function displayNibContours(paths, width, cut){
  const n = nibShape(width, cut.contrast || 1, cut.penAngle || 0, cut.ends !== 'flat');
  const u = [n.c, -n.s], v = [n.s, n.c];   // SVG y runs down
  const hu = n.round ? (n.length-n.thick)/2 : n.length/2, hv = n.round ? 0 : n.thick/2;
  const corners = (hv ? [[hu,hv],[-hu,hv],[-hu,-hv],[hu,-hv]] : [[hu,0],[-hu,0]])
    .map(([a,b]) => [a*u[0]+b*v[0], a*u[1]+b*v[1]]);
  const edges = hv ? corners.map((p,i) => [p, corners[(i+1)%4]]) : [[corners[0], corners[1]]];
  const shift = (points, o) => points.map(p => [p[0]+o[0], p[1]+o[1]]);
  const contours = [];
  for(const path of paths){
    const segments = path.segments.slice();
    if(!segments.length) continue;
    const first = segments[0][0], end = segments[segments.length-1][segments[segments.length-1].length-1];
    if(path.closed && Math.hypot(first[0]-end[0], first[1]-end[1]) > 1e-7) segments.push([end, first]);
    for(const [a,b] of edges){
      const d = [b[0]-a[0], b[1]-a[1]];
      for(const segment of segments) for(const piece of displayNibSplit(segment, d)){
        const back = shift(piece, b).reverse();
        contours.push([shift(piece, a), [shift(piece, a)[piece.length-1], back[0]], back, [back[back.length-1], shift(piece, a)[0]]]);
      }
    }
    if(hv) contours.push(corners.map((p,i) => [[first[0]+p[0], first[1]+p[1]], [first[0]+corners[(i+1)%4][0], first[1]+corners[(i+1)%4][1]]]));
  }
  return {contours, nib:n};
}

/** One SVG path of nib contours, all turned the same way so overlaps fill as a union. */
function displayNibPath(contours){
  const coord = p => p.map(x => x.toFixed(5)).join(' ');
  return contours.map(contour => {
    let area = 0, previous = contour[0][0];
    for(const segment of contour) for(let i = 1; i <= 8; i++){
      const p = displaySample(segment, i/8); area += previous[0]*p[1]-p[0]*previous[1]; previous = p;
    }
    const ordered = area < 0 ? contour.slice().reverse().map(s => s.slice().reverse()) : contour;
    return 'M'+coord(ordered[0][0]) + ordered.map(s => (s.length === 2 ? 'L' : 'C') + s.slice(1).map(coord).join(' ')).join('') + 'Z';
  }).join('');
}

/** Flat nib body: swept strokes and outlined fills, round dots kept; no caps are needed. */
function displayNibBody(g, cut){
  let body = '';
  const draw = (d, width) => {
    const {contours, nib} = displayNibContours(displaySegments(d), width, cut);
    if(!contours.length) return;
    // A rounded nib is the sharp sweep grown by half its thickness: fill plus a round stroke.
    body += `<path d="${displayNibPath(contours)}" fill="currentColor" fill-rule="nonzero"`
      + (nib.round ? ` stroke="currentColor" stroke-width="${nib.thick.toFixed(5)}" stroke-linejoin="round" stroke-linecap="round"/>` : '/>');
  };
  let rest = g.body.replace(/<path d="([^"]+)" fill="none"[^>]*stroke-width="([^"]+)"[^>]*\/>/g, (tag,d,width) => { draw(d, +width); return ''; });
  rest = rest.replace(/<path data-fill="1" d="([^"]+)"[^>]*stroke-width="([^"]+)"[^>]*\/>/g, (tag,d,width) => {
    if(+width > 0) draw(d, +width);
    return tag.replace(/stroke-width="[^"]+"/, 'stroke-width="0"');
  });
  return body + rest;
}

/** Emit a Boolean-safe stroke preview with terminal joins and perpendicular caps. */
function displayPenBody(g, cut){
  if(cut.pen === 'nib') return displayNibBody(g, cut);
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
            // A Bezier and every sampled chord lie in its control-point box.
            // Compare in the same pen coordinates as the contact test below.
            const control = j === owner ? segment : segment.map(transform);
            const radius = j === owner ? 2 : strokes[j].width/2;
            const xs = control.map(p => p[0]), ys = control.map(p => p[1]);
            if(query[0] < Math.min(...xs)-radius-1e-7 || query[0] > Math.max(...xs)+radius+1e-7 ||
               query[1] < Math.min(...ys)-radius-1e-7 || query[1] > Math.max(...ys)+radius+1e-7) continue;
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
