import test from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { build } from '../display/node_modules/esbuild/lib/main.js';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const srcDir = join(root, 'packages/elemental-title/src');

// Bundle internal engine modules in-memory via locked esbuild so pure Node tests run in <100ms
const entrySource = `
  export * as publicApi from './index.ts';
  export { sceneAnchors } from './engine/anchors.ts';
  export { registeredElementalEffects, resolveElementalEffect } from './engine/effects.ts';
  export { scaleFrame, pushFrame } from './engine/frames.ts';
  export { measurePolyline } from './engine/geometry.ts';
  export { composeLightning, lightning, lightningJolt } from './engine/lightning.ts';
  export { poison } from './engine/poison.ts';
  export { cadenceFor, tierProgramViolations, tiers } from './engine/program.ts';
  export { createRandom, hashString } from './engine/random.ts';
  export { ignoredSignatures, resolveRecipe, resolveRecipeEffect, resolveTier } from './engine/recipe.ts';
  export { primitiveEnd } from './engine/scene.ts';
  export { timelineDuration, describeTimeline } from './engine/timeline.ts';
  export { water } from './engine/water.ts';
  export { waterPoses, waterSurface } from './engine/water-surface.ts';
  export { createStageCoordinator, drawSignature } from './engine/coordinator.ts';
  export {
    defaultSignatureCadence,
    defineSignature,
    familiarSignatures,
    officialSignature,
    officialSignatures,
    resolveSignatures,
  } from './engine/signatures/index.ts';
`;

const compiled = await build({
  stdin: { contents: entrySource, resolveDir: srcDir, loader: 'ts' },
  bundle: true,
  format: 'esm',
  platform: 'browser',
  nodePaths: [join(root, 'display/node_modules')],
  write: false,
});

const engine = await import(
  `data:text/javascript;base64,${Buffer.from(compiled.outputFiles[0].text).toString('base64')}`
);

function makeStage(text = 'Kept Reading', perLine = Infinity) {
  const em = 40;
  const glyphs = [];
  let index = 0;
  let column = 0;
  let row = 0;
  for (const character of text) {
    if (column >= perLine) {
      column = 0;
      row += 1;
    }
    if (/\s/u.test(character)) {
      index += 1;
      column += 1;
      continue;
    }
    const x = 32 + column * 30;
    const y = 56 + row * 56;
    const height = 46;
    const baseline = y + height * 0.79;
    glyphs.push({
      character,
      x,
      y,
      width: 28,
      height,
      inkTop: baseline - em * (/[A-Zbdfhklt]/.test(character) ? 0.7 : 0.47),
      inkBottom: baseline + em * (/[gjpqy]/.test(character) ? 0.21 : 0.02),
      center: { x: x + 14, y: y + height / 2 },
    });
    index += 1;
    column += 1;
  }
  const columns = Math.min(index, perLine);
  return {
    width: 32 * 2 + columns * 30,
    height: 56 + (row + 1) * 56 - 10 + 26,
    em,
    offset: { x: -32, y: -56 },
    text: { x: 32, y: 56, width: columns * 30, height: (row + 1) * 56 - 10 },
    glyphs,
  };
}

function context(seed = 7, tier = 'legendary', params = {}) {
  return {
    tier,
    params,
    engaged: true,
    interactive: false,
    explicit: false,
    random: engine.createRandom(seed),
    key: 1,
    textSeed: 3,
  };
}

function primitivePoints(primitive) {
  switch (primitive.type) {
    case 'stroke':
      return primitive.spine;
    case 'traveler':
      return [
        ...primitive.path.map(([, x, y]) => ({ x, y })),
        ...primitive.sparks.flatMap((spark) => [
          spark,
          { x: spark.x + spark.dx, y: spark.y + spark.dy },
        ]),
      ];
    case 'shape':
      return [primitive.center];
    case 'dissolve':
      return primitive.fragments.flatMap((spark) => [
        spark,
        { x: spark.x + spark.dx, y: spark.y + spark.dy },
      ]);
    default:
      return [];
  }
}

test('tier programs never de-escalate and recipes map legacy intensities cleanly', () => {
  const effects = engine.registeredElementalEffects();
  assert.ok(effects.length >= 3);
  for (const effect of effects) {
    assert.deepEqual(engine.tierProgramViolations(effect.program), [], effect.id);
    for (const tier of engine.tiers) {
      for (const moment of Object.keys(effect.program[tier].cadence)) {
        assert.ok(effect.moments[moment] !== undefined, `${effect.id} ${tier} ${moment}`);
      }
    }
  }
  assert.deepEqual(engine.resolveRecipe('lightning', 'legendary'), {
    elements: ['lightning'],
    tier: 'legendary',
    signatures: [],
  });
  assert.equal(engine.resolveTier('subtle'), 'rare');
  assert.equal(engine.resolveTier('active'), 'epic');
  assert.equal(engine.resolveElementalEffect('toString'), undefined);
});

