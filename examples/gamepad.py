import asyncio
import pygame
from elrs import ELRS

PORT = "/dev/ttyUSB0"
BAUD = 921600

async def main() -> None:
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        raise RuntimeError("No game controller found.")

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    elrs = ELRS(PORT, baud=BAUD, rate=50)
    asyncio.create_task(elrs.start())

    while True:
        pygame.event.pump()
        axes = [joystick.get_axis(i) for i in range(min(16, joystick.get_numaxes()))]

        # Map axis float [-1.0, 1.0] to ELRS channel int [0, 2047]
        channels = [int((a + 1.0) * 1024) for a in axes]
        channels += [1024] * (16 - len(channels))  # Pad to 16 channels

        elrs.set_channels(channels)
        await asyncio.sleep(0.02)  # 50Hz

if __name__ == "__main__":
    asyncio.run(main())
