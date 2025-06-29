#!/usr/bin/env python3
import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List

import pygame
from elrs import ELRS

PORT_DEFAULT = "/dev/ttyUSB0"
BAUD_DEFAULT = 921600
ELRS_RATE_HZ = 50
NUM_CHANNELS = 16
CAL_CHANNELS = 4          # how many axes we calibrate (0-3)

def config_dir() -> Path:
    """Return an OS-agnostic per-user config directory."""
    try:
        from platformdirs import user_config_dir  # type: ignore
        return Path(user_config_dir("elrs_gamepad"))
    except ModuleNotFoundError:
        return Path.home() / ".elrs_gamepad"


CFG_DIR = config_dir()
CFG_DIR.mkdir(parents=True, exist_ok=True)
MAPPING_FILE = CFG_DIR / "mapping.json"

def wait_for_axis_movement(joystick: pygame.joystick.Joystick,
                           baseline: List[float],
                           prompt: str,
                           thresh: float = 0.6,
                           used_axes: set[int] | None = None) -> Dict:
    if used_axes is None:
        used_axes = set()
    print(prompt)
    sys.stdout.flush()
    axis_count = joystick.get_numaxes()
    while True:
        pygame.event.pump()
        # Ignore axes we've already mapped
        diffs = [
            0.0 if i in used_axes else joystick.get_axis(i) - baseline[i]
            for i in range(axis_count)
        ]
        idx, delta = max(enumerate(diffs), key=lambda x: abs(x[1]))
        if abs(delta) >= thresh:
            inverted = (joystick.get_axis(idx) < baseline[idx])
            print(f"  Detected axis {idx} "
                  f"{'inverted' if inverted else 'normal'}")
            return {"index": idx, "inverted": inverted}


def wait_for_button_press(joystick: pygame.joystick.Joystick,
                          already_taken: set,
                          prompt: str) -> int:
    """Block until the user presses a button not in *already_taken*."""
    print(prompt)
    sys.stdout.flush()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                btn = event.button
                if btn not in already_taken:
                    print(f"  Detected button {btn}")
                    return btn


def calibrate(joystick: pygame.joystick.Joystick) -> Dict:
    axis_mapping: List[Dict] = []
    used_axes: set[int] = set()
    baseline = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]

    for ch in range(CAL_CHANNELS):
        cfg = wait_for_axis_movement(
            joystick,
            baseline,
            f"\nMove the control you want to be **channel {ch}** fully "
            "FORWARD / RIGHT (max positive) and hold…",
            used_axes=used_axes
        )
        axis_mapping.append(cfg)
        used_axes.add(cfg["index"])
        baseline = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]


    taken_buttons = set()
    button_a = wait_for_button_press(
        joystick,
        taken_buttons,
        "\nPress the first button you’d like to map (e.g. ARM)…",
    )
    taken_buttons.add(button_a)

    button_b = wait_for_button_press(
        joystick,
        taken_buttons,
        "Press the second button (e.g. MODE)…",
    )

    mapping = {
        "axes": axis_mapping,           # list of dicts with index & inverted
        "buttons": {"btn_a": button_a, "btn_b": button_b},
    }
    print("\nCalibration completed!\n")
    return mapping




def load_or_calibrate(joystick, force_calibration: bool) -> Dict:
    if not force_calibration and MAPPING_FILE.exists():
        try:
            with MAPPING_FILE.open() as fp:
                mapping = json.load(fp)
            print(f"Loaded mapping from {MAPPING_FILE}")
            return mapping
        except Exception as exc:
            print(f"Failed to read mapping: {exc!s}. Re-calibrating…")

    mapping = calibrate(joystick)
    with MAPPING_FILE.open("w") as fp:
        json.dump(mapping, fp, indent=2)
    print(f"Mapping saved to {MAPPING_FILE}")
    return mapping

async def elrs_loop(port: str, baud: int, mapping: Dict):
    elrs = ELRS(port, baud=baud, rate=ELRS_RATE_HZ)
    asyncio.create_task(elrs.start())

    axes_cfg = mapping["axes"]
    btn_cfg = mapping["buttons"]

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    inv_flags = [cfg["inverted"] for cfg in axes_cfg]
    axis_indices = [cfg["index"] for cfg in axes_cfg]

    def axis_to_channel(value: float) -> int:
        """Convert joystick float → ELRS channel int."""
        return max(0, min(2047, int((value + 1.0) * 1024)))

    while True:
        pygame.event.pump()

        channels = [1024] * NUM_CHANNELS
        # Map calibrated axes to channels 0-3
        for ch, idx in enumerate(axis_indices):
            raw = joystick.get_axis(idx)
            if inv_flags[ch]:
                raw = -raw
            channels[ch] = axis_to_channel(raw)

        # Example: send buttons to channels 4 & 5 as 0 / 2047
        channels[4] = 2047 if joystick.get_button(btn_cfg["btn_a"]) else 0
        channels[5] = 2047 if joystick.get_button(btn_cfg["btn_b"]) else 0

        elrs.set_channels(channels)
        await asyncio.sleep(1 / ELRS_RATE_HZ)


def parse_args():
    p = argparse.ArgumentParser(description="Gamepad → ELRS bridge")
    p.add_argument("--port", default=PORT_DEFAULT, help="Serial port")
    p.add_argument("--baud", type=int, default=BAUD_DEFAULT, help="Baud rate")
    p.add_argument("--calibrate", action="store_true",
                   help="Ignore stored mapping and run calibration")
    return p.parse_args()


async def main():
    args = parse_args()

    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        sys.exit("No game controller found.")

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    mapping = load_or_calibrate(joystick, args.calibrate)
    await elrs_loop(args.port, args.baud, mapping)


if __name__ == "__main__":
    asyncio.run(main())

