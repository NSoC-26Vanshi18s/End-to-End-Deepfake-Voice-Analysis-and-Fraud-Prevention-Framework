"use client";

import React from "react";
import { useAudioVisualizer } from "../hooks/useAudioVisualizer";
import WaveformVisualizer from "./WaveformVisualizer";

interface AudioPlayerProps {
  file: File;
}

function formatTime(seconds: number): string {
  if (isNaN(seconds) || seconds < 0) return "0:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
}

export default function AudioPlayer({ file }: AudioPlayerProps) {
  const { isPlaying, currentTime, duration, togglePlay, seek } = useAudioVisualizer(file);
  const progress = duration > 0 ? currentTime / duration : 0;

  return (
    <div className="audio-preview-box" role="region" aria-label="Audio sample player">
      <div className="audio-preview-top">
        <button
          type="button"
          className="play-toggle-btn"
          onClick={togglePlay}
          aria-label={isPlaying ? "Pause audio" : "Play audio"}
        >
          {isPlaying ? "❚❚" : "▶"}
        </button>

        <div className="preview-meta">
          <span className="preview-label">Audio Playback Preview</span>
          <span className="preview-timer">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>
      </div>

      <WaveformVisualizer isPlaying={isPlaying} progress={progress} />

      <input
        type="range"
        min={0}
        max={duration || 100}
        step={0.01}
        value={currentTime}
        onChange={(e) => seek(parseFloat(e.target.value))}
        className="audio-scrubber"
        aria-label="Audio playback scrubber"
      />
    </div>
  );
}
