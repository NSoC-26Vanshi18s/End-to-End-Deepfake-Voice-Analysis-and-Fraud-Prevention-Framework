from pathlib import Path
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

try:
    from core.constants import (
        DEFAULT_SEGMENT_HOP_SECONDS,
        DEFAULT_SEGMENT_WINDOW_SECONDS,
        SUPPORTED_AUDIO_EXTENSIONS,
    )
    from schemas.detection import TimelineAnalysisResponse
    from services.audio_validator import validate_and_decode_audio
    from services.segment_analyzer import analyze_temporal_segments
except ImportError:
    from backend.core.constants import (
        DEFAULT_SEGMENT_HOP_SECONDS,
        DEFAULT_SEGMENT_WINDOW_SECONDS,
        SUPPORTED_AUDIO_EXTENSIONS,
    )
    from backend.schemas.detection import TimelineAnalysisResponse
    from backend.services.audio_validator import validate_and_decode_audio
    from backend.services.segment_analyzer import analyze_temporal_segments

router = APIRouter(prefix="/analyze/timeline", tags=["Temporal Segment Analysis"])


@router.post("", response_model=TimelineAnalysisResponse)
async def analyze_audio_timeline(
    file: UploadFile = File(...),
    window_seconds: float = Query(
        DEFAULT_SEGMENT_WINDOW_SECONDS,
        ge=0.2,
        le=5.0,
        description="Sliding window length in seconds",
    ),
    hop_seconds: float = Query(
        DEFAULT_SEGMENT_HOP_SECONDS,
        ge=0.1,
        le=2.5,
        description="Hop stride between consecutive windows in seconds",
    ),
):
    """
    Performs fine-grained sliding-window forensic analysis to localize partial
    synthetic voice spoofs and detect acoustic splice discontinuities.
    """
    filename = file.filename or "audio_sample.wav"
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format. Supported formats: WAV, MP3, OGG, FLAC, M4A.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded audio file is empty.",
        )

    audio, sample_rate, _, _ = validate_and_decode_audio(contents, filename=filename)
    duration = round(len(audio) / float(sample_rate), 3)
    timeline = analyze_temporal_segments(
        audio=audio,
        sample_rate=sample_rate,
        window_seconds=window_seconds,
        hop_seconds=hop_seconds,
    )

    return TimelineAnalysisResponse(
        filename=filename,
        duration_seconds=duration,
        sample_rate=sample_rate,
        timeline=timeline,
    )
