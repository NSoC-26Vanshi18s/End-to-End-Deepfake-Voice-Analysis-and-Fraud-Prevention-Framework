"use client";

import React from "react";

interface NavbarProps {
  statusText?: string;
  isBackendOnline?: boolean;
  historyCount?: number;
  onOpenHistory?: () => void;
}

export default function Navbar({
  statusText,
  isBackendOnline = true,
  historyCount = 0,
  onOpenHistory,
}: NavbarProps) {
  const displayStatus =
    statusText || (isBackendOnline ? "Forensic Engine Active" : "Engine Offline / Connecting");

  return (
    <header className="topbar">
      <a className="brand" href="/" aria-label="VoxShield home">
        <span className="brand-mark" aria-hidden="true">V</span>
        <span>
          VoxShield<span className="brand-dot">.</span>
        </span>
      </a>
      <div className="topbar-actions">
        <button
          type="button"
          className="history-trigger-btn"
          onClick={onOpenHistory}
          aria-label="Open audit scan history"
        >
          <span>Audit History</span>
          {historyCount > 0 && <span className="history-count-badge">{historyCount}</span>}
        </button>
        <span
          className="topbar-note"
          title={isBackendOnline ? "Backend API reachable" : "Unable to connect to backend API"}
          aria-live="polite"
        >
          <span
            className={`status-dot ${isBackendOnline ? "status-dot-online" : "status-dot-offline"}`}
            style={{
              backgroundColor: isBackendOnline ? "#83dfb4" : "#f87171",
              boxShadow: isBackendOnline ? "0 0 12px #83dfb455" : "0 0 12px #f8717155",
            }}
          />{" "}
          {displayStatus}
        </span>
      </div>
    </header>
  );
}
