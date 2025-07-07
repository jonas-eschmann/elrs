# ELRS Python Interface

```python
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

    value = 1000
    while True:
        channels = [value] * 16
        elrs.set_channels(channels)
        value = (value + 1) % 2048
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())
```

Tested with the Radiomaster Ranger Nano.
### Radiomaster Ranger Nano
- Connect to the Wifi hosted by the Ranger Nano and go to `http://10.0.0.1/hardware.html` and set `RX: 3` `TX: 1`
- After it is configured make sure that after power cycling it, you send commands to it within a certain time. It seems to go into the Wifi-hosting configuration mode some time after powerup if it does not receive commands.
