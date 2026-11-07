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

MAX_AUDIT_LOG_BYTES = 10 * 1024 * 1024  # 10 MB per audit log file
MAX_BACKUP_LOGS = 5


def _rotate_audit_log_if_needed(max_bytes: int = MAX_AUDIT_LOG_BYTES, backup_count: int = MAX_BACKUP_LOGS):
    """Rotates the audit log file when it exceeds the specified maximum byte size."""
    if not _AUDIT_LOG_FILE.exists():
        return

    try:
        if _AUDIT_LOG_FILE.stat().st_size < max_bytes:
            return

        for i in range(backup_count - 1, 0, -1):
            sfn = _AUDIT_LOG_FILE.parent / f"{_AUDIT_LOG_FILE.name}.{i}"
            dfn = _AUDIT_LOG_FILE.parent / f"{_AUDIT_LOG_FILE.name}.{i + 1}"
            if sfn.exists():
                if dfn.exists():
                    dfn.unlink()
                sfn.rename(dfn)

        dfn = _AUDIT_LOG_FILE.parent / f"{_AUDIT_LOG_FILE.name}.1"
        if dfn.exists():
            dfn.unlink()
        _AUDIT_LOG_FILE.rename(dfn)
    except Exception as exc:
        logger.warning("Failed to rotate audit log: %s", exc)


def log_fraud_incident(
    filename: str,
    sha256_hash: str,
    fake_probability: float,
    threat_category: str,
    requires_human_escalation: bool,
    client_host: str | None = None,
) -> IncidentAuditLog:
    """
    Records a structured security incident audit event with automated log file rotation.
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
        _rotate_audit_log_if_needed()
        with open(_AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(incident.model_dump()) + chr(10))
    except Exception as exc:
        logger.warning("Could not persist audit event to file: %s", exc)

    return incident
