"""Compatibility constants for the 0G Python storage SDK.

Some PyPI builds of ``0g-storage-sdk`` import these constants from a top-level
``config`` module. Keeping this shim in the Django backend lets the SDK resolve
those imports when the backend directory is on ``sys.path``.
"""

DEFAULT_CHUNK_SIZE = 256
DEFAULT_SEGMENT_MAX_CHUNKS = 1024
DEFAULT_SEGMENT_SIZE = DEFAULT_CHUNK_SIZE * DEFAULT_SEGMENT_MAX_CHUNKS
DEFAULT_BATCH_SIZE = 10

ZERO_HASH = "0x" + ("00" * 32)

try:
    from Crypto.Hash import keccak

    _hash = keccak.new(digest_bits=256)
    _hash.update(bytes(DEFAULT_CHUNK_SIZE))
    EMPTY_CHUNK_HASH = "0x" + _hash.hexdigest()
except Exception:
    # The SDK depends on pycryptodome, so this should not happen after install.
    # This value is only a final fallback to keep imports readable.
    EMPTY_CHUNK_HASH = ZERO_HASH
