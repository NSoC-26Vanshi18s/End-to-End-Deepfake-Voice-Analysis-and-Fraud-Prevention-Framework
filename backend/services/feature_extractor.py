import numpy as np
from scipy import signal
from scipy.fft import dct

try:
    from core.constants import NUM_MEL_BANDS, NUM_MFCC_COEFFICIENTS
    from schemas.audio import AcousticFeatures
    from services.audio_enhancer import estimate_snr_db
except ImportError:
    from backend.core.constants import NUM_MEL_BANDS, NUM_MFCC_COEFFICIENTS
    from backend.schemas.audio import AcousticFeatures
    from backend.services.audio_enhancer import estimate_snr_db


def _build_mel_filterbank(sample_rate: int, n_fft: int, n_mels: int) -> np.ndarray:
    """Constructs a triangular Mel-scale filterbank matrix of shape (n_mels, n_fft // 2 + 1)."""
    n_bins = n_fft // 2 + 1
    high_mel = 2595.0 * np.log10(1.0 + (sample_rate / 2.0) / 700.0)
    mel_points = np.linspace(0.0, high_mel, n_mels + 2)
    hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)
    bin_points = np.clip(np.floor((n_fft + 1) * hz_points / sample_rate).astype(int), 0, n_bins - 1)

    filterbank = np.zeros((n_mels, n_bins), dtype=np.float32)
    for m in range(1, n_mels + 1):
        left, center, right = bin_points[m - 1], bin_points[m], bin_points[m + 1]
        if center > left:
            for k in range(left, center):
                filterbank[m - 1, k] = (k - left) / float(center - left)
        if right > center:
            for k in range(center, right):
                filterbank[m - 1, k] = (right - k) / float(right - center)
        if left == center == right:
            filterbank[m - 1, center] = 1.0
    return filterbank


def extract_mfcc_features(
    audio: np.ndarray,
    sample_rate: int,
    num_ceps: int = NUM_MFCC_COEFFICIENTS,
    n_mels: int = NUM_MEL_BANDS,
) -> tuple[list[float], float]:
    """
    Extracts mean Mel-Frequency Cepstral Coefficients (MFCCs) and cepstral flux
    (inter-frame L2 delta) from mono audio using Mel filterbanks and DCT-II.
    """
    if len(audio) < 32 or sample_rate <= 0:
        return [0.0] * num_ceps, 0.0

    emphasized = np.append(audio[0], audio[1:] - 0.97 * audio[:-1])
    nperseg = min(512, len(emphasized))
    noverlap = nperseg // 2

    _, _, zxx = signal.stft(
        emphasized,
        fs=sample_rate,
        nperseg=nperseg,
        noverlap=noverlap,
        boundary=None,
    )

    if zxx.shape[1] == 0:
        return [0.0] * num_ceps, 0.0

    power_spec = (np.abs(zxx) ** 2) / float(nperseg)
    filterbank = _build_mel_filterbank(sample_rate, nperseg, n_mels)
    mel_energies = np.maximum(filterbank @ power_spec, 1e-10)
    log_mel = np.log(mel_energies)

    mfccs = dct(log_mel, type=2, axis=0, norm="ortho")[:num_ceps, :]
    mfcc_means = [round(float(val), 4) for val in np.mean(mfccs, axis=1)]

    if mfccs.shape[1] >= 2:
        deltas = np.diff(mfccs, axis=1)
        cepstral_flux = round(float(np.mean(np.linalg.norm(deltas, axis=0))), 4)
    else:
        cepstral_flux = 0.0

    return mfcc_means, cepstral_flux


