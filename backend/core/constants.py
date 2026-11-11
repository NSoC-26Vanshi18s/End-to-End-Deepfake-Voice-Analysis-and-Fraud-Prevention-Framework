"""Forensic thresholds and detection constants for synthetic voice analysis."""

# Natural human voice normative ranges
HUMAN_MIN_PITCH_HZ = 70.0
HUMAN_MAX_PITCH_HZ = 500.0
HUMAN_MIN_JITTER = 0.005  # Below 0.5% indicates unnatural pitch perfection (TTS/cloning)
HUMAN_MAX_JITTER = 0.040  # Above 4.0% indicates unnatural jitter instability
HUMAN_MIN_SHIMMER = 0.015 # Below 1.5% indicates robotic amplitude constancy

# Risk level boundaries
RISK_THRESHOLD_LOW = 0.35
RISK_THRESHOLD_HIGH = 0.65

# Heuristic weights for fake probability calculation
WEIGHT_PITCH_PERFECTION = 0.30
WEIGHT_SHIMMER_ANOMALY = 0.20
WEIGHT_VOCODER_ARTIFACTS = 0.35
WEIGHT_SPECTRAL_INCOHERENCE = 0.15

# Forensic risk labels
RISK_LEVEL_LOW = "LOW_RISK"
RISK_LEVEL_SUSPICIOUS = "SUSPICIOUS"
RISK_LEVEL_HIGH = "HIGH_RISK_DEEPFAKE"

# Audio format and container definitions
SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".wave", ".mp3", ".ogg", ".flac", ".m4a", ".aac"}
MIME_TYPE_MAPPING = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "ogg": "audio/ogg",
    "flac": "audio/flac",
    "m4a": "audio/mp4",
}

# MFCC & temporal segment analysis configuration
NUM_MFCC_COEFFICIENTS = 13
NUM_MEL_BANDS = 26
DEFAULT_SEGMENT_WINDOW_SECONDS = 0.5
DEFAULT_SEGMENT_HOP_SECONDS = 0.25
MAX_TIMELINE_SEGMENTS = 120
ACTIVE_RMS_THRESHOLD = 0.005
SPLICE_DISTANCE_MIN_THRESHOLD = 1.8
SPLICE_MAD_MULTIPLIER = 3.0


