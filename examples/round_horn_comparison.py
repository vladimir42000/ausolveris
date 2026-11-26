"""Compare equal-length round horns. Run with PYTHONPATH=src."""
import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from ausolveris.geometry.round_horn import solve_round_horn


def profiles():
    z = np.linspace(0, 0.120, 17)
    return {"Conical": np.array([[0, 0.0127], [0.120, 0.060]]),
            "Exponential": np.column_stack((z, 0.0127*(0.060/0.0127)**(z/0.120)))}


def main():
    parser = argparse.ArgumentParser(description="Uniform throat velocity 1 m/s peak; microphones at 1 m")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--axial-cells", type=int, default=96)
    parser.add_argument("--radial-cells", type=int, default=16)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    angles = np.arange(0, 90, 2)
    theta = np.deg2rad(angles)
    points = np.column_stack((np.sin(theta), 0*theta, np.cos(theta)))
    fig, (polar, wall) = plt.subplots(1, 2, figsize=(10, 4))
    with (args.output_dir / "round_horns.csv").open("w", newline="") as out:
        rows = csv.writer(out)
        rows.writerow(["profile", "frequency_Hz", "throat_Z_real_Pa_s_m3", "throat_Z_imag_Pa_s_m3",
                       "angle_deg", "pressure_real_Pa_peak", "pressure_imag_Pa_peak", "SPL_dB_re_20uPa_RMS"])
        for name, profile in profiles().items():
            for f in (600, 1500, 3000, 6000):
                result = solve_round_horn(profile, f, axial_cells=args.axial_cells, radial_cells=args.radial_cells)
                p = result.exterior_pressure(points)
                spl = 20*np.log10(abs(p)/(np.sqrt(2)*20e-6))
                z = result.throat_impedance
                rows.writerows((name, f, z.real, z.imag, angle, value.real, value.imag, level)
                               for angle, value, level in zip(angles, p, spl))
                if f == 6000:
                    polar.plot(angles, spl-spl[0], label=name)
                    wall.plot(1000*result.axial_positions_m, abs(result.wall_pressure_pa), label=name)
    polar.set(xlabel="Angle from axis (degrees)", ylabel="Relative level (dB)", title="Directivity at 6 kHz")
    wall.set(xlabel="Distance from throat (mm)", ylabel="Peak pressure magnitude (Pa)", title="Wall pressure at 6 kHz")
    for ax in (polar, wall):
        ax.grid(alpha=0.3)
        ax.legend()
    fig.tight_layout()
    fig.savefig(args.output_dir / "round_horns.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
