"use client";

import { ChangeEvent, DragEvent, FormEvent, useRef, useState } from "react";
import Navbar from "../components/Navbar";
import ScanHistoryDrawer from "../components/ScanHistoryDrawer";
import ExportReportModal from "../components/ExportReportModal";
import { useScanHistory, ScanHistoryItem } from "../hooks/useScanHistory";

type AnalysisResult = {
  filename?: string;
  status?: string;
  fake_probability?: number;
  [key: string]: unknown;
};

const MAX_FILE_BYTES = 25 * 1024 * 1024;
const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function Home() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);

  const { history, saveItem, removeItem, clearHistory } = useScanHistory();

  function selectFile(candidate?: File) {
    setError("");
    setResult(null);
    if (!candidate) return;
    if (![".wav", ".wave"].includes(candidate.name.toLowerCase().slice(candidate.name.lastIndexOf(".")))) {
      setFile(null);
      setError("Please choose a WAV audio file (.wav or .wave).");
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

  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || loading) return;
    setLoading(true);
    setError("");
    setResult(null);

    const body = new FormData();
    body.append("file", file);

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
        filename: res.filename || file.name,
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

  const probability = typeof result?.fake_probability === "number" ? result.fake_probability : null;

  return (
    <main className="analysis-shell">
      <Navbar
        historyCount={history.length}
        onOpenHistory={() => setIsHistoryOpen(true)}
      />

      <section className="hero">
        <p className="eyebrow">DEEPFAKE VOICE DETECTION</p>
        <h1>Is this voice <span>really real?</span></h1>
        <p className="hero-copy">Upload an audio recording to check it for signs of synthetic or manipulated speech.</p>
      </section>

      <section className="workspace" aria-label="Audio analysis">
        <form className="upload-card" onSubmit={analyze}>
          <div className="card-heading">
            <div>
              <p className="step-label">01 <span>/ UPLOAD</span></p>
              <h2>Choose an audio file</h2>
            </div>
            <span className="file-type">WAV · MAX 25 MB</span>
          </div>

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
              accept=".wav,.wave,audio/wav,audio/wave"
              onChange={onInputChange}
              aria-label="Choose WAV audio file"
            />
            {file ? (
              <>
                <div className="audio-icon selected-icon" aria-hidden="true">♫</div>
                <div className="selected-file">
                  <strong>{file.name}</strong>
                  <span>{formatBytes(file.size)} · Ready to analyze</span>
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

          {error && <p className="error-message" role="alert"><span aria-hidden="true">!</span>{error}</p>}

          <div className="upload-footer">
            <p><span className="lock-icon" aria-hidden="true">◇</span> Audio is sent to your configured analysis server.</p>
            <button className="analyze-button" type="submit" disabled={!file || loading}>
              {loading ? <><span className="spinner" /> Analyzing audio…</> : <>Analyze audio <span aria-hidden="true">→</span></>}
            </button>
          </div>
        </form>

        <aside className="result-card" aria-live="polite">
          <div className="card-heading">
            <div>
              <p className="step-label">02 <span>/ RESULTS</span></p>
              <h2>Analysis report</h2>
            </div>
            {result && <span className="result-status">{result.status || "Complete"}</span>}
          </div>
          {!result && !loading ? (
            <div className="empty-result">
              <div className="report-graphic" aria-hidden="true"><span>〰</span><span>〰</span><span>〰</span></div>
              <strong>Your report will appear here</strong>
              <p>Choose a WAV file and run the analysis to see the response from the detection API.</p>
            </div>
          ) : loading ? (
            <div className="empty-result">
              <div className="loading-graphic"><span /><span /><span /><span /><span /></div>
              <strong>Listening for signals…</strong>
              <p>Your audio is being sent to the backend for analysis.</p>
            </div>
          ) : result ? (
            <div className="report-content">
              <div className="report-file">
                <span className="mini-audio">♫</span>
                <div>
                  <strong>{result.filename || file?.name || "Audio file"}</strong>
                  <span>Server response received</span>
                </div>
                <button
                  type="button"
                  className="export-trigger-btn"
                  onClick={() => setIsExportOpen(true)}
                  aria-label="Export forensic report"
                >
                  Export Case ↓
                </button>
              </div>

              {probability !== null ? (
                <div className="probability-block">
                  <div className="probability-top"><span>Fake voice probability</span><strong>{(probability * 100).toFixed(1)}%</strong></div>
                  <div className="probability-track"><span style={{ width: `${Math.max(0, Math.min(100, probability * 100))}%` }} /></div>
                </div>
              ) : (
                <div className="response-note"><strong>Analysis status</strong><span>{result.status || "The API returned a result."}</span></div>
              )}

              <details className="raw-response"><summary>View full API response</summary><pre>{JSON.stringify(result, null, 2)}</pre></details>
            </div>
          ) : null}
          <div className="result-footnote"><span className="info-mark">i</span> Results depend on the analysis model and should not be treated as definitive proof.</div>
        </aside>
      </section>

      <footer className="page-footer"><span>VOXSHIELD · AUDIO FORENSICS</span><span>Supported format: WAV / WAVE</span></footer>

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
