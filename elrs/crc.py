from typing import List

POLY = 0xD5

def _make_table(poly: int) -> List[int]:
    tbl = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = ((c << 1) ^ poly) & 0xFF if (c & 0x80) else (c << 1) & 0xFF
        tbl.append(c)
    return tbl


_CRC_TBL = _make_table(POLY)

def crc8(data: bytes) -> int:
    crc = 0
    for b in data:
        crc = _CRC_TBL[crc ^ b]
    return crc