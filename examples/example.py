import asyncio
from elrs import ELRS
from datetime import datetime

PORT = "/dev/ttyUSB0"
BAUD = 921600

async def main() -> None:

    def callback(ftype, decoded):
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{ts}] {ftype:02X} {decoded}")

    elrs = ELRS(PORT, baud=BAUD, rate=50, telemetry_callback=callback)

    asyncio.create_task(elrs.start())

    value = 0
    while True:
        channels = [value] * 16
        elrs.set_channels(channels)
        value = (value + 10) % 2048
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())