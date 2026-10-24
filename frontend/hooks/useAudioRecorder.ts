"use client";

import { useEffect, useRef, useState } from "react";

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const startRecording = async () => {
    setError(null);
    setRecordingSeconds(0);
    chunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.start(250);
      setIsRecording(true);

      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Microphone permission denied or audio device unavailable."
      );
    }
  };

  const stopRecording = (): Promise<File | null> => {
    return new Promise((resolve) => {
      const mediaRecorder = mediaRecorderRef.current;
      if (!mediaRecorder || mediaRecorder.state === "inactive") {
        setIsRecording(false);
        resolve(null);
        return;
      }

      mediaRecorder.onstop = async () => {
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }

        const rawBlob = new Blob(chunksRef.current, { type: mediaRecorder.mimeType });
        mediaRecorder.stream.getTracks().forEach((track) => track.stop());
        setIsRecording(false);

        try {
          // Convert browser blob to standard WAV
          const wavFile = await convertBlobToWav(rawBlob);
          resolve(wavFile);
        } catch {
          // Fallback to direct blob file
          const file = new File([rawBlob], `voice-recording-${Date.now()}.wav`, {
            type: "audio/wav",
          });
          resolve(file);
        }
      };

      mediaRecorder.stop();
    });
  };

  const cancelRecording = () => {
    const mediaRecorder = mediaRecorderRef.current;
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stream.getTracks().forEach((track) => track.stop());
      mediaRecorder.stop();
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsRecording(false);
    setRecordingSeconds(0);
    chunksRef.current = [];
  };

  return {
    isRecording,
    recordingSeconds,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
  };
}

async function convertBlobToWav(blob: Blob): Promise<File> {
  const arrayBuffer = await blob.arrayBuffer();
  const audioCtx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
  const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

  const numChannels = 1;
  const sampleRate = audioBuffer.sampleRate;
  const channelData = audioBuffer.getChannelData(0); // mono
  const numSamples = channelData.length;

  const wavBuffer = new ArrayBuffer(44 + numSamples * 2);
  const view = new DataView(wavBuffer);

  // RIFF identifier
  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + numSamples * 2, true);
  writeString(view, 8, "WAVE");

  // fmt chunk
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * numChannels * 2, true); // Byte rate
  view.setUint16(32, numChannels * 2, true); // Block align
  view.setUint16(34, 16, true); // 16 bits per sample

  // data chunk
  writeString(view, 36, "data");
  view.setUint32(40, numSamples * 2, true);

  // PCM samples
  let offset = 44;
  for (let i = 0; i < numSamples; i++) {
    const s = Math.max(-1, Math.min(1, channelData[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    offset += 2;
  }

  const wavBlob = new Blob([view], { type: "audio/wav" });
  return new File([wavBlob], `voice-recording-${Date.now()}.wav`, { type: "audio/wav" });
}

function writeString(view: DataView, offset: number, string: string) {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}
