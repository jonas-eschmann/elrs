import struct
from typing import Deque
from .crc import crc8

ADDRS_START = {0xC8, 0xEA, 0xEE}       # FC, RadioTX, CRSF TX
FT_LINKSTAT = 0x14                     # Link statistics
FT_BATTERY  = 0x08                     # Battery sensor
FT_GPS      = 0x02                     # GPS, etc. (example only)

def _parse_linkstats(payload: bytes) -> str:
    if len(payload) != 10:
        return f"LinkStats invalid length {len(payload)}"
    (rssi1_inv, rssi2_inv, lq_up, snr_up, ant, rf_mode,
     txpwr, rssi_d_inv, lq_dn, snr_dn) = struct.unpack('<BBBBBBBbbb', payload)
    return (f"LinkStat:  RSSI1={-rssi1_inv}dBm  RSSI2={-rssi2_inv}dBm  "
            f"LQ={lq_up}%  SNR={snr_up}dB  RFmode={rf_mode}  TxPwrIdx={txpwr}  "
            f"DownRSSI={-rssi_d_inv}dBm  DownLQ={lq_dn}%  DownSNR={snr_dn}dB")


def _parse_battery(payload: bytes) -> str:
    """
    Battery-sensor frame (type 0x08)

    Layout in C++:
        u16 voltage   // big-endian  (mV * 100)
        u16 current   // big-endian  (mA * 100)
        u32 capacity  // little-endian:
                      #   lower 24 bits  = capacity [mAh]
                      #   upper  8 bits  = remaining [%]
    """
    if len(payload) != 8:
        return f"Battery invalid length {len(payload)}"

    voltage_raw, current_raw = struct.unpack(">HH", payload[:4])   # big-endian
    cap_pack,                 = struct.unpack("<I", payload[4:])   # little-endian

    voltage  = voltage_raw  / 10.0            # volts
    current  = current_raw  / 100.0           # amps
    capacity = (cap_pack & 0xFFFFFF) / 1000.0 # amp-hours
    remain   = cap_pack >> 24                 # percent

    return (f"Battery:  {voltage:.2f} V  {current:.2f} A  "
            f"{capacity:.2f} Ah  {remain}%")

# Map frame-type → decoder
_DECODERS = {
    FT_LINKSTAT: _parse_linkstats,
    FT_BATTERY : _parse_battery,
}


def frames_from_bytes(buf: Deque[int]):
    """
    In-place parser – consumes bytes from *buf* and yields complete frames.
    """
    while True:
        # Need at least addr + size + type
        if len(buf) < 3:
            return

        # Sync: discard bytes until a plausible address shows up
        if buf[0] not in ADDRS_START:
            buf.popleft()
            continue

        if len(buf) < 2:
            return
        size = buf[1]
        frame_total = size + 2
        if len(buf) < frame_total:
            return

        # Validate CRC
        crc_in  = buf[frame_total - 1]
        calc_crc = crc8(bytes(list(buf)[2:frame_total - 1]))
        if crc_in != calc_crc:
            # bad frame – skip first byte and resync
            buf.popleft()
            continue

        # All good – extract
        addr   = buf.popleft()
        size   = buf.popleft()          # discard, we know it
        ftype  = buf.popleft()
        payload = bytes(buf.popleft() for _ in range(frame_total - 3 - 1))
        buf.popleft()  # remove CRC byte
        yield addr, ftype, payload