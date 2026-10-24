"use client";

import React from "react";
import { useAudioRecorder } from "../hooks/useAudioRecorder";

interface LiveVoiceRecorderProps {
  onRecorded: (file: File) => void;
  disabled?: boolean;
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

export default function LiveVoiceRecorder({ onRecorded, disabled = false }: LiveVoiceRecorderProps) {
  const {
    isRecording,
    recordingSeconds,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useAudioRecorder();

  const handleStop = async () => {
    const file = await stopRecording();
    if (file) {
      onRecorded(file);
    }
  };

  return (
    <div className="recorder-container" role="region" aria-label="Microphone voice recorder">
      {error && (
        <div className="recorder-error" role="alert">
          <span>⚠️</span> {error}
        </div>
      )}

      {!isRecording ? (
        <div className="recorder-idle-state">
          <div className="recorder-icon" aria-hidden="true">
            🎙️
          </div>
          <h4>Capture Live Voice Sample</h4>
          <p>Record speech directly from your microphone to test real-time voice anti-spoofing.</p>
          <button
            type="button"
            className="start-record-btn"
            onClick={startRecording}
            disabled={disabled}
          >
            Start Recording
          </button>
        </div>
      ) : (
        <div className="recorder-active-state">
          <div className="recording-indicator">
            <span className="recording-pulse" />
            <span className="recording-text">RECORDING AUDIO</span>
          </div>

          <div className="recording-timer">
            {formatDuration(recordingSeconds)}
          </div>

          <p className="recorder-hint">Speak clearly for at least 3 seconds...</p>

          <div className="recorder-actions">
            <button
              type="button"
              className="stop-record-btn"
              onClick={handleStop}
              disabled={recordingSeconds < 1}
            >
              Finish & Analyze →
            </button>
            <button
              type="button"
              className="cancel-record-btn"
              onClick={cancelRecording}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
