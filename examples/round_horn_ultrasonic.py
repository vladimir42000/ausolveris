"""Compare mesh resolutions for the prescribed-velocity 30 kHz conical horn."""
import csv
import sys

import numpy as np

from ausolveris.geometry.round_horn import solve_round_horn


def main():
    angles = np.arange(0, 90, 2)
    theta = np.deg2rad(angles)
    points = np.column_stack((np.sin(theta), np.zeros_like(theta), np.cos(theta)))
    writer = csv.writer(sys.stdout)
    writer.writerow(["axial_cells", "radial_cells", "angle_deg", "zin_real_Pa_s_m3",
                     "zin_imag_Pa_s_m3", "pressure_real_Pa_peak", "pressure_imag_Pa_peak"])
    for axial, radial in [(192, 32), (384, 64), (576, 96), (768, 128)]:
        result = solve_round_horn([[0, .0127], [.12, .060]], 30000,
                                  axial_cells=axial, radial_cells=radial)
        impedance = result.throat_impedance
        for angle, pressure in zip(angles, result.exterior_pressure(points)):
            writer.writerow([axial, radial, angle, impedance.real, impedance.imag,
                             pressure.real, pressure.imag])


if __name__ == "__main__":
    main()
