import React from "react";
import { Composition } from "remotion";
import { StickerVideo } from "./StickerVideo";

export interface SingleSceneProps {
  audioSrc: string;
  imageSrc: string;
  wordTimings: Array<{
    word: string;
    startMs: number;
    endMs: number;
  }>;
  durationInFrames: number;
  captionGlowColor?: string;
  backgroundColors?: {
    color: string;
    dark: string;
  };
}

export interface MultiSceneProps {
  scenes: Array<SingleSceneProps>;
}

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="StickerVideo"
      component={StickerVideo as any}
      calculateMetadata={({ props }: any) => {
        const p = props as MultiSceneProps;
        let totalDuration = 0;
        if (p.scenes) {
          totalDuration = p.scenes.reduce(
            (acc: number, scene: SingleSceneProps) => acc + (scene.durationInFrames || 0),
            0
          );
        }
        return {
          durationInFrames: totalDuration || 300,
          props,
        };
      }}
      defaultProps={{
        scenes: [],
      }}
      fps={30}
      width={720}
      height={1280}
    />
  );
};
