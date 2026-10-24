try:
    from schemas.fraud import AdvisoryAction, FraudRiskReport
except ImportError:
    from backend.schemas.fraud import AdvisoryAction, FraudRiskReport


def evaluate_fraud_risk(
    fake_probability: float,
    sha256_hash: str,
    duration_seconds: float = 0.0,
) -> FraudRiskReport:
    """
    Evaluates fraud threat posture based on synthetic voice detection scores,
    audio duration, and known threat patterns.
    """
    impersonation_score = round(fake_probability * 100.0, 1)
    actions: list[AdvisoryAction] = []

    if impersonation_score < 35.0:
        threat_category = "AUTHENTIC_HUMAN_SPEECH"
        escalation = False
        actions.append(
            AdvisoryAction(
                action_type="STANDARD_PROCESSING",
                description="Audio profile is consistent with genuine biological voice. Standard security workflows apply.",
                severity="LOW",
            )
        )
    elif impersonation_score < 65.0:
        threat_category = "SUSPECTED_VOICE_SYNTHESIS"
        escalation = True
        actions.append(
            AdvisoryAction(
                action_type="MULTI_FACTOR_CHALLENGE",
                description="Trigger secondary out-of-band (OOB) authentication before approving sensitive requests.",
                severity="MEDIUM",
            )
        )
        actions.append(
            AdvisoryAction(
                action_type="CALLBACK_VERIFICATION",
                description="Conduct voice callback to verified registered phone number to prevent unauthorized spoofing.",
                severity="MEDIUM",
            )
        )
    else:
        threat_category = "CRITICAL_VOICE_CLONING_FRAUD"
        escalation = True
        actions.append(
            AdvisoryAction(
                action_type="BLOCK_SENSITIVE_ACTIONS",
                description="Halt funds transfers, password resets, and critical account changes pending investigation.",
                severity="URGENT",
            )
        )
        actions.append(
            AdvisoryAction(
                action_type="SECURITY_OPERATIONS_ESCALATION",
                description="Forward audio SHA-256 fingerprint and forensic metadata to Fraud Operations / SIEM.",
                severity="HIGH",
            )
        )
        actions.append(
            AdvisoryAction(
                action_type="BIOMETRIC_AUTH_OVERRIDE",
                description="Revoke voice biometric authentication token and enforce physical/FIDO2 hardware verification.",
                severity="URGENT",
            )
        )

    return FraudRiskReport(
        sha256_hash=sha256_hash,
        impersonation_threat_score=impersonation_score,
        threat_category=threat_category,
        requires_human_escalation=escalation,
        advisory_actions=actions,
    )
