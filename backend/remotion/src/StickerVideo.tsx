import React from "react";
import { AbsoluteFill, Audio, staticFile, Series } from "remotion";
import { Background } from "./components/Background";
import { GlowCaptions } from "./components/GlowCaptions";
import { StickerImage } from "./components/StickerImage";
import { MultiSceneProps } from "./Root";

export const StickerVideo: React.FC<MultiSceneProps> = ({ scenes }) => {
  if (!scenes || scenes.length === 0) {
    return <AbsoluteFill style={{ backgroundColor: "black" }} />;
  }

  return (
    <AbsoluteFill>
      <Series>
        {scenes.map((scene, index) => {
          let finalAudioSrc = scene.audioSrc;
          if (scene.audioSrc) {
            if (scene.audioSrc.startsWith("http") || scene.audioSrc.startsWith("data") || scene.audioSrc.startsWith("file://")) {
              finalAudioSrc = scene.audioSrc;
            } else {
              finalAudioSrc = staticFile(scene.audioSrc);
            }
          }

          return (
            <Series.Sequence key={index} durationInFrames={scene.durationInFrames}>
              <Background colors={scene.backgroundColors} />
              {scene.imageSrc && <StickerImage src={scene.imageSrc} />}
              {scene.wordTimings && <GlowCaptions words={scene.wordTimings} glowColor={scene.captionGlowColor} />}
              {scene.audioSrc && <Audio src={finalAudioSrc} />}
            </Series.Sequence>
          );
        })}
      </Series>
    </AbsoluteFill>
  );
};
