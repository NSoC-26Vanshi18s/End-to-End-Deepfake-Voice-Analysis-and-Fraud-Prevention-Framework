"use client";

import React from "react";

interface AdvisoryAction {
  action_type: string;
  description: string;
  severity: string;
}

interface FraudPreventionData {
  sha256_hash?: string;
  impersonation_threat_score?: number;
  threat_category?: string;
  requires_human_escalation?: boolean;
  advisory_actions?: AdvisoryAction[];
}

interface FraudAdvisoryPanelProps {
  fraudData?: FraudPreventionData;
  fakeProbability?: number;
}

export default function FraudAdvisoryPanel({
  fraudData,
  fakeProbability = 0.0,
}: FraudAdvisoryPanelProps) {
  const isHighRisk = (fraudData?.impersonation_threat_score ?? fakeProbability * 100) >= 65;
  const isSuspicious = (fraudData?.impersonation_threat_score ?? fakeProbability * 100) >= 35;
  const threatCategory = fraudData?.threat_category || (isHighRisk ? "CRITICAL_VOICE_CLONING_FRAUD" : isSuspicious ? "SUSPECTED_VOICE_SYNTHESIS" : "AUTHENTIC_HUMAN_SPEECH");
  const requiresEscalation = fraudData?.requires_human_escalation ?? isSuspicious;

  return (
    <div className="fraud-advisory-box" role="region" aria-label="Fraud prevention advisory">
      <div className="advisory-header">
        <div className="advisory-title-group">
          <span className="advisory-eyebrow">FRAUD PREVENTION PROTOCOL</span>
          <h3>Threat Assessment: <span className={isHighRisk ? "threat-danger" : isSuspicious ? "threat-warning" : "threat-safe"}>{threatCategory.replace(/_/g, " ")}</span></h3>
        </div>
        {requiresEscalation && (
          <span className="escalation-badge">⚠️ Escalation Required</span>
        )}
      </div>

      {fraudData?.sha256_hash && (
        <div className="sha-fingerprint">
          <span className="sha-label">SHA-256 Fingerprint:</span>
          <code>{fraudData.sha256_hash}</code>
        </div>
      )}

      {fraudData?.advisory_actions && fraudData.advisory_actions.length > 0 ? (
        <div className="actions-list">
          <span className="actions-label">Recommended Countermeasures:</span>
          <ul>
            {fraudData.advisory_actions.map((action, idx) => (
              <li key={idx} className={`action-item action-${action.severity.toLowerCase()}`}>
                <span className="action-tag">{action.action_type.replace(/_/g, " ")}</span>
                <p>{action.description}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="clean-advisory-note">
          ✓ No active threat indicators detected. Standard voice biometric workflows permitted.
        </p>
      )}
    </div>
  );
}
