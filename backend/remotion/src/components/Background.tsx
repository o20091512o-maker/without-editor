import React from "react";
import { AbsoluteFill } from "remotion";

export const Background: React.FC<{ colors?: { color: string; dark: string } }> = ({ colors }) => {
  const c = colors || { color: "#FF0000", dark: "#1A0000" };
  
  return (
    <>
      <AbsoluteFill
        style={{
          background: `linear-gradient(135deg, ${c.color} 0%, ${c.dark} 70%)`,
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at 50% 30%, ${c.color}80 0%, transparent 70%)`,
        }}
      />
    </>
  );
};