test('lightning composes deterministic arcs, bounded stage geometry, and transform/opacity-only jolts', () => {
  const stage = makeStage('Kept Reading');
  const a = engine.composeLightning(stage, {
    slot: 'still',
    tier: 'legendary',
    engaged: false,
    random: engine.createRandom(11),
    key: 11,
  });
  const b = engine.composeLightning(stage, {
    slot: 'still',
    tier: 'legendary',
    engaged: false,
    random: engine.createRandom(11),
    key: 11,
  });
  assert.deepEqual(a, b);

  for (const tier of engine.tiers) {
    const strike = engine.composeLightning(stage, {
      slot: 'strike',
      tier,
      engaged: true,
      random: engine.createRandom(42),
      key: 42,
    });
    const motions = engine.lightningJolt(stage, strike, {
      tier,
      engaged: true,
      random: engine.createRandom(42),
    });
    assert.equal(motions.length, 1);
    for (const kf of motions[0].keyframes) {
      for (const key of Object.keys(kf)) {
        assert.ok(['transform', 'opacity', 'offset', 'easing'].includes(key), key);
      }
    }
    assert.deepEqual(motions[0].keyframes.at(-1), motions[0].keyframes[0]);
  }
});

test('water and poison preserve morph-compatible poses, multi-line waves, and slow-motion scaling', () => {
  for (const tier of engine.tiers) {
    const poses = engine.waterPoses(engine.water.program[tier].params);
    assert.equal(poses.length, 17);
    for (const key of Object.keys(poses[0])) {
      const commands = poses[0][key].replace(/[^a-zA-Z]/g, '');
      for (const pose of poses) {
        assert.doesNotMatch(pose[key], /NaN|Infinity/);
        assert.equal(pose[key].replace(/[^a-zA-Z]/g, ''), commands);
      }
    }
  }
  const wrapped = makeStage('Wayfinder of the Jagged Fjord', 10);
  const waveTimeline = engine.water.timeline(
    'wave',
    wrapped,
    context(7, 'legendary', engine.water.program.legendary.params)
  );
  const waveFrame = waveTimeline.cues.find((c) => c.type === 'frame').frame;
  assert.equal(waveFrame.material.type, 'water');
  assert.ok(waveFrame.material.waves.length > 1);

  const scaled = engine.scaleFrame(waveFrame, 0.25);
  assert.equal(scaled.life, waveFrame.life * 4);
  assert.equal(scaled.material.waves[0].duration, waveFrame.material.waves[0].duration * 4);

  const dripTimeline = engine.poison.timeline(
    'drip',
    makeStage('Kept Reading'),
    context(7, 'legendary', engine.poison.program.legendary.params)
  );
  assert.deepEqual(
    dripTimeline.beats.map((b) => b.label),
    ['gather', 'release']
  );
});

test('official familiar signatures stay closed, isolated from engine code, and obey eligibility rules', () => {
  assert.deepEqual(Object.keys(engine.familiarSignatures), ['quill']);
  assert.deepEqual(
    engine.officialSignatures().map((s) => s.id),
    ['quill/stormwrit', 'quill/true-north']
  );
  assert.equal(Object.isFrozen(engine.familiarSignatures), true);
  assert.equal(engine.officialSignature('toString'), undefined);
  assert.deepEqual(
    Object.keys(engine.publicApi).filter((name) => /signature|regist/i.test(name)),
    []
  );

  // Familiar names must never leak into engine/*.ts outside engine/signatures/
  const engineDir = join(srcDir, 'engine');
  const engineFiles = readdirSync(engineDir).filter((name) => /\.tsx?$/.test(name));
  assert.ok(engineFiles.length > 10);
  for (const name of engineFiles) {
    const code = readFileSync(join(engineDir, name), 'utf8');
    assert.doesNotMatch(code, /quill|stormwrit|true.?north/i, name);
  }

  const ids = ['quill/stormwrit', 'quill/true-north'];
  assert.deepEqual(
    engine
      .resolveSignatures(ids, { element: 'lightning', tier: 'legendary', engine: true })
      .eligible.map((s) => s.id),
    ids
  );
  assert.deepEqual(
    engine.resolveSignatures(ids, { element: 'lightning', tier: 'epic', engine: true }).eligible,
    []
  );
  assert.deepEqual(
    engine.resolveSignatures(ids, { element: 'fire', tier: 'legendary', engine: false }).ignored[0]
      .reason,
    'it needs the lightning element'
  );
});

