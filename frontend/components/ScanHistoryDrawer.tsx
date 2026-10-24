"use client";

import React from "react";
import { ScanHistoryItem } from "../hooks/useScanHistory";

interface ScanHistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  history: ScanHistoryItem[];
  onSelectScan: (item: ScanHistoryItem) => void;
  onClearHistory: () => void;
  onRemoveItem: (id: string) => void;
}

export default function ScanHistoryDrawer({
  isOpen,
  onClose,
  history,
  onSelectScan,
  onClearHistory,
  onRemoveItem,
}: ScanHistoryDrawerProps) {
  if (!isOpen) return null;

  return (
    <div className="drawer-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Scan history drawer">
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <h3>Audit Scan History</h3>
            <span className="drawer-subtitle">{history.length} scans recorded locally</span>
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="Close scan history">
            ✕
          </button>
        </div>

        <div className="drawer-content">
          {history.length === 0 ? (
            <div className="drawer-empty">
              <span>📋</span>
              <p>No audio files have been analyzed in this session yet.</p>
            </div>
          ) : (
            <div className="drawer-list">
              {history.map((item) => {
                const prob = item.fake_probability;
                const isFake = prob >= 0.5;

                return (
                  <div
                    key={item.id}
                    className="history-item"
                    onClick={() => {
                      onSelectScan(item);
                      onClose();
                    }}
                    role="button"
                    tabIndex={0}
                  >
                    <div className="history-item-top">
                      <strong className="history-filename" title={item.filename}>
                        {item.filename}
                      </strong>
                      <span className={`history-risk-tag ${isFake ? "tag-danger" : "tag-safe"}`}>
                        {(prob * 100).toFixed(1)}% {isFake ? "Fake" : "Human"}
                      </span>
                    </div>

                    <div className="history-item-bottom">
                      <span className="history-time">
                        {new Date(item.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                      <button
                        type="button"
                        className="history-delete-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          onRemoveItem(item.id);
                        }}
                        aria-label={`Delete record for ${item.filename}`}
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {history.length > 0 && (
          <div className="drawer-footer">
            <button type="button" className="clear-history-btn" onClick={onClearHistory}>
              Clear History
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
