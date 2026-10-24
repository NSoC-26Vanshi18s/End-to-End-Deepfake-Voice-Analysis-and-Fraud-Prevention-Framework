"use client";

import React from "react";

interface NavbarProps {
  statusText?: string;
  historyCount?: number;
  onOpenHistory?: () => void;
}

export default function Navbar({
  statusText = "Audio integrity analysis",
  historyCount = 0,
  onOpenHistory,
}: NavbarProps) {
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
        <span className="topbar-note">
          <span className="status-dot" /> {statusText}
        </span>
      </div>
    </header>
  );
}
