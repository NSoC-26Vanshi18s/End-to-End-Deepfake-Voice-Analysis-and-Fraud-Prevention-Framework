"use client";

import { ChangeEvent, DragEvent, FormEvent, useEffect, useRef, useState } from "react";
import AnalysisReportCard from "../components/AnalysisReportCard";
import AudioPlayer from "../components/AudioPlayer";
import Navbar from "../components/Navbar";
import ScanHistoryDrawer from "../components/ScanHistoryDrawer";
import ExportReportModal from "../components/ExportReportModal";
import { useScanHistory, ScanHistoryItem } from "../hooks/useScanHistory";
import LiveVoiceRecorder from "../components/LiveVoiceRecorder";
import SampleAudioPlayground from "../components/SampleAudioPlayground";

type AnalysisResult = {
  filename?: string;
  status?: string;
  fake_probability?: number;
  confidence_score?: number;
  risk_level?: string;
  indicators?: string[];
  breakdown?: {
    spectral_consistency?: number;
    pitch_naturalness?: number;
    vocoder_artifact_score?: number;
  };
  fraud_prevention?: {
    sha256_hash?: string;
    impersonation_threat_score?: number;
    threat_category?: string;
    requires_human_escalation?: boolean;
    advisory_actions?: {
      action_type: string;
      description: string;
      severity: string;
    }[];
  };
  sha256_hash?: string;
  [key: string]: unknown;
};

type InputMode = "upload" | "record" | "samples";

