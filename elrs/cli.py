import argparse 
import asyncio
from .elrs import ELRS
from datetime import datetime

def main() -> None:
    p = argparse.ArgumentParser(description="Minimal CRSF TX + Telemetry RX")
    p.add_argument("port", help="Serial port (e.g. COM3 or /dev/ttyACM0)")
    p.add_argument("baud", nargs="?", type=int, default=921600,
                   help="Baud rate (default 921600)")
    p.add_argument("--ch", type=int, nargs="+",
                   help="Up to 16 raw channel values (0-2047). Missing → 1024")
    p.add_argument("--rate", type=float, default=50.0,
                   help="Transmit rate in Hz (default 50)")
    args = p.parse_args()


    def callback(ftype, decoded):
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{ts}] {ftype:02X} {decoded}")

    elrs = ELRS(args.port, baud=args.baud, rate=args.rate, telemetry_callback=callback)

    elrs.set_channels(args.ch if args.ch else [1024] * 16)
    asyncio.run(elrs.start())

if __name__ == "__main__":
    main()
