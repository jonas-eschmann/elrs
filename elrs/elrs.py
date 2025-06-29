import sys
import time
from collections import deque
from typing import Deque
from .rc import build_rc_frame
from .telemetry import frames_from_bytes, _DECODERS
import serial

# Standard CRSF channel values (100% endpoints)
# Centered at 992, with a range of +/- 819.
# The 11-bit value sent is from 0 to 2047.
# 992 is the "zero" or center-stick value.
# 172 is the -100% value.
# 1811 is the +100% value.
RC_CHANNEL_MIN = 172
RC_CHANNEL_MID = 992
RC_CHANNEL_MAX = 1811



import asyncio

class ELRS:
    def __init__(self, port: str, baud: int = 921600, rate: float = 50.0, telemetry_callback=None):
        self.NUM_CHANNELS = 16
        self.port = port
        self.baud = baud
        self.rate = rate
        self._running = False
        self.set_channels([])
        self.telemetry_callback = telemetry_callback
    
    def set_channels(self, input_channels: list[int]) -> bytes:
        input_channels = input_channels[:self.NUM_CHANNELS]
        channels = [RC_CHANNEL_MID] * self.NUM_CHANNELS
        channels[:len(input_channels)] = [int(v) for v in input_channels]
        self.rc_frame = build_rc_frame(channels)

    async def _run(self):
        period   = 1.0 / self.rate

        ring: Deque[int] = deque(maxlen=512)   # crude RX buffer

        try:
            with serial.Serial(self.port, self.baud, timeout=0) as ser:
                print(f"Opened {ser.port} @ {ser.baudrate} baud")
                next_tx = time.perf_counter()

                while self._running:
                    now = time.perf_counter()
                    if now >= next_tx:
                        ser.write(self.rc_frame)
                        ser.write(self.rc_frame)     # duplicate like ExpressLRS
                        next_tx += period

                    data = ser.read(ser.in_waiting or 1)
                    ring.extend(data)

                    for addr, ftype, payload in frames_from_bytes(ring):
                        if ftype in _DECODERS:
                            self.telemetry_callback(ftype, _DECODERS[ftype](payload)) if self.telemetry_callback else None
                        else:
                            print(f"Unknown Frame Type 0x{ftype:02X} (len={len(payload)}) from 0x{addr:02X}")
                    await asyncio.sleep(period)

        except serial.SerialException as e:
            print(f"Serial error: {e}", file=sys.stderr)
            self._running = False

    async def start(self):
        if not self._running:
            self._running = True
            await self._run()

    def stop(self):
        self._running = False


