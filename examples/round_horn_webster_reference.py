"""Low-frequency comparison with Webster's equation and a baffled piston."""
import csv
import sys

import numpy as np
from scipy.integrate import solve_ivp
from scipy.special import j1, struve

from ausolveris.geometry.round_horn import solve_round_horn


def webster_reference(profile, hz, distance):
    """Throat impedance and axial pressure for unit throat velocity."""
    (z0, throat), (z1, mouth) = profile
    rho, c = 1.21, 343.
    omega = 2*np.pi*hz
    k = omega/c
    ka = k*mouth
    # Start with 1 m/s at the mouth. State variables are pressure and volume flow.
    pressure = rho*c*(1 - j1(2*ka)/ka - 1j*struve(1, 2*ka)/ka)
    flow = np.pi*mouth**2

    def derivative(z, state):
        p, q = state
        radius = throat + (mouth-throat)*(z-z0)/(z1-z0)
        area = np.pi*radius**2
        return [1j*omega*rho*q/area, 1j*omega*area*p/(rho*c**2)]

    sol = solve_ivp(derivative, (z1, z0), [pressure, flow], rtol=1e-10, atol=1e-13)
    if not sol.success:
        raise RuntimeError(sol.message)
    p_in, q_in = sol.y[:, -1]
    mouth_velocity = np.pi*throat**2/q_in
    path_difference = mouth**2/(np.hypot(distance, mouth) + distance)
    axial_pressure = -rho*c*mouth_velocity*np.exp(1j*k*distance)*np.expm1(1j*k*path_difference)
    return p_in/q_in, axial_pressure


def main():
    writer = csv.writer(sys.stdout)
    writer.writerow(["Hz", "axial_cells", "radial_cells", "Z_complex_error_pct",
                     "axial_pressure_delta_dB", "axial_phase_delta_deg"])
    profile = [(0., .0127), (.12, .060)]
    for hz in (140, 204, 296, 360):
        z_ref, p_ref = webster_reference(profile, hz, 1.)
        for nz, nr in [(48, 8), (96, 16)]:
            horn = solve_round_horn(profile, hz, axial_cells=nz, radial_cells=nr)
            ratio = horn.exterior_pressure([[0, 0, 1]])[0]/p_ref
            writer.writerow([hz, nz, nr, 100*abs(horn.throat_impedance/z_ref - 1),
                             20*np.log10(abs(ratio)), np.angle(ratio, deg=True)])


if __name__ == "__main__":
    main()
