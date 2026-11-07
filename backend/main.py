from pathlib import Path
import json

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from api.v1.batch import router as batch_router
from api.v1.health import router as health_router
from api.v1.incidents import router as incidents_router
from core.config import get_settings
from core.middleware import RequestAuditMiddleware

app = FastAPI(title="Deepfake Audio Detection API")

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

SUPPORTED_EXTENSIONS = {".wav", ".wave", ".mp3", ".ogg", ".flac", ".m4a", ".aac"}
MAX_UPLOAD_SIZE = settings.max_upload_size
UPLOAD_CHUNK_SIZE = settings.upload_chunk_size
UPLOAD_TOO_LARGE_DETAIL = (
    f"Upload is too large. Maximum request size is {MAX_UPLOAD_SIZE // (1024 * 1024)} MB."
)


class UploadSizeLimitMiddleware:
    """Limit the streamed request body for the audio-analysis endpoint."""

    def __init__(self, app, max_bytes: int = MAX_UPLOAD_SIZE):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] != "http"
            or scope.get("method") != "POST"
            or scope.get("path") != "/api/v1/analyze"
        ):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError:
                await self._respond(send, 400, "Invalid Content-Length header.")
                return
            if declared_length < 0:
                await self._respond(send, 400, "Invalid Content-Length header.")
                return
            if declared_length > self.max_bytes:
                await self._respond(send, 413, UPLOAD_TOO_LARGE_DETAIL)
                return

        received = 0
        too_large = False

        async def limited_receive():
            nonlocal received, too_large
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    too_large = True
                    raise _UploadTooLarge
            return message

        async def guarded_send(message):
            # Starlette may try to emit an error response after limited_receive
            # raises. The middleware owns the 413 response in that case.
            if not too_large:
                await send(message)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except _UploadTooLarge:
            await self._respond(send, 413, UPLOAD_TOO_LARGE_DETAIL)

    @staticmethod
    async def _respond(send, status_code: int, detail: str):
        body = json.dumps({"detail": detail}).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        })
        await send({"type": "http.response.body", "body": body})

class _UploadTooLarge(Exception):
    """Internal signal used to stop reading an oversized request."""


app.add_middleware(RequestAuditMiddleware)
app.add_middleware(UploadSizeLimitMiddleware)
app.include_router(health_router, prefix="/api/v1")
app.include_router(incidents_router, prefix="/api/v1")
app.include_router(batch_router, prefix="/api/v1")


import sys

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from schemas.detection import AnalysisResponse
    from core.security import compute_sha256
    from services.audio_validator import validate_and_decode_wav, validate_and_decode_audio
    from services.audit_logger import log_fraud_incident
    from services.detector import detect_synthetic_voice
    from services.feature_extractor import extract_acoustic_features
    from services.fraud_engine import evaluate_fraud_risk
except ImportError:
    from backend.schemas.detection import AnalysisResponse
    from backend.core.security import compute_sha256
    from backend.services.audio_validator import validate_and_decode_wav, validate_and_decode_audio
    from backend.services.audit_logger import log_fraud_incident
    from backend.services.detector import detect_synthetic_voice
    from backend.services.feature_extractor import extract_acoustic_features
    from backend.services.fraud_engine import evaluate_fraud_risk


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Deepfake Audio Detection & Fraud Prevention API",
        "version": "1.0.0",
        "service": "deepfake-voice-analysis-engine",
    }


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_audio(file: UploadFile = File(...)):
    filename = file.filename or "audio_sample.wav"
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
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

    # Decode and validate audio payload (multi-format support)
    audio, sample_rate, channels, format_name = validate_and_decode_audio(contents, filename=filename)


    # Compute cryptographic SHA-256 fingerprint
    sha256_hash = compute_sha256(contents)

    # 2. Extract forensic acoustic & spectral features
    features = extract_acoustic_features(audio, sample_rate=sample_rate, channels=channels)

    # 3. Execute multi-heuristic deepfake detection engine
    detection = detect_synthetic_voice(
        audio=audio,
        sample_rate=sample_rate,
        pitch_jitter=features.pitch_jitter,
        shimmer=features.shimmer,
        spectral_flatness=features.spectral_flatness,
    )

    # 4. Compute cryptographic SHA-256 fingerprint
    sha256_hash = compute_sha256(contents)

    # 5. Run fraud prevention risk evaluation
    fraud_report = evaluate_fraud_risk(
        fake_probability=detection.fake_probability,
        sha256_hash=sha256_hash,
        duration_seconds=features.duration_seconds,
    )

    # 6. Record structured incident audit log
    incident = log_fraud_incident(
        filename=filename,
        sha256_hash=sha256_hash,
        fake_probability=detection.fake_probability,
        threat_category=fraud_report.threat_category,
        requires_human_escalation=fraud_report.requires_human_escalation,
    )

    return AnalysisResponse(
        filename=filename,
        status="completed",
        fake_probability=detection.fake_probability,
        confidence_score=detection.confidence_score,
        risk_level=detection.risk_level,
        indicators=detection.indicators,
        breakdown=detection.breakdown,
        features=features,
        fraud_prevention=fraud_report,
        incident_id=incident.incident_id,
        sha256_hash=sha256_hash,
    )


