"""Generate a baffled piston pressure and directivity sweep, e.g.
PYTHONPATH=src python examples/baffled_piston_polar.py --output-dir piston-results
"""
import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from ausolveris.geometry.baffled_piston import baffled_piston_pressure


def main():
    parser = argparse.ArgumentParser(description="25.4 mm diameter piston at 1 m, 1 m/s peak")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    angles = np.arange(0, 90)
    theta = np.deg2rad(angles)
    points = np.column_stack((np.sin(theta), np.zeros_like(theta), np.cos(theta)))
    fig, ax = plt.subplots()
    with (args.output_dir / "piston_polar.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["frequency_Hz", "angle_deg", "peak_pressure_real_Pa",
                         "peak_pressure_imag_Pa", "SPL_dB_re_20uPa_RMS", "relative_level_dB"])
        for frequency in (1000, 10000, 30000):
            p = baffled_piston_pressure(0.0127, frequency, 1, points)
            levels = 20 * np.log10(np.abs(p) / (np.sqrt(2) * 20e-6))
            relative = levels - levels[0]
            writer.writerows(zip([frequency] * len(p), angles, p.real, p.imag, levels, relative))
            ax.plot(angles, relative, label=f"{frequency / 1000:g} kHz")
    ax.set(xlabel="Angle from piston axis (degrees)", ylabel="Level relative to on-axis (dB)",
           title="25.4 mm piston in an infinite rigid baffle, 1 m")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.output_dir / "piston_directivity.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
