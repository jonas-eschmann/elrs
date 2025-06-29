from typing import List
from .crc import crc8

SYNC_ADDR = 0xC8                       # also Flight-Controller address
FT_RC       = 0x16                     # RC_CHANNELS_PACKED
RC_PAYLOAD_LEN = 22                    # 16 × 11-bit
RC_FRAME_SIZE  = 1 + RC_PAYLOAD_LEN + 1


def _pack_channels(ch: List[int]) -> bytes:
    if len(ch) != 16:
        raise ValueError("Exactly 16 channels required")
    ch = [max(0, min(0x7FF, int(v))) for v in ch]

    buf = bytearray(RC_PAYLOAD_LEN)
    for i, v in enumerate(ch):
        byte_idx = (i * 11) // 8
        bit_off  = (i * 11) % 8

        buf[byte_idx]     |= (v << bit_off) & 0xFF
        buf[byte_idx + 1] |= (v >> (8 - bit_off)) & 0xFF
        if bit_off > 5:
            buf[byte_idx + 2] |= (v >> (16 - bit_off)) & 0xFF
    return bytes(buf)


def build_rc_frame(channels: List[int]) -> bytes:
    payload = _pack_channels(channels)
    crc     = crc8(bytes([FT_RC]) + payload)
    return bytes([SYNC_ADDR, RC_FRAME_SIZE, FT_RC]) + payload + bytes([crc])