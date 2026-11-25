"""Compare 1 V RMS impedance around resonance, with a released or sealed rear."""
import csv
import sys

import numpy as np
from os_lem.model import Driver

from ausolveris.geometry.driven_round_horn import solve_driven_round_horn


def main():
    radius = 0.0127
    profile = [(0.0, radius), (0.12, 0.060)]
    driver = Driver("illustrative", 6., .0001, 4., .002, .0003, 1.,
                    np.pi * radius**2, "front", "rear", 1.)
    writer = csv.writer(sys.stdout)
    writer.writerow(["Hz", "rear", "Ze_real_ohm", "Ze_imag_ohm", "Ze_mag_ohm"])
    for hz in range(140, 361):
        for label, volume in [("released", None), ("sealed_10_cm3", 10e-6)]:
            result = solve_driven_round_horn(profile, hz, driver, rear_volume_m3=volume)
            z = result.electrical_impedance
            writer.writerow([hz, label, z.real, z.imag, abs(z)])


if __name__ == "__main__":
    main()
