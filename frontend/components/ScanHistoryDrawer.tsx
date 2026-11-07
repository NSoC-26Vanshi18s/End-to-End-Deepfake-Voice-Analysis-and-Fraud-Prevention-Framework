"use client";

import React, { useMemo, useState } from "react";
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
  const [searchQuery, setSearchQuery] = useState("");
  const [filterRisk, setFilterRisk] = useState<"all" | "human" | "fake">("all");

  const filteredHistory = useMemo(() => {
    return history.filter((item) => {
      const matchesSearch = item.filename.toLowerCase().includes(searchQuery.toLowerCase());
      if (!matchesSearch) return false;

      const isFake = item.fake_probability >= 0.5;
      if (filterRisk === "fake") return isFake;
      if (filterRisk === "human") return !isFake;
      return true;
    });
  }, [history, searchQuery, filterRisk]);

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

        {history.length > 0 && (
          <div style={{ padding: "12px 18px", borderBottom: "1px solid #25313d", display: "flex", flexDirection: "column", gap: "8px" }}>
            <input
              type="text"
              placeholder="Filter by filename…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search scan history by filename"
              style={{
                width: "100%",
                padding: "7px 11px",
                background: "#0c141d",
                border: "1px solid #2a3a49",
                borderRadius: "7px",
                color: "#e6edf4",
                fontSize: "12px",
              }}
            />
            <div style={{ display: "flex", gap: "6px" }}>
              {(
                [
                  { id: "all", label: "All" },
                  { id: "human", label: "Human" },
                  { id: "fake", label: "Synthetic / Fake" },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setFilterRisk(tab.id)}
                  style={{
                    padding: "4px 10px",
                    fontSize: "11px",
                    borderRadius: "6px",
                    border: "1px solid",
                    borderColor: filterRisk === tab.id ? "#8ee2b8" : "#2a3a49",
                    background: filterRisk === tab.id ? "#132b24" : "#111a24",
                    color: filterRisk === tab.id ? "#a5edd0" : "#9aa7b6",
                    cursor: "pointer",
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="drawer-content">
          {history.length === 0 ? (
            <div className="drawer-empty">
              <span>📋</span>
              <p>No audio files have been analyzed in this session yet.</p>
            </div>
          ) : filteredHistory.length === 0 ? (
            <div className="drawer-empty">
              <span>🔍</span>
              <p>No scans match your search or filter criteria.</p>
            </div>
          ) : (
            <div className="drawer-list">
              {filteredHistory.map((item) => {
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
