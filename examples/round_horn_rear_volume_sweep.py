"""Compare 1 V RMS impedance around resonance, with a released or sealed rear."""
import argparse
import csv
import sys

import numpy as np
from os_lem.model import Driver

from ausolveris.geometry.driven_round_horn import solve_driven_round_horn


def webster_drive(driver, hz, volume, throat_impedance):
    omega = 2*np.pi*hz
    stiffness = 1/driver.Cms
    if volume is not None:
        stiffness += 1.21*343.**2*driver.Sd**2/volume
    mechanical = driver.Rms + 1j*(stiffness/omega - omega*driver.Mms)
    load = mechanical + driver.Sd**2*throat_impedance
    impedance = driver.Re - 1j*omega*driver.Le + driver.Bl**2/load
    velocity = driver.Bl*driver.source_voltage_rms/(impedance*load)
    return impedance, velocity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compare-webster", action="store_true",
                        help="include the independent 1D motor and horn comparison")
    compare = parser.parse_args().compare_webster
    if compare:
        from round_horn_webster_reference import webster_reference
    radius = 0.0127
    profile = [(0.0, radius), (0.12, 0.060)]
    driver = Driver("illustrative", 6., .0001, 4., .002, .0003, 1.,
                    np.pi * radius**2, "front", "rear", 1.)
    writer = csv.writer(sys.stdout)
    columns = ["Hz", "rear", "Ze_real_ohm", "Ze_imag_ohm", "Ze_mag_ohm"]
    if compare:
        columns += ["Webster_Ze_mag_ohm", "Ze_complex_diff_pct", "v_complex_diff_pct",
                    "FEM_v_rms_m_s", "Webster_v_rms_m_s", "FEM_SPL_dB", "Webster_SPL_dB"]
    writer.writerow(columns)
    for hz in range(140, 361):
        if compare:
            throat_z, unit_pressure = webster_reference(profile, hz, 1.)
        for label, volume in [("released", None), ("sealed_10_cm3", 10e-6)]:
            result = solve_driven_round_horn(profile, hz, driver, rear_volume_m3=volume)
            z = result.electrical_impedance
            row = [hz, label, z.real, z.imag, abs(z)]
            if compare:
                ref_z, ref_v = webster_drive(driver, hz, volume, throat_z)
                velocity = result.throat_velocity_rms
                pressure = result.exterior_pressure_rms([[0., 0., 1.]])[0]
                row += [abs(ref_z), 100*abs(z/ref_z - 1), 100*abs(velocity/ref_v - 1),
                        abs(velocity), abs(ref_v), 20*np.log10(abs(pressure)/20e-6),
                        20*np.log10(abs(unit_pressure*ref_v)/20e-6)]
            writer.writerow(row)


if __name__ == "__main__":
    main()
