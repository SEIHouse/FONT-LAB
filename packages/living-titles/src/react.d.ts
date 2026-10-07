import type { CSSProperties, ReactElement } from 'react';
import type { SceneOptions, MotionSource } from './index.js';
export interface LivingTitleProps extends Omit<SceneOptions, 'signal' | 'onProgress'> {
  source?: MotionSource; color?: string; playing?: boolean; className?: string;
  style?: CSSProperties; onError?: (error: Error) => void;
}
export declare function LivingTitle(props: LivingTitleProps): ReactElement;