def extract_acoustic_features(audio: np.ndarray, sample_rate: int, channels: int = 1) -> AcousticFeatures:
    """
    Extracts forensic acoustic features from normalized mono audio.
    """
    duration = float(len(audio)) / float(sample_rate)

    signs = np.signbit(audio)
    zcr = float(np.mean(signs[:-1] != signs[1:]))

    rms_energy = float(np.sqrt(np.mean(audio ** 2)))

    nperseg = min(1024, max(64, len(audio)))
    noverlap = nperseg // 2

    freqs, _, zxx = signal.stft(
        audio,
        fs=sample_rate,
        nperseg=nperseg,
        noverlap=noverlap,
        boundary=None,
    )

    mag_spec = np.abs(zxx) + 1e-10
    power_spec = mag_spec ** 2

    freq_grid = freqs[:, np.newaxis]
    total_energy = np.sum(mag_spec, axis=0)
    frame_centroids = np.sum(freq_grid * mag_spec, axis=0) / total_energy
    spectral_centroid = float(np.mean(frame_centroids))

    cumsum_power = np.cumsum(power_spec, axis=0)
    total_power = cumsum_power[-1:, :]
    rolloff_mask = cumsum_power >= (0.85 * total_power)
    rolloff_indices = np.argmax(rolloff_mask, axis=0)
    spectral_rolloff = float(np.mean(freqs[rolloff_indices]))

    eps = 1e-10
    log_power = np.log(power_spec + eps)
    geom_mean = np.exp(np.mean(log_power, axis=0))
    arith_mean = np.mean(power_spec, axis=0) + eps
    spectral_flatness = float(np.mean(geom_mean / arith_mean))

    f0_mean, jitter, shimmer = _estimate_pitch_and_perturbation(audio, sample_rate)

    snr_db = estimate_snr_db(audio, sample_rate)
    mfcc_means, cepstral_flux = extract_mfcc_features(audio, sample_rate)

    return AcousticFeatures(
        sample_rate=sample_rate,
        duration_seconds=round(duration, 3),
        channels=channels,
        zero_crossing_rate=round(zcr, 4),
        rms_energy=round(rms_energy, 4),
        spectral_centroid_hz=round(spectral_centroid, 2),
        spectral_rolloff_hz=round(spectral_rolloff, 2),
        spectral_flatness=round(spectral_flatness, 4),
        fundamental_frequency_hz=round(f0_mean, 2) if f0_mean is not None else None,
        pitch_jitter=round(jitter, 4) if jitter is not None else None,
        shimmer=round(shimmer, 4) if shimmer is not None else None,
        snr_db=round(snr_db, 1),
        mfcc_means=mfcc_means,
        cepstral_flux=cepstral_flux,
    )


def _estimate_pitch_and_perturbation(
    audio: np.ndarray, sample_rate: int
) -> tuple[float | None, float | None, float | None]:
    frame_len = int(0.04 * sample_rate)
    hop_len = int(0.02 * sample_rate)
    min_lag = max(1, int(sample_rate / 500))
    max_lag = min(frame_len - 1, int(sample_rate / 70))

    if len(audio) < frame_len or max_lag <= min_lag:
        return None, None, None

    f0_values = []
    amplitudes = []

    num_frames = (len(audio) - frame_len) // hop_len
    for i in range(num_frames):
        start = i * hop_len
        frame = audio[start : start + frame_len]
        frame = frame - np.mean(frame)
        frame_rms = np.sqrt(np.mean(frame ** 2))

        if frame_rms < 0.01:
            continue

        autocorr = np.correlate(frame, frame, mode="full")
        autocorr = autocorr[len(frame) - 1 :]
        r0 = autocorr[0] + 1e-10

        norm_autocorr = autocorr[min_lag:max_lag] / r0
        if len(norm_autocorr) == 0:
            continue

        peak_idx = int(np.argmax(norm_autocorr))
        peak_val = float(norm_autocorr[peak_idx])

        if peak_val > 0.35:
            lag = min_lag + peak_idx
            f0 = sample_rate / lag
            f0_values.append(f0)
            amplitudes.append(frame_rms)

    if len(f0_values) < 4:
        return None, None, None

    f0_arr = np.array(f0_values)
    amp_arr = np.array(amplitudes)

    f0_mean = float(np.mean(f0_arr))
    f0_diffs = np.abs(np.diff(f0_arr))
    jitter = float(np.mean(f0_diffs) / (f0_mean + 1e-10))

    amp_diffs = np.abs(np.diff(amp_arr))
    shimmer = float(np.mean(amp_diffs) / (np.mean(amp_arr) + 1e-10))

    return f0_mean, jitter, shimmer
