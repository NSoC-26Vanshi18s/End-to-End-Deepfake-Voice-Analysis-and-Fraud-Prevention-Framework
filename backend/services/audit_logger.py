import datetime
import uuid
import json
import logging
from pathlib import Path

try:
    from schemas.fraud import IncidentAuditLog
except ImportError:
    from backend.schemas.fraud import IncidentAuditLog

logger = logging.getLogger("fraud_prevention_audit")
_AUDIT_LOG_FILE = Path(__file__).resolve().parent.parent / "fraud_audit_events.log"


def log_fraud_incident(
    filename: str,
    sha256_hash: str,
    fake_probability: float,
    threat_category: str,
    requires_human_escalation: bool,
    client_host: str | None = None,
) -> IncidentAuditLog:
    """
    Records a structured security incident audit event.
    """
    incident = IncidentAuditLog(
        incident_id=f"INC-{uuid.uuid4().hex[:12].upper()}",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        filename=filename,
        sha256_hash=sha256_hash,
        fake_probability=fake_probability,
        threat_category=threat_category,
        requires_human_escalation=requires_human_escalation,
        client_host=client_host,
    )

    try:
        with open(_AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(incident.model_dump()) + "\n")
    except Exception as exc:
        logger.warning("Could not persist audit event to file: %s", exc)

    return incident
