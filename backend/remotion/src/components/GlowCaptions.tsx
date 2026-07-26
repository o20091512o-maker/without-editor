import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

interface WordTiming {
  word: string;
  startMs: number;
  endMs: number;
}

interface GlowCaptionsProps {
  words: WordTiming[];
  glowColor?: string;
}

export const GlowCaptions: React.FC<GlowCaptionsProps> = ({ words, glowColor = "#00E5FF" }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();

  if (!words || words.length === 0) return null;

  const currentTimeMs = (frame / fps) * 1000;
  const currentWordIndex = words.findIndex(
    (w) => currentTimeMs >= w.startMs && currentTimeMs < w.endMs
  );
  
  if (currentWordIndex === -1) return null;

  // Check if text contains Arabic characters
  const isArabic = words.some((w) => /[\u0600-\u06FF]/.test(w.word));

  const MAX_CHARS = 25;
  let startIdx = currentWordIndex;
  let endIdx = currentWordIndex;
  let totalChars = words[currentWordIndex].word.length;

  while (
    endIdx + 1 < words.length &&
    totalChars + words[endIdx + 1].word.length + 1 <= MAX_CHARS
  ) {
    endIdx++;
    totalChars += words[endIdx].word.length + 1;
  }
  while (
    startIdx > 0 &&
    totalChars + words[startIdx - 1].word.length + 1 <= MAX_CHARS
  ) {
    startIdx--;
    totalChars += words[startIdx].word.length + 1;
  }

  const visibleWords = words.slice(startIdx, endIdx + 1);
  const baseSize = Math.max(
    38,
    Math.min(68, Math.round(76 - totalChars * 1.4))
  );
  const fontSize = Math.round((baseSize * Math.min(width, height)) / 1080);

  const fontFamily = "'Cairo', 'Segoe UI', 'Inter', 'Tahoma', 'Arial', sans-serif";

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: "22%",
      }}
    >
      <div
        dir={isArabic ? "rtl" : "ltr"}
        style={{
          direction: isArabic ? "rtl" : "ltr",
          unicodeBidi: "plaintext",
          textAlign: "center",
          maxWidth: "92%",
          overflow: "hidden",
          lineHeight: 1.35,
        }}
      >
        {visibleWords.map((token, i) => {
          const isCurrent = currentWordIndex === startIdx + i;
          const cleanWord = token.word.trim();
          const isWordArabic = /[\u0600-\u06FF]/.test(cleanWord);
          
          return (
            <React.Fragment key={`${token.startMs}-${i}`}>
              <span
                dir="auto"
                style={{
                  fontSize,
                  fontWeight: 900,
                  fontFamily,
                  color: isCurrent ? "#FFFFFF" : "#777777",
                  textShadow: isCurrent
                    ? `0 0 12px ${glowColor}, 0 0 25px ${glowColor}, 0 0 45px rgba(255,255,255,0.8)`
                    : "0 2px 8px rgba(0,0,0,0.9)",
                  display: "inline-block",
                  letterSpacing: isWordArabic ? 0 : 0.5,
                  padding: "0 4px",
                  unicodeBidi: "isolate",
                  transition: "all 0.1s ease",
                }}
              >
                {cleanWord}
              </span>
              {i < visibleWords.length - 1 && (
                <span style={{ fontSize, fontFamily }}>{" "}</span>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
