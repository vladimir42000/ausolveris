"""Export horizontal and vertical 1 m polar cuts for a 120 × 60 mm aperture."""
import csv
import sys

import numpy as np

from ausolveris.geometry.rectangular_piston import rectangular_piston_pressure


def main():
    writer = csv.writer(sys.stdout)
    writer.writerow(["Hz", "plane", "angle_deg", "p_real_Pa_peak", "p_imag_Pa_peak",
                     "level_relative_to_axis_dB"])
    angles = np.arange(90)
    sine = np.sin(np.deg2rad(angles))
    zero = np.zeros_like(sine)
    for hz in (1000, 6000, 30000):
        for plane, x, y in [("horizontal", sine, zero), ("vertical", zero, sine)]:
            points = np.column_stack((x, y, np.cos(np.deg2rad(angles))))
            pressure = rectangular_piston_pressure(.12, .06, hz, 1., points)
            for angle, p in zip(angles, pressure):
                writer.writerow([hz, plane, angle, p.real, p.imag, 20*np.log10(abs(p/pressure[0]))])


if __name__ == "__main__":
    main()
