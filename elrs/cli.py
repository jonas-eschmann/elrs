import argparse
import asyncio
from typing import Dict
from gamepad_mapper import load_or_map, read_gamepad
from elrs import ELRS
from datetime import datetime

PORT_DEFAULT = "/dev/ttyUSB0"
BAUD_DEFAULT = 921600

async def elrs_loop(joystick, port, baud, mapping, rate=50):
    elrs = ELRS(port, baud=baud, rate=rate)
    asyncio.create_task(elrs.start())

    def axis_to_channel(value: float) -> int:
        return max(0, min(2047, int((value + 1.0) * 1024)))

    while True:
        channels, buttons = read_gamepad(joystick, mapping)
        channels = list(map(axis_to_channel, channels.values()))
        for value in buttons.values():
            channels.append(2047 if value else 0)

        elrs.set_channels(channels)
        await asyncio.sleep(1 / rate)

async def async_main():
    p = argparse.ArgumentParser(description="Gamepad → ELRS bridge")
    p.add_argument("port", help="Serial port (e.g. COM3 or /dev/ttyACM0)")
    p.add_argument("baud", nargs="?", type=int, default=921600, help="Baud rate (default 921600)")
    p.add_argument("--rate", type=float, default=50.0, help="Transmit rate in Hz (default 50)")
    p.add_argument("--ch", type=int, nargs="+", help="Up to 16 raw channel values (0-2047). Missing → 1024")
    p.add_argument("--axes", type=str, nargs="+", default=["Roll", "Pitch", "Throttle", "Yaw"], help="Axes names in order. Default: ['Roll', 'Pitch', 'Throttle', 'Yaw'] (Betaflight default AETR)")
    p.add_argument("--buttons", type=str, nargs="+", default=["arm"], help="Button names to map to channels. Default: ['arm']")
    p.add_argument("--force", action="store_true", help="Force remapping of gamepad axes and buttons")

    args = p.parse_args()

    if args.ch is None:
        # gamepad mode
        import pygame

        pygame.init()
        pygame.joystick.init()
        assert pygame.joystick.get_count() > 0, "No game controller found."

        joystick = pygame.joystick.Joystick(0)
        joystick.init()

        mapping = load_or_map(joystick, args.axes, args.buttons, force=args.force, name="elrs")

        await elrs_loop(joystick, args.port, args.baud, mapping)
    else:
        def callback(ftype, decoded):
            ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print(f"[{ts}] {ftype:02X} {decoded}")

        elrs = ELRS(args.port, baud=args.baud, rate=args.rate, telemetry_callback=callback)

        elrs.set_channels(args.ch if args.ch else [1024] * 16)
        await elrs.start()

def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("Exiting...")


if __name__ == "__main__":
    main()

