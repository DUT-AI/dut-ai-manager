"""
UUID utilities supporting RFC 9562 UUIDv7.

UUIDv7 is a time-ordered UUID with 48-bit millisecond timestamp precision,
providing sequential insertion properties ideal for database B-tree indexes
while retaining the uniqueness and unpredictability of UUIDs.
"""

import os
import time
import uuid


def uuid7() -> uuid.UUID:
    """
    Generate an RFC 9562 compliant UUIDv7 (time-ordered).

    Structure:
    - 48 bits: Unix timestamp in milliseconds.
    - 4 bits: Version 7 (0b0111).
    - 12 bits: rand_a (pseudorandom).
    - 2 bits: Variant 2 (0b10, RFC 4122/9562).
    - 62 bits: rand_b (pseudorandom).
    """
    ns = time.time_ns()
    timestamp_ms = ns // 1_000_000
    time_high = timestamp_ms & 0xFFFFFFFFFFFF
    rand_bytes = os.urandom(10)
    rand_a = int.from_bytes(rand_bytes[:2], "big") & 0x0FFF
    rand_b = int.from_bytes(rand_bytes[2:], "big") & 0x3FFFFFFFFFFFFFFF

    uuid_int = (time_high << 80) | (0x7 << 76) | (rand_a << 64) | (0x2 << 62) | rand_b
    return uuid.UUID(int=uuid_int)
