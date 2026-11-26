"""Compare complex 1 V pressure on both principal cuts at a 1 m radius."""
import argparse
import csv
import sys

import numpy as np
from os_lem.model import Driver

from ausolveris.geometry.driven_round_horn import solve_driven_rectangular_horn


def fixture(angle_step=5):
    throat, mouth = (.025, .020), (.120, .060)
    driver = Driver("illustrative", 6., .0001, 4., .002, .0003, 1.,
                    np.prod(throat), "front", "rear", 1.)
    theta = np.deg2rad(np.arange(0, 86, angle_step))
    s, c = np.sin(theta), np.cos(theta)
    zero = np.zeros_like(s)
    points = np.vstack((np.column_stack((s, zero, c)), np.column_stack((zero, s, c))))
    return throat, mouth, driver, points


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--directional", action="store_true",
                        help="compare axial and transverse refinements at 30 kHz")
    modes.add_argument("--cross-section", action="store_true",
                       help="vary width and height separately with 128 axial elements at 30 kHz")
    parser.add_argument("--axial-order", type=int, choices=(1, 2), default=1)
    parser.add_argument('--angle-step', type=int, choices=(1, 5), default=5,
                        help='sample the same 0 to 85 degree arc in each plane')
    args = parser.parse_args()
    throat, mouth, driver, points = fixture(args.angle_step)
    writer = csv.writer(sys.stdout)
    if args.cross_section:
        pairs = []
        for coarse, fine in [((24, 12, 128), (32, 16, 128)), ((32, 16, 128), (40, 20, 128))]:
            width = (fine[0], coarse[1], coarse[2])
            height = (coarse[0], fine[1], coarse[2])
            pairs.extend([(coarse, width, "width"), (coarse, height, "height"),
                          (height, fine, "width"), (width, fine, "height"),
                          (coarse, fine, "combined")])
        pairs.append(((40, 20, 128), (40, 24, 128), "height"))
        compare_pairs(writer, throat, mouth, driver, points, args.axial_order, pairs)
        return
    if args.directional:
        directional_study(writer, throat, mouth, driver, points, args.axial_order)
        return
    writer.writerow(["Hz", "quarter_nx", "quarter_ny", "nz", "axis_dB_SPL",
                     "horizontal_complex_change_pct", "vertical_complex_change_pct"])
    for hz in (1000, 3000, 6000, 12000, 30000):
        previous = None
        for grid in ((4, 2, 24), (6, 3, 36), (8, 4, 48), (12, 6, 72), (16, 8, 96)):
            r = solve_driven_rectangular_horn(throat, mouth, .12, hz, driver, cells=grid,
                                             axial_order=args.axial_order)
            p = r.exterior_pressure_rms(points).reshape(2, -1)
            changes = ["", ""] if previous is None else (
                100*np.linalg.norm(p-previous, axis=1)/np.linalg.norm(p, axis=1))
            writer.writerow([hz, *grid, 20*np.log10(abs(p[0, 0])/20e-6), *changes])
            previous = p


def directional_study(writer, throat, mouth, driver, points, axial_order):
    """Reuse each field across comparisons with explicitly named reference grids."""
    levels = [(12, 6, 72), (16, 8, 96), (24, 12, 144), (32, 16, 192)]
    if axial_order == 2:
        levels = [(12, 6, 48), (16, 8, 64), (20, 10, 80), (24, 12, 96)]
    pairs = []
    for coarse, fine in zip(levels, levels[1:]):
        axial = (*coarse[:2], fine[2])
        transverse = (*fine[:2], coarse[2])
        pairs.extend([(coarse, axial, "axial"), (coarse, transverse, "transverse"),
                      (transverse, fine, "axial"), (axial, fine, "transverse"),
                      (coarse, fine, "combined")])
    if axial_order == 2:
        pairs.insert(0, ((12, 6, 36), levels[0], "axial"))
        pairs.append((levels[-1], (32, 16, 128), "combined"))
    compare_pairs(writer, throat, mouth, driver, points, axial_order, pairs)


def compare_pairs(writer, throat, mouth, driver, points, axial_order, pairs):
    fields = {}
    writer.writerow(["from_grid", "to_grid", "refinement", "axis_dB_SPL",
                     "horizontal_complex_change_pct", "vertical_complex_change_pct",
                     "horizontal_normalized_magnitude_change_pct",
                     "vertical_normalized_magnitude_change_pct"])
    for src, dst, label in pairs:
        for grid in (src, dst):
            if grid not in fields:
                result = solve_driven_rectangular_horn(throat, mouth, .12, 30000, driver,
                                                       cells=grid, axial_order=axial_order, layered=True)
                fields[grid] = result.exterior_pressure_rms(points).reshape(2, -1)
        p, prev = fields[dst], fields[src]
        delta = 100*np.linalg.norm(p-prev, axis=1)/np.linalg.norm(p, axis=1)
        mag = abs(p/p[:, :1])
        prev_mag = abs(prev/prev[:, :1])
        pattern_delta = 100*np.linalg.norm(mag-prev_mag, axis=1)/np.linalg.norm(mag, axis=1)
        writer.writerow(["x".join(map(str, src)), "x".join(map(str, dst)), label,
                         20*np.log10(abs(p[0, 0])/20e-6), *delta, *pattern_delta])


if __name__ == "__main__":
    main()