const MAX_FILE_BYTES = 25 * 1024 * 1024;
const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [activeTab, setActiveTab] = useState<InputMode>("upload");
  const inputRef = useRef<HTMLInputElement>(null);

  // History & Export States
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(true);
  const { history, saveItem, removeItem, clearHistory } = useScanHistory();

  useEffect(() => {
    let isMounted = true;
    async function checkHealth() {
      try {
        const res = await fetch(`${API_URL}/api/v1/health`, { method: "GET" });
        if (isMounted) {
          setIsBackendOnline(res.ok);
        }
      } catch {
        if (isMounted) {
          setIsBackendOnline(false);
        }
      }
    }
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  function selectFile(candidate?: File) {
    setError("");
    setResult(null);
    if (!candidate) return;
    const supportedExtensions = [".wav", ".wave", ".mp3", ".ogg", ".flac", ".m4a", ".aac"];
    const ext = candidate.name.toLowerCase().slice(candidate.name.lastIndexOf("."));
    if (!supportedExtensions.includes(ext)) {
      setFile(null);
      setError("Unsupported audio format. Supported formats: WAV, MP3, OGG, FLAC, M4A, AAC.");
      return;
    }
    if (candidate.size > MAX_FILE_BYTES) {
      setFile(null);
      setError("This file is larger than 25 MB. Choose a smaller audio file.");
      return;
    }
    setFile(candidate);
  }

  function onInputChange(event: ChangeEvent<HTMLInputElement>) {
    selectFile(event.target.files?.[0]);
    event.target.value = "";
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    selectFile(event.dataTransfer.files?.[0]);
  }

  async function triggerAnalysis(fileToAnalyze: File) {
    setLoading(true);
    setError("");
    setResult(null);

    const body = new FormData();
    body.append("file", fileToAnalyze);

    try {
      const response = await fetch(`${API_URL}/api/v1/analyze`, {
        method: "POST",
        body,
      });

      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        const detail = payload && typeof payload.detail === "string" ? payload.detail : "";
        throw new Error(detail || `Analysis failed (HTTP ${response.status}).`);
      }

      if (!payload || typeof payload !== "object") {
        throw new Error("The server returned an unexpected response.");
      }

      const res = payload as AnalysisResult;
      setResult(res);

      // Save to audit history
      saveItem({
        filename: res.filename || fileToAnalyze.name,
        fake_probability: typeof res.fake_probability === "number" ? res.fake_probability : 0.0,
        risk_level: (typeof res.risk_level === "string" ? res.risk_level : "ANALYZED"),
        status: (typeof res.status === "string" ? res.status : "completed"),
        details: res,
      });
    } catch (caught) {
      setError(
        caught instanceof TypeError
          ? `Could not connect to the analysis API at ${API_URL}. Make sure the backend is running and CORS is configured.`
          : caught instanceof Error
            ? caught.message
            : "Something went wrong while analyzing the audio.",
      );
    } finally {
      setLoading(false);
    }
  }

  const handleSelectHistoryScan = (item: ScanHistoryItem) => {
    if (item.details) {
      setResult(item.details as AnalysisResult);
    } else {
      setResult({
        filename: item.filename,
        fake_probability: item.fake_probability,
        status: item.status,
      });
    }
  };

  async function handleUploadSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || loading) return;
    await triggerAnalysis(file);
  }

  const handleSampleSelected = (selectedFile: File) => {
    setFile(selectedFile);
    triggerAnalysis(selectedFile);
  };

  const handleLiveRecorded = (recordedFile: File) => {
    setFile(recordedFile);
    triggerAnalysis(recordedFile);
  };

  const probability = typeof result?.fake_probability === "number" ? result.fake_probability : null;

  return (
    <main className="analysis-shell">
      <Navbar
        historyCount={history.length}
        isBackendOnline={isBackendOnline}
        onOpenHistory={() => setIsHistoryOpen(true)}
      />

      <section className="hero">
        <p className="eyebrow">DEEPFAKE VOICE DETECTION</p>
        <h1>Is this voice <span>really real?</span></h1>
        <p className="hero-copy">Upload, record, or test an audio sample to check it for signs of synthetic voice fraud.</p>
      </section>

      <section className="workspace" aria-label="Audio analysis">
        <div className="upload-card">
          <div className="card-heading">
            <div>
              <p className="step-label">01 <span>/ SOURCE SELECTION</span></p>
              <h2>Select audio source</h2>
            </div>
            <div className="input-mode-tabs" role="tablist">
              <button
                type="button"
                className={`tab-btn ${activeTab === "upload" ? "tab-active" : ""}`}
                onClick={() => setActiveTab("upload")}
              >
                Upload
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === "record" ? "tab-active" : ""}`}
                onClick={() => setActiveTab("record")}
              >
                Record
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === "samples" ? "tab-active" : ""}`}
                onClick={() => setActiveTab("samples")}
              >
                Samples
              </button>
            </div>
          </div>

          {activeTab === "upload" && (
            <form onSubmit={handleUploadSubmit}>
              <div
                className={`dropzone ${dragging ? "dropzone-active" : ""} ${file ? "dropzone-selected" : ""}`}
                onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
              >
                <input
                  ref={inputRef}
                  className="visually-hidden"
                  type="file"
                  accept=".wav,.wave,.mp3,.ogg,.flac,.m4a,.aac,audio/*"
                  onChange={onInputChange}
                  aria-label="Choose audio file to analyze (WAV, MP3, OGG, FLAC, M4A, AAC)"
                />
                {file ? (
                  <>
                    <div className="audio-icon selected-icon" aria-hidden="true">♫</div>
                    <div className="selected-file">
                      <strong>{file.name}</strong>
                      <span>{(file.size / (1024 * 1024)).toFixed(2)} MB · Ready to analyze</span>
                    </div>
                    <button className="change-file" type="button" onClick={() => inputRef.current?.click()}>Change</button>
                  </>
                ) : (
                  <>
                    <div className="audio-icon" aria-hidden="true">↑</div>
                    <strong className="drop-title">Drop your audio file here</strong>
                    <span className="drop-subtitle">or browse files from your device</span>
                    <button className="browse-button" type="button" onClick={() => inputRef.current?.click()}>Browse files</button>
                  </>
                )}
              </div>

              {file && (
                <div style={{ marginTop: "12px", width: "100%" }}>
                  <AudioPlayer file={file} />
                </div>
              )}

              {error && <p className="error-message" role="alert"><span aria-hidden="true">!</span>{error}</p>}

              <div className="upload-footer">
                <p><span className="lock-icon" aria-hidden="true">◇</span> Audio is sent to your configured analysis server.</p>
                <button className="analyze-button" type="submit" disabled={!file || loading}>
                  {loading ? <><span className="spinner" /> Analyzing audio…</> : <>Analyze audio <span aria-hidden="true">→</span></>}
                </button>
              </div>
            </form>
          )}

          {activeTab === "record" && (
            <LiveVoiceRecorder
              onRecorded={handleLiveRecorded}
              disabled={loading}
            />
          )}

          {activeTab === "samples" && (
            <SampleAudioPlayground
              onSelectSample={handleSampleSelected}
              disabled={loading}
            />
          )}
        </div>

        <AnalysisReportCard
          result={result}
          loading={loading}
          file={file}
          onExport={() => setIsExportOpen(true)}
        />
      </section>

      <footer className="page-footer"><span>VOXSHIELD · AUDIO FORENSICS</span><span>Supported formats: WAV, MP3, OGG, FLAC, M4A, AAC (up to 25 MB)</span></footer>

      <ScanHistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        history={history}
        onSelectScan={handleSelectHistoryScan}
        onClearHistory={clearHistory}
        onRemoveItem={removeItem}
      />

      {result && (
        <ExportReportModal
          isOpen={isExportOpen}
          onClose={() => setIsExportOpen(false)}
          reportData={result as Record<string, unknown>}
        />
      )}
    </main>
  );
}