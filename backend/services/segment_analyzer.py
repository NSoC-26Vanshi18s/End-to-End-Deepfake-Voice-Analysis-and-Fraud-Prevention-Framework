import math
import numpy as np

try:
    from core.constants import (
        ACTIVE_RMS_THRESHOLD,
        DEFAULT_SEGMENT_HOP_SECONDS,
        DEFAULT_SEGMENT_WINDOW_SECONDS,
        MAX_TIMELINE_SEGMENTS,
        RISK_LEVEL_LOW,
        SPLICE_DISTANCE_MIN_THRESHOLD,
        SPLICE_MAD_MULTIPLIER,
    )
    from schemas.detection import SegmentAnalysis, TimelineAnalysis
    from services.detector import detect_synthetic_voice
    from services.feature_extractor import extract_acoustic_features
except ImportError:
    from backend.core.constants import (
        ACTIVE_RMS_THRESHOLD,
        DEFAULT_SEGMENT_HOP_SECONDS,
        DEFAULT_SEGMENT_WINDOW_SECONDS,
        MAX_TIMELINE_SEGMENTS,
        RISK_LEVEL_LOW,
        SPLICE_DISTANCE_MIN_THRESHOLD,
        SPLICE_MAD_MULTIPLIER,
    )
    from backend.schemas.detection import SegmentAnalysis, TimelineAnalysis
    from backend.services.detector import detect_synthetic_voice
    from backend.services.feature_extractor import extract_acoustic_features


def _build_timbre_vector(features) -> np.ndarray:
    """Constructs a normalized acoustic timbre vector ignoring global energy C0."""
    mfccs = features.mfcc_means or [0.0] * 13
    mfcc_slice = np.array(mfccs[1:8], dtype=np.float32)
    centroid_scaled = float(features.spectral_centroid_hz) / 1000.0
    flatness_scaled = float(features.spectral_flatness) * 5.0
    return np.concatenate([mfcc_slice, np.array([centroid_scaled, flatness_scaled], dtype=np.float32)])


def _compute_window_bounds(
    total_samples: int,
    sample_rate: int,
    window_seconds: float,
    hop_seconds: float,
) -> tuple[list[tuple[int, int]], float, float]:
    """Computes (start, end) sample slices, scaling hop for very long recordings."""
    duration = total_samples / float(sample_rate)
    eff_hop = hop_seconds
    if duration > 0 and (duration / hop_seconds) > MAX_TIMELINE_SEGMENTS:
        eff_hop = round(duration / float(MAX_TIMELINE_SEGMENTS), 3)

    eff_window = max(window_seconds, eff_hop)
    window_samples = max(256, int(eff_window * sample_rate))
    hop_samples = max(128, int(eff_hop * sample_rate))

    if total_samples <= window_samples:
        return [(0, total_samples)], round(duration, 3), round(duration, 3)

    bounds: list[tuple[int, int]] = []
    start = 0
    while start + window_samples <= total_samples:
        bounds.append((start, start + window_samples))
        start += hop_samples

    last_end = bounds[-1][1]
    if total_samples - last_end >= max(256, hop_samples // 2):
        bounds.append((total_samples - window_samples, total_samples))

    return bounds, round(eff_window, 3), round(eff_hop, 3)


def analyze_temporal_segments(
    audio: np.ndarray,
    sample_rate: int,
    window_seconds: float = DEFAULT_SEGMENT_WINDOW_SECONDS,
    hop_seconds: float = DEFAULT_SEGMENT_HOP_SECONDS,
) -> TimelineAnalysis:
    """
    Runs sliding-window forensic analysis across audio segments to localize
    partial spoofs and detect acoustic splice boundary discontinuities.
    """
    if len(audio) == 0 or sample_rate <= 0:
        return TimelineAnalysis(
            window_seconds=window_seconds,
            hop_seconds=hop_seconds,
            total_segments=0,
            anomalous_segments=0,
            peak_fake_probability=0.0,
            splicing_detected=False,
            splice_timestamps=[],
            segments=[],
        )

    bounds, eff_window, eff_hop = _compute_window_bounds(
        len(audio), sample_rate, window_seconds, hop_seconds
    )

    segments: list[SegmentAnalysis] = []
    active_distances: list[float] = []
    prev_active_vec: np.ndarray | None = None

    for idx, (start_idx, end_idx) in enumerate(bounds):
        chunk = audio[start_idx:end_idx]
        features = extract_acoustic_features(chunk, sample_rate=sample_rate, channels=1)
        detection = detect_synthetic_voice(
            audio=chunk,
            sample_rate=sample_rate,
            pitch_jitter=features.pitch_jitter,
            shimmer=features.shimmer,
            spectral_flatness=features.spectral_flatness,
        )

        is_voiced = features.rms_energy >= ACTIVE_RMS_THRESHOLD
        boundary_dist = 0.0

        if is_voiced:
            vec = _build_timbre_vector(features)
            if prev_active_vec is not None:
                boundary_dist = round(float(np.linalg.norm(vec - prev_active_vec)), 3)
                active_distances.append(boundary_dist)
            prev_active_vec = vec

        segments.append(
            SegmentAnalysis(
                segment_index=idx,
                start_seconds=round(start_idx / float(sample_rate), 3),
                end_seconds=round(end_idx / float(sample_rate), 3),
                fake_probability=detection.fake_probability,
                risk_level=detection.risk_level,
                is_voiced=is_voiced,
                spectral_centroid_hz=features.spectral_centroid_hz,
                snr_db=features.snr_db,
                boundary_distance=boundary_dist,
                splice_detected=False,
            )
        )

    # Identify statistical boundary outliers indicative of audio splicing
    splice_timestamps: list[float] = []
    if active_distances:
        if len(active_distances) >= 3:
            median_dist = float(np.median(active_distances))
            mad = float(np.median(np.abs(np.array(active_distances) - median_dist)))
            scaled_mad = max(mad * 1.4826, 0.25)
            splice_threshold = max(
                SPLICE_DISTANCE_MIN_THRESHOLD,
                median_dist + SPLICE_MAD_MULTIPLIER * scaled_mad,
            )
        else:
            splice_threshold = SPLICE_DISTANCE_MIN_THRESHOLD * 1.5

        for seg in segments:
            if seg.is_voiced and seg.boundary_distance >= splice_threshold and not math.isclose(seg.boundary_distance, 0.0):
                seg.splice_detected = True
                splice_timestamps.append(seg.start_seconds)

    voiced_segments = [s for s in segments if s.is_voiced]
    eval_segments = voiced_segments if voiced_segments else segments

    anomalous_count = sum(1 for s in eval_segments if s.risk_level != RISK_LEVEL_LOW)
    peak_prob = max((s.fake_probability for s in eval_segments), default=0.0)

    return TimelineAnalysis(
        window_seconds=eff_window,
        hop_seconds=eff_hop,
        total_segments=len(segments),
        anomalous_segments=anomalous_count,
        peak_fake_probability=round(peak_prob, 3),
        splicing_detected=len(splice_timestamps) > 0,
        splice_timestamps=splice_timestamps,
        segments=segments,
    )
