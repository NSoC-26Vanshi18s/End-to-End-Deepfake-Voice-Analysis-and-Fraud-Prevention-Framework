"use client";

import React, { useEffect, useRef } from "react";

interface WaveformVisualizerProps {
  isPlaying: boolean;
  progress: number; // 0.0 to 1.0
}

export default function WaveformVisualizer({ isPlaying, progress }: WaveformVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const barCount = 42;
    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const width = canvas.width;
      const height = canvas.height;
      const barWidth = width / barCount - 2;

      for (let i = 0; i < barCount; i++) {
        const x = i * (barWidth + 2);
        // Procedural pseudo-waveform envelope with sinusoidal modulation when playing
        const baseHeight = Math.sin((i / barCount) * Math.PI) * (height * 0.75) + 6;
        const dynamicFactor = isPlaying
          ? Math.sin(phase + i * 0.35) * 0.35 + 0.65
          : 0.5;
        const currentBarHeight = Math.max(4, baseHeight * dynamicFactor);
        const y = (height - currentBarHeight) / 2;

        const isPlayed = i / barCount <= progress;
        ctx.fillStyle = isPlayed ? "#8ee2b8" : "#2a3945";
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, currentBarHeight, 2);
        ctx.fill();
      }

      if (isPlaying) {
        phase += 0.15;
      }
      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [isPlaying, progress]);

  return (
    <div className="waveform-container" aria-label="Audio waveform visualizer">
      <canvas ref={canvasRef} width={360} height={46} className="waveform-canvas" />
    </div>
  );
}
