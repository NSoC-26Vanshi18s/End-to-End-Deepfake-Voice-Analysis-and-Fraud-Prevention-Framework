import os
from pathlib import Path
from services.audit_logger import _rotate_audit_log_if_needed, _AUDIT_LOG_FILE, log_fraud_incident


def test_rotate_audit_log_triggers_when_size_exceeded(tmp_path, monkeypatch):
    test_log = tmp_path / "test_events.log"
    # Create fake log file exceeding 100 bytes
    test_log.write_text("A" * 150, encoding="utf-8")

    monkeypatch.setattr("services.audit_logger._AUDIT_LOG_FILE", test_log)

    _rotate_audit_log_if_needed(max_bytes=100, backup_count=3)

    assert not test_log.exists() or test_log.stat().st_size == 0
    backup_1 = tmp_path / "test_events.log.1"
    assert backup_1.exists()
    assert backup_1.stat().st_size == 150


def test_log_fraud_incident_creates_and_rotates(tmp_path, monkeypatch):
    test_log = tmp_path / "audit_test.log"
    monkeypatch.setattr("services.audit_logger._AUDIT_LOG_FILE", test_log)

    inc = log_fraud_incident(
        filename="test.wav",
        sha256_hash="0" * 64,
        fake_probability=0.9,
        threat_category="CRITICAL_VOICE_CLONING_FRAUD",
        requires_human_escalation=True,
    )

    assert inc.incident_id.startswith("INC-")
    assert test_log.exists()
