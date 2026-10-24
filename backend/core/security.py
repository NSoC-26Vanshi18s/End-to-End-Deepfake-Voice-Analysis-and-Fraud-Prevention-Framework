import hashlib


def compute_sha256(data: bytes) -> str:
    """
    Computes a cryptographic SHA-256 hex digest for an audio byte stream
    to provide tamper verification and immutable audit tracking.
    """
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()
