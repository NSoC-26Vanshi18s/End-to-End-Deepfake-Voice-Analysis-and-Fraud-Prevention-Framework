from typing import Optional
from pydantic import BaseModel, Field


class AdvisoryAction(BaseModel):
    action_type: str = Field(..., description="Action category (e.g., VERIFY_IDENTITY, BLOCK_TRANSACTION)")
    description: str = Field(..., description="Detailed fraud mitigation guidance for operational teams")
    severity: str = Field(..., description="Action priority: LOW, MEDIUM, HIGH, URGENT")


class FraudRiskReport(BaseModel):
    sha256_hash: str = Field(..., description="Cryptographic SHA-256 fingerprint of the audio file")
    impersonation_threat_score: float = Field(..., description="Threat score (0-100) indicating risk of voice cloning fraud")
    threat_category: str = Field(..., description="Primary suspected fraud vector (e.g. BIOMETRIC_SPOOFING, CEO_FRAUD)")
    requires_human_escalation: bool = Field(..., description="Whether security operations must manually review the transaction")
    advisory_actions: list[AdvisoryAction] = Field(default_factory=list, description="Prescribed fraud prevention counter-measures")


class IncidentAuditLog(BaseModel):
    incident_id: str
    timestamp: str
    filename: str
    sha256_hash: str
    fake_probability: float
    threat_category: str
    requires_human_escalation: bool
    client_host: Optional[str] = None
