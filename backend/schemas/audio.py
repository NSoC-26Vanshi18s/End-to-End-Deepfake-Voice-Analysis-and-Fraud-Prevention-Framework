from typing import Optional
from pydantic import BaseModel, Field


class AcousticFeatures(BaseModel):
    sample_rate: int = Field(..., description="Sampling rate in Hz")
    duration_seconds: float = Field(..., description="Duration of audio in seconds")
    channels: int = Field(..., description="Number of audio channels (1 for mono, 2 for stereo)")
    zero_crossing_rate: float = Field(..., description="Mean zero-crossing rate of the audio signal")
    rms_energy: float = Field(..., description="Root-mean-square energy indicating loudness dynamics")
    spectral_centroid_hz: float = Field(..., description="Center of mass of the frequency spectrum in Hz")
    spectral_rolloff_hz: float = Field(..., description="Frequency below which 85% of spectral energy lies")
    spectral_flatness: float = Field(..., description="Measure of noisiness versus tonality (0 to 1)")
    fundamental_frequency_hz: Optional[float] = Field(None, description="Estimated average pitch (F0) in Hz")
    pitch_jitter: Optional[float] = Field(None, description="Cycle-to-cycle pitch period variation")
    shimmer: Optional[float] = Field(None, description="Cycle-to-cycle amplitude perturbation")
    snr_db: Optional[float] = Field(None, description="Estimated Signal-to-Noise Ratio (SNR) in decibels")
    mfcc_means: Optional[list[float]] = Field(None, description="Mean Mel-Frequency Cepstral Coefficients across frames")
    cepstral_flux: Optional[float] = Field(None, description="Mean frame-to-frame L2 delta of MFCC trajectories")


class AudioFormatMetadata(BaseModel):
    format_name: str = Field(..., description="Detected container format (e.g., wav, mp3, ogg, flac, m4a)")
    mime_type: str = Field(..., description="Canonical MIME type")
    sample_rate: int = Field(..., description="Decoded sampling rate in Hz")
    channels: int = Field(..., description="Decoded audio channel count")
    duration_seconds: float = Field(..., description="Duration in seconds")

