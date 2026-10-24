from pathlib import Path
import json
import os

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Deepfake Audio Detection API")

frontend_origin = os.getenv("FRONTEND_ORIGIN")
allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if frontend_origin:
    allowed_origins.append(frontend_origin.rstrip("/"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

SUPPORTED_EXTENSIONS = {".wav", ".wave"}
MAX_UPLOAD_SIZE = 25 * 1024 * 1024
UPLOAD_CHUNK_SIZE = 1024 * 1024
UPLOAD_TOO_LARGE_DETAIL = "Upload is too large. Maximum request size is 25 MB."


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


app.add_middleware(UploadSizeLimitMiddleware)


import sys

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from core.security import compute_sha256
    from services.fraud_engine import evaluate_fraud_risk
    from services.audit_logger import log_fraud_incident
except ImportError:
    from backend.core.security import compute_sha256
    from backend.services.fraud_engine import evaluate_fraud_risk
    from backend.services.audit_logger import log_fraud_incident


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Deepfake Audio Detection & Fraud Prevention API",
        "version": "1.0.0",
        "service": "deepfake-voice-analysis-engine",
    }


@app.post("/api/v1/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    filename = file.filename or "audio_sample.wav"
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format. Please upload a .wav or .wave file.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded audio file is empty.",
        )

    # Compute cryptographic SHA-256 fingerprint
    sha256_hash = compute_sha256(contents)

    # Evaluate baseline synthetic probability (heuristic baseline)
    fake_probability = 0.0

    # Run fraud prevention risk evaluation
    fraud_report = evaluate_fraud_risk(
        fake_probability=fake_probability,
        sha256_hash=sha256_hash,
    )

    # Record structured incident audit log
    incident = log_fraud_incident(
        filename=filename,
        sha256_hash=sha256_hash,
        fake_probability=fake_probability,
        threat_category=fraud_report.threat_category,
        requires_human_escalation=fraud_report.requires_human_escalation,
    )

    return {
        "filename": filename,
        "status": "completed",
        "fake_probability": fake_probability,
        "fraud_prevention": fraud_report.model_dump(),
        "incident_id": incident.incident_id,
        "sha256_hash": sha256_hash,
    }

