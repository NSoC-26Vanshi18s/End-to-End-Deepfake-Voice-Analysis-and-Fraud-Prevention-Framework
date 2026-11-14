from typing import Optional
from pydantic import BaseModel, Field

try:
    from schemas.audio import AcousticFeatures
    from schemas.fraud import FraudRiskReport
except ImportError:
    from backend.schemas.audio import AcousticFeatures
    from backend.schemas.fraud import FraudRiskReport


class ForensicBreakdown(BaseModel):
    spectral_consistency: float = Field(..., description="Score 0-100 indicating spectral naturalness")
    pitch_naturalness: float = Field(..., description="Score 0-100 indicating natural biological pitch micro-tremors")
    vocoder_artifact_score: float = Field(..., description="Score 0-100 indicating presence of neural synthesis artifacts")


class DetectionResult(BaseModel):
    fake_probability: float = Field(..., description="Estimated synthetic probability (0.0 to 1.0)")
    confidence_score: float = Field(..., description="Confidence percentage of the forensic verdict (0.0 to 100.0)")
    risk_level: str = Field(..., description="Risk tier: LOW_RISK, SUSPICIOUS, or HIGH_RISK_DEEPFAKE")
    indicators: list[str] = Field(default_factory=list, description="Forensic red flags or verification notes")
    breakdown: ForensicBreakdown


class SegmentAnalysis(BaseModel):
    segment_index: int = Field(..., description="Zero-based chronological index of the audio window")
    start_seconds: float = Field(..., description="Window start offset in seconds")
    end_seconds: float = Field(..., description="Window end offset in seconds")
    fake_probability: float = Field(..., description="Segment-level synthetic voice probability (0.0 to 1.0)")
    risk_level: str = Field(..., description="Segment risk tier: LOW_RISK, SUSPICIOUS, or HIGH_RISK_DEEPFAKE")
    is_voiced: bool = Field(..., description="Whether segment exceeds active speech RMS threshold")
    spectral_centroid_hz: float = Field(..., description="Mean spectral centroid within the segment")
    snr_db: Optional[float] = Field(None, description="Local signal-to-noise ratio estimate in dB")
    boundary_distance: float = Field(0.0, description="Acoustic distance from preceding active segment")
    splice_detected: bool = Field(False, description="True when an abrupt timbral splice jump occurs at segment start")


class TimelineAnalysis(BaseModel):
    window_seconds: float = Field(..., description="Sliding window duration in seconds")
    hop_seconds: float = Field(..., description="Step interval between consecutive windows in seconds")
    total_segments: int = Field(..., description="Total evaluated windows across the audio file")
    anomalous_segments: int = Field(..., description="Number of voiced segments classified as suspicious or high-risk")
    peak_fake_probability: float = Field(..., description="Maximum synthetic probability observed across voiced windows")
    splicing_detected: bool = Field(..., description="True when partial-spoof acoustic boundary discontinuities are found")
    splice_timestamps: list[float] = Field(default_factory=list, description="Timestamps (seconds) of suspected audio splices")
    segments: list[SegmentAnalysis] = Field(default_factory=list, description="Ordered per-window forensic breakdown")


class TimelineAnalysisResponse(BaseModel):
    filename: str = Field(..., description="Name of the analyzed audio file")
    duration_seconds: float = Field(..., description="Total duration of the audio sample in seconds")
    sample_rate: int = Field(..., description="Audio sample rate in Hz")
    timeline: TimelineAnalysis = Field(..., description="Temporal segment localization and splice analysis report")


class AnalysisResponse(BaseModel):
    filename: str = Field(..., description="Name of the analyzed audio file")
    status: str = Field("completed", description="Analysis execution state")
    fake_probability: float = Field(..., description="Calculated probability that the voice sample is synthetic (0.0 to 1.0)")
    confidence_score: float = Field(..., description="Confidence percentage of the forensic verdict (0.0 to 100.0)")
    risk_level: str = Field(..., description="Risk categorization: LOW_RISK, SUSPICIOUS, or HIGH_RISK_DEEPFAKE")
    indicators: list[str] = Field(default_factory=list, description="Forensic red flags or verification notes")
    breakdown: ForensicBreakdown = Field(..., description="Forensic breakdown component scores")
    features: AcousticFeatures = Field(..., description="Extracted physical and spectral acoustic features")
    fraud_prevention: FraudRiskReport = Field(..., description="Fraud risk report with recommended mitigation actions")
    incident_id: str = Field(..., description="Unique audit incident identifier")
    sha256_hash: str = Field(..., description="Cryptographic SHA-256 hash of the audio binary")
    timeline: Optional[TimelineAnalysis] = Field(None, description="Sliding-window temporal segment and splice localization")

