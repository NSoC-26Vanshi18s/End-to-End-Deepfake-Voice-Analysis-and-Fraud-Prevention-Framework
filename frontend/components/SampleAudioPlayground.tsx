"use client";

import React from "react";

interface SampleVoice {
  id: string;
  title: string;
  description: string;
  category: "human" | "synthetic" | "vocoder";
  duration: number;
  freq: number;
  jitter: boolean;
}

const DEMO_SAMPLES: SampleVoice[] = [
  {
    id: "sample-human",
    title: "Natural Human Speech",
    description: "Standard voice profile featuring natural biological pitch micro-tremors.",
    category: "human",
    duration: 2.0,
    freq: 180,
    jitter: true,
  },
  {
    id: "sample-clone",
    title: "AI Voice Clone (TTS Engine)",
    description: "Synthetic speech exhibiting unnatural robotic pitch constancy.",
    category: "synthetic",
    duration: 2.0,
    freq: 220,
    jitter: false,
  },
  {
    id: "sample-vocoder",
    title: "Neural Vocoder Artifact",
    description: "Sample with high-frequency phase and spectral cutoff anomalies.",
    category: "vocoder",
    duration: 1.8,
    freq: 310,
    jitter: false,
  },
];

interface SampleAudioPlaygroundProps {
  onSelectSample: (file: File) => void;
  disabled?: boolean;
}

export default function SampleAudioPlayground({
  onSelectSample,
  disabled = false,
}: SampleAudioPlaygroundProps) {
  const loadSample = (sample: SampleVoice) => {
    // Generate an in-browser WAV file modeling the selected profile
    const sampleRate = 16000;
    const numSamples = Math.floor(sample.duration * sampleRate);
    const wavBuffer = new ArrayBuffer(44 + numSamples * 2);
    const view = new DataView(wavBuffer);

    // RIFF header
    writeString(view, 0, "RIFF");
    view.setUint32(4, 36 + numSamples * 2, true);
    writeString(view, 8, "WAVE");
    writeString(view, 12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, 1, true);  // Mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, "data");
    view.setUint32(40, numSamples * 2, true);

    let offset = 44;
    for (let i = 0; i < numSamples; i++) {
      const t = i / sampleRate;
      let val = 0;

      if (sample.category === "human") {
        // Natural modulated pitch
        const f0 = sample.freq + Math.sin(t * 12) * 5 + (Math.random() - 0.5) * 4;
        val = 0.6 * Math.sin(2 * Math.PI * f0 * t) + 0.3 * Math.sin(2 * Math.PI * 2 * f0 * t);
      } else if (sample.category === "synthetic") {
        // Flat, unnaturally constant synthetic frequency
        val = 0.8 * Math.sin(2 * Math.PI * sample.freq * t);
      } else {
        // Harmonic buzz with steep cutoff
        val = 0.5 * Math.sin(2 * Math.PI * sample.freq * t) + 0.4 * Math.sin(2 * Math.PI * 3 * sample.freq * t);
      }

      val = Math.max(-1, Math.min(1, val));
      view.setInt16(offset, val < 0 ? val * 0x8000 : val * 0x7fff, true);
      offset += 2;
    }

    const blob = new Blob([view], { type: "audio/wav" });
    const file = new File([blob], `${sample.id}.wav`, { type: "audio/wav" });
    onSelectSample(file);
  };

  return (
    <div className="playground-container" role="region" aria-label="Demo sample audio playground">
      <div className="playground-header">
        <h4>Test with Pre-Configured Voice Samples</h4>
        <p>No audio files on your device? Click any sample to run an instant forensic analysis.</p>
      </div>

      <div className="sample-cards-grid">
        {DEMO_SAMPLES.map((sample) => (
          <div key={sample.id} className="sample-card">
            <div className="sample-card-top">
              <span className={`sample-badge badge-${sample.category}`}>
                {sample.category === "human" ? "Organic" : "Synthetic"}
              </span>
              <span className="sample-duration">{sample.duration}s WAV</span>
            </div>
            <h5>{sample.title}</h5>
            <p>{sample.description}</p>
            <button
              type="button"
              className="load-sample-btn"
              onClick={() => loadSample(sample)}
              disabled={disabled}
            >
              Analyze This Sample →
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function writeString(view: DataView, offset: number, string: string) {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}
