import io
import wave
import numpy as np
import pytest
from fastapi.testclient import TestClient

from core.constants import MAX_TIMELINE_SEGMENTS, NUM_MFCC_COEFFICIENTS
from main import MAX_UPLOAD_SIZE, app
from services.feature_extractor import extract_acoustic_features, extract_mfcc_features
from services.incident_service import _AUDIT_LOG_FILE
from services.segment_analyzer import analyze_temporal_segments


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def preserve_audit_log():
    """Preserve existing audit log file state across tests."""
    backup = _AUDIT_LOG_FILE.read_bytes() if _AUDIT_LOG_FILE.exists() else None
    yield
    if backup is not None:
        _AUDIT_LOG_FILE.write_bytes(backup)
    elif _AUDIT_LOG_FILE.exists():
        _AUDIT_LOG_FILE.unlink()


def _make_organic_signal(duration: float, sample_rate: int = 16000, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, duration, int(duration * sample_rate), endpoint=False)
    f0 = 155.0 + 12.0 * np.sin(2 * np.pi * 3.1 * t) + 5.0 * np.sin(2 * np.pi * 7.2 * t)
    phase = 2 * np.pi * np.cumsum(f0) / sample_rate
    return (
        0.4 * np.sin(phase)
        + 0.2 * np.sin(2 * phase)
        + 0.015 * rng.normal(size=len(t))
    ).astype(np.float32)


def _make_synthetic_splice(duration: float, sample_rate: int = 16000) -> np.ndarray:
    t = np.linspace(0, duration, int(duration * sample_rate), endpoint=False)
    return (
        0.35 * np.sin(2 * np.pi * 380.0 * t)
        + 0.30 * np.sin(2 * np.pi * 1520.0 * t)
        + 0.25 * np.sin(2 * np.pi * 2660.0 * t)
    ).astype(np.float32)


def _to_wav_bytes(samples: np.ndarray, sample_rate: int = 16000) -> bytes:
    pcm = (np.clip(samples, -1.0, 1.0) * 32767.0).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def test_extract_mfcc_features_shape_and_flux():
    sr = 16000
    organic = _make_organic_signal(1.5, sr)
    mfcc_means, cepstral_flux = extract_mfcc_features(organic, sr)

    assert len(mfcc_means) == NUM_MFCC_COEFFICIENTS
    assert all(isinstance(v, float) for v in mfcc_means)
    assert cepstral_flux > 0.0

    # Short degenerate sample should return zero-padded vector cleanly
    short_mfcc, short_flux = extract_mfcc_features(np.zeros(10, dtype=np.float32), sr)
    assert len(short_mfcc) == NUM_MFCC_COEFFICIENTS
    assert short_flux == 0.0


def test_extract_acoustic_features_includes_mfcc():
    sr = 16000
    organic = _make_organic_signal(1.0, sr)
    feats = extract_acoustic_features(organic, sr)
    assert feats.mfcc_means is not None
    assert len(feats.mfcc_means) == NUM_MFCC_COEFFICIENTS
    assert feats.cepstral_flux is not None
    assert feats.cepstral_flux >= 0.0


def test_continuous_organic_signal_no_splice():
    sr = 16000
    organic = _make_organic_signal(2.5, sr, seed=42)
    timeline = analyze_temporal_segments(organic, sr)

    assert timeline.total_segments > 1
    assert timeline.anomalous_segments == 0
    assert timeline.splicing_detected is False
    assert timeline.splice_timestamps == []
    assert timeline.peak_fake_probability < 0.35


def test_partial_spoof_splice_localization():
    sr = 16000
    spliced = np.concatenate([
        _make_organic_signal(1.6, sr, seed=7),
        _make_synthetic_splice(0.8, sr),
        _make_organic_signal(1.6, sr, seed=11),
    ]).astype(np.float32)

    timeline = analyze_temporal_segments(spliced, sr)

    assert timeline.splicing_detected is True
    assert len(timeline.splice_timestamps) >= 1
    assert any(1.0 <= ts <= 2.6 for ts in timeline.splice_timestamps)
    assert timeline.anomalous_segments >= 1
    assert timeline.peak_fake_probability >= 0.65


def test_short_audio_falls_back_to_single_segment():
    sr = 16000
    short = _make_organic_signal(0.15, sr)
    timeline = analyze_temporal_segments(short, sr)

    assert timeline.total_segments == 1
    assert timeline.segments[0].start_seconds == 0.0
    assert timeline.splicing_detected is False


def test_long_audio_caps_segment_count():
    sr = 16000
    # 45s silent/low-tone buffer should adaptively increase hop to bound segment count
    long_audio = np.zeros(45 * sr, dtype=np.float32)
    timeline = analyze_temporal_segments(long_audio, sr)

    assert timeline.total_segments <= MAX_TIMELINE_SEGMENTS + 2
    assert timeline.hop_seconds > 0.25


def test_analyze_endpoint_escalates_partial_spoof(client):
    sr = 16000
    spliced = np.concatenate([
        _make_organic_signal(1.6, sr, seed=7),
        _make_synthetic_splice(0.8, sr),
        _make_organic_signal(1.6, sr, seed=11),
    ]).astype(np.float32)
    wav_bytes = _to_wav_bytes(spliced, sr)

    response = client.post(
        "/api/v1/analyze",
        files={"file": ("partial_spoof.wav", wav_bytes, "audio/wav")},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["timeline"] is not None
    assert data["timeline"]["splicing_detected"] is True
    assert data["risk_level"] in ("SUSPICIOUS", "HIGH_RISK_DEEPFAKE")
    assert data["fraud_prevention"]["requires_human_escalation"] is True
    assert any("Partial spoof alert" in ind for ind in data["indicators"])
    assert len(data["features"]["mfcc_means"]) == NUM_MFCC_COEFFICIENTS


def test_timeline_endpoint_and_validation(client):
    sr = 16000
    spliced = np.concatenate([
        _make_organic_signal(1.2, sr, seed=3),
        _make_synthetic_splice(0.8, sr),
    ]).astype(np.float32)
    wav_bytes = _to_wav_bytes(spliced, sr)

    resp = client.post(
        "/api/v1/analyze/timeline?window_seconds=0.5&hop_seconds=0.25",
        files={"file": ("splice_check.wav", wav_bytes, "audio/wav")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["filename"] == "splice_check.wav"
    assert body["sample_rate"] == sr
    assert body["timeline"]["splicing_detected"] is True
    assert body["timeline"]["total_segments"] >= 5

    # Unsupported format check
    bad_ext = client.post(
        "/api/v1/analyze/timeline",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert bad_ext.status_code == 400

    # Oversized upload middleware protection
    too_big = b"\0" * (MAX_UPLOAD_SIZE + 1)
    oversized = client.post(
        "/api/v1/analyze/timeline",
        files={"file": ("huge.wav", too_big, "audio/wav")},
    )
    assert oversized.status_code == 413
