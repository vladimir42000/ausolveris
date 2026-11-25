"""Compare complex 1 V pressure on both principal cuts at a 1 m radius."""
import csv
import sys

import numpy as np
from os_lem.model import Driver

from ausolveris.geometry.driven_round_horn import solve_driven_rectangular_horn


def main():
    throat, mouth = (.025, .020), (.120, .060)
    driver = Driver("illustrative", 6., .0001, 4., .002, .0003, 1.,
                    np.prod(throat), "front", "rear", 1.)
    theta = np.deg2rad(np.arange(0, 90, 5))
    s, c = np.sin(theta), np.cos(theta)
    zero = np.zeros_like(s)
    points = np.vstack((np.column_stack((s, zero, c)), np.column_stack((zero, s, c))))
    writer = csv.writer(sys.stdout)
    writer.writerow(["Hz", "quarter_nx", "quarter_ny", "nz", "axis_dB_SPL",
                     "horizontal_complex_change_pct", "vertical_complex_change_pct"])
    for hz in (1000, 3000, 6000, 12000, 30000):
        previous = None
        for grid in ((4, 2, 24), (6, 3, 36), (8, 4, 48), (12, 6, 72), (16, 8, 96)):
            r = solve_driven_rectangular_horn(throat, mouth, .12, hz, driver, cells=grid)
            p = r.exterior_pressure_rms(points).reshape(2, -1)
            changes = ["", ""] if previous is None else (
                100*np.linalg.norm(p-previous, axis=1)/np.linalg.norm(p, axis=1))
            writer.writerow([hz, *grid, 20*np.log10(abs(p[0, 0])/20e-6), *changes])
            previous = p


if __name__ == "__main__":
    main()
