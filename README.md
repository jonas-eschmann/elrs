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
j after it is configured make sure that after power cycling it, you send commands to it within a certain time. it seems to go into the wifi-hosting configuration mode some time after powerup if it does not receive commands.

### ELRS forwarding

Use e.g. Radiomaster Ranger Micro. (This is tested with `3.5.5`, flash using the ExpressLRS Configurator):
1. Connect to the WiFi hosted by it
2. Go to 10.0.0.1
3. Set the passphrase to match the one on your desired model
4. Set the same passphrase in betaflight by copying the 6 numbers from the site: `set expresslrs_uid = {6 numbers}` then `save` (both in the CLI)
5. Go to 10.0.0.1/hardware.html
6. Disable the Backpack
7. Set `CSRF.RX=3` and `CSRF.TX=1` (this works for both Radiomaster Ranger Micro and Jumper Aion ELRS 2.4G TX Nano and is reported to work for other modules like the BetaFPV ones as well)
8. After it is configured make sure that after power cycling it, you send commands to it within a certain time. it seems to go into the wifi-hosting configuration mode some time after powerup if it does not receive commands.
9. run `elrs /dev/ttyUSB0 921600 --ch 1337` (replace path with the assigned port on you PC). This should send a `1337` value to the receiver. Note that this is sent in these ranges
```
RC_CHANNEL_MIN = 172
RC_CHANNEL_MID = 992
RC_CHANNEL_MAX = 1811
```
and should be normalized to 1000 - 2000 in betaflight

