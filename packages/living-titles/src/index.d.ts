export type CutName = 'Soft' | 'Edge' | 'Ink' | 'Wide';
export interface MotionAxes { weight?: boolean; slant?: boolean; penAngle?: boolean }
export interface SceneOptions {
  title: string; cut?: CutName; strength?: number; capitalSpacing?: boolean; axes?: MotionAxes;
  signal?: AbortSignal; onProgress?: (fraction: number) => void;
}
export interface TitleFrame {readonly body: string; readonly defs: string; readonly bounds: readonly number[]; readonly time: number; readonly duration: number}
export interface TitleScene {
  readonly title: string; readonly cut: CutName; readonly profile: string; readonly strength: number;
  readonly capitalSpacing: boolean; readonly axes: Readonly<MotionAxes>; readonly viewBox: readonly number[];
  readonly advance: number; readonly frames: readonly TitleFrame[];
}
export interface MotionSource {sample(elapsedSeconds: number): number}
export interface BpmOptions {bpm?: number; beats?: number}
export interface SVGOptions {color?: string; idPrefix?: string; longestEdge?: 1080 | 1920}
export interface PlayerState {readonly playing: boolean; readonly disposed: boolean; readonly elapsed: number; readonly energy: number; readonly pose: number; readonly reducedMotion: boolean}
export interface TitlePlayer {
  play(): void; pause(): void; seek(seconds: number): void; setScene(scene: TitleScene): void;
  setSource(source: MotionSource): void; setColor(color: string): void; render(): void;
  getState(): PlayerState; dispose(): void;
}
export declare const cuts: readonly Readonly<{name: CutName; note: string}>[];
export declare function createTitleScene(options: SceneOptions): Promise<TitleScene>;
export declare function poseIndex(scene: TitleScene, energy: number): number;
export declare function renderTitleSVG(scene: TitleScene, energy?: number, options?: SVGOptions): string;
export declare function createBpmSource(options?: BpmOptions): MotionSource & {readonly duration: number};
export declare function smoothEnergy(previous: number, input: number, deltaSeconds: number): number;
export declare function exportAnimatedSVG(scene: TitleScene, options?: BpmOptions & Pick<SVGOptions, 'color' | 'longestEdge'>): string;
export declare function createTitlePlayer(element: HTMLElement, scene: TitleScene, options?: {source?: MotionSource; color?: string; autoplay?: boolean}): TitlePlayer;
