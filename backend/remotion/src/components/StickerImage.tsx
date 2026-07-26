import React from "react";
import {
  Img,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  AbsoluteFill,
  staticFile
} from "remotion";

export const StickerImage: React.FC<{ src: string }> = ({ src }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const popInScaleDuration = 15;
  const popInFadeDuration = 10;

  const scale = interpolate(frame, [0, popInScaleDuration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.34, 1.56, 0.64, 1),
  });
  
  const opacity = interpolate(frame, [0, popInFadeDuration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const shakeFrequency = 0.5;
  const shakeAmplitudeX = 5;
  const shakeAmplitudeY = 10;
  const shakeRotation = 1.5;

  const t = frame / 30; // seconds
  const dx = Math.sin(t * Math.PI * 2 * shakeFrequency) * shakeAmplitudeX;
  const dy = Math.cos(t * Math.PI * 2 * shakeFrequency * 1.3) * shakeAmplitudeY;
  const r = Math.sin(t * Math.PI * 2 * shakeFrequency * 0.7) * shakeRotation;

  const imgW = width * 0.96;
  const imgH = height * 0.5;

  let finalSrc = src;
  if (src) {
    if (src.startsWith("http") || src.startsWith("data") || src.startsWith("file://")) {
      finalSrc = src;
    } else {
      finalSrc = staticFile(src);
    }
  }

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          transform: `translate(${dx}px, ${dy}px) rotate(${r}deg)`,
        }}
      >
        <Img
          src={finalSrc}
          style={{
            width: imgW,
            height: imgH,
            objectFit: "contain",
            opacity,
            scale,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