test('every official signature is a deterministic fancy underline beneath & beside the name', () => {
  const stages = [
    ['one-letter', makeStage('Q')],
    ['40-letter', makeStage('Archivist of the Storm-Written Library X')],
    ['two-line wrapped', makeStage('Wayfinder of the Jagged Fjord', 16)],
    ['three-line wrapped', makeStage('Nine Heavens Pavilion Of Ink', 10)],
  ];

  for (const signature of engine.officialSignatures()) {
    const baseStage = makeStage('Kept Reading');
    const first = signature.timeline(baseStage, context(11));
    assert.deepEqual(signature.timeline(baseStage, context(11)), first);
    assert.notDeepEqual(signature.timeline(baseStage, context(12)), first);
    assert.equal(first.moment, 'signature');
    assert.ok(engine.timelineDuration(first) >= 2000 && engine.timelineDuration(first) < 5000);
    assert.deepEqual(
      first.beats.map((b) => b.label),
      ['arrival', 'act', 'mark', 'exit']
    );

    // Never moves or recolors letters
    assert.deepEqual(new Set(first.cues.map((c) => c.type)), new Set(['scene', 'edge-light']));
    assert.doesNotMatch(JSON.stringify(first), /color|fill|background|textFill/i);

    // Front strokes stay thin so name remains readable
    for (const cue of first.cues) {
      if (cue.type === 'scene') {
        for (const prim of cue.primitives) {
          if (prim.type === 'stroke') {
            for (const run of prim.runs.front) {
              assert.ok(Math.max(...run.widths) <= baseStage.em * 0.06);
            }
          }
        }
      }
    }

    // "is a fancy underline": beneath the name, ending beside it, nothing above
    for (const [label, stage] of stages) {
      const anchors = engine.sceneAnchors(stage);
      const { em } = stage;
      const tl = signature.timeline(stage, context(7));
      const scenes = tl.cues.filter((c) => c.type === 'scene');
      const primitives = scenes.flatMap((c) => c.primitives);
      assert.ok(primitives.length > 3, `${signature.id} ${label}`);

      for (const pt of primitives.flatMap(primitivePoints)) {
        assert.ok(pt.x >= 0 && pt.x <= stage.width, `${signature.id} ${label} x=${pt.x}`);
        assert.ok(pt.y >= 0 && pt.y <= stage.height, `${signature.id} ${label} y=${pt.y}`);
      }

      const drawn = primitives.flatMap((p) =>
        p.type === 'stroke' || p.type === 'traveler' ? primitivePoints(p) : []
      );
      const last = anchors.lines.at(-1);
      for (const pt of drawn) {
        for (const line of anchors.lines) {
          const over =
            pt.x > line.start + em * 0.15 &&
            pt.x < (line === last ? line.end - em * 0.35 : line.end) &&
            pt.y > line.baseline - em * 1.0 &&
            pt.y < line.baseline + em * 0.3;
          if (over) {
            assert.ok(pt.y > line.baseline - em * 0.1, `${signature.id} ${label} crossed letters`);
          }
        }
      }

      const firstLine = anchors.lines[0];
      const shapes = primitives.filter((p) => p.type === 'shape');
      const beside = (x) => x < firstLine.start || x > last.end;
      const hasEnding =
        shapes.some((s) => beside(s.center.x)) ||
        drawn.some((pt) => beside(pt.x) && pt.y < last.baseline);
      assert.equal(hasEnding, true, `${signature.id} ${label} ending mark beside name`);
    }
  }
});

test('page coordinator stretches crowded ambient cadences evenly and rotates signatures without immediate repeats', () => {
  const coordinator = engine.createStageCoordinator();
  const leaves = [];
  for (let i = 0; i < 12; i++) {
    leaves.push(coordinator.joinAmbient(8));
  }
  assert.equal(coordinator.ambientLoad, 96);
  const stretch = coordinator.ambientStretch(1, false);
  assert.equal(stretch, 96 / 16);
  assert.equal(coordinator.ambientStretch(0.25, false), (96 / 16) * 2);
  for (const leave of leaves) leave();
  assert.equal(coordinator.ambientLoad, 0);

  const bag = { played: [] };
  const rng = engine.createRandom(42);
  const enabled = ['quill/stormwrit', 'quill/true-north'];
  let prev = '';
  for (let i = 0; i < 10; i++) {
    const picked = engine.drawSignature(bag, enabled, rng);
    assert.notEqual(picked, prev);
    prev = picked;
  }
});
