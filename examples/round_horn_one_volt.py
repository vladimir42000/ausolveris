"""CSV for an illustrative area-matched motor at 1 V RMS."""
import csv
import sys

import numpy as np
from os_lem.model import Driver

from ausolveris.geometry.driven_round_horn import solve_driven_round_horn


def main():
    radius = .0127
    driver = Driver(id="illustrative", Re=6., Le=.0001, Bl=4., Mms=.002,
                    Cms=.0003, Rms=1., Sd=np.pi*radius**2, node_front="front",
                    node_rear="rear", source_voltage_rms=1.)
    profile = [(0., radius), (.12, .060)]
    angles = np.arange(0, 90, 2)
    theta = np.deg2rad(angles)
    points = np.column_stack((np.sin(theta), np.zeros_like(theta), np.cos(theta)))
    writer = csv.writer(sys.stdout)
    writer.writerow(["Hz", "angle_deg", "Ze_real_ohm", "Ze_imag_ohm",
                     "v_real_m_s_rms", "v_imag_m_s_rms", "p_real_Pa_rms",
                     "p_imag_Pa_rms", "SPL_dB_re_20uPa"])
    for hz, nz, nr in [(1000, 96, 16), (6000, 192, 32), (30000, 768, 128)]:
        result = solve_driven_round_horn(profile, hz, driver, axial_cells=nz, radial_cells=nr)
        z, v = result.electrical_impedance, result.throat_velocity_rms
        for angle, p in zip(angles, result.exterior_pressure_rms(points)):
            writer.writerow([hz, angle, z.real, z.imag, v.real, v.imag,
                             p.real, p.imag, 20*np.log10(abs(p)/20e-6)])


if __name__ == "__main__":
    main()
