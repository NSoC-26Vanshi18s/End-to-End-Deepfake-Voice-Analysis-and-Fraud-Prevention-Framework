"use client";

import React, { useState } from "react";

interface ExportReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  reportData: Record<string, unknown>;
}

export default function ExportReportModal({ isOpen, onClose, reportData }: ExportReportModalProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const jsonString = JSON.stringify(reportData, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleDownload = () => {
    const filename = `voxshield-forensic-report-${Date.now()}.json`;
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Export forensic report">
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>Export Forensic Case Report</h3>
            <span className="modal-subtitle">Cryptographic evidence package for incident response</span>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close export dialog">
            ✕
          </button>
        </div>

        <div className="modal-body">
          <p className="modal-description">
            This export contains raw acoustic measurements, deepfake model probabilities, threat categorization, and SHA-256 integrity digests.
          </p>
          <pre className="export-preview">{jsonString}</pre>
        </div>

        <div className="modal-footer">
          <button type="button" className="copy-btn" onClick={handleCopy}>
            {copied ? "✓ Copied to Clipboard!" : "Copy JSON"}
          </button>
          <button type="button" className="download-btn" onClick={handleDownload}>
            Download .JSON File ↓
          </button>
        </div>
      </div>
    </div>
  );
}
