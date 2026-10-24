"use client";

import React from "react";

interface ForensicIndicatorListProps {
  indicators?: string[];
  riskLevel?: string;
}

export default function ForensicIndicatorList({
  indicators = [],
  riskLevel = "LOW_RISK",
}: ForensicIndicatorListProps) {
  const isHighRisk = riskLevel === "HIGH_RISK_DEEPFAKE";

  return (
    <div className="indicators-container" role="region" aria-label="Forensic indicators">
      <h4 className="indicators-title">Forensic Signals & Anomaly Indicators</h4>
      {indicators.length > 0 ? (
        <ul className="indicators-list">
          {indicators.map((indicator, index) => (
            <li key={index} className={`indicator-item ${isHighRisk ? "indicator-danger" : "indicator-neutral"}`}>
              <span className="indicator-bullet" aria-hidden="true">
                {isHighRisk ? "▲" : "◆"}
              </span>
              <span>{indicator}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="no-indicators-note">
          ✓ Acoustic harmonic distribution conforms to standard biological speech norms.
        </p>
      )}
    </div>
  );
}
