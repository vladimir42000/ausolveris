"""Mesh a closed air-volume STL once and sweep a voltage-driven horn."""
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from os_lem.model import Driver

from ausolveris.geometry.cad_mesh import mesh_air_stl
from ausolveris.geometry.cad_horn import prepare_cad_horn
from ausolveris.geometry.chamber_driver import drive_chamber_horn


def read_driver(path, voltage):
    data = json.loads(path.read_text())
    driver = Driver(id=data["id"], Re=data["Re_ohm"], Le=data["Le_mH"]*1e-3,
                    Bl=data["Bl_T_m"], Mms=data["Mms_g"]*1e-3,
                    Cms=data["Cms_mm_per_N"]*1e-3, Rms=data["Rms_N_s_per_m"],
                    Sd=data["Sd_cm2"]*1e-4, node_front="front", node_rear="rear",
                    source_voltage_rms=voltage)
    rear = data["rear_volume_litre"]
    return driver, data["front_volume_cm3"]*1e-6, None if rear is None else rear*1e-3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("air_stl", type=Path)
    parser.add_argument("driver_json", type=Path)
    parser.add_argument("--units", choices=("mm", "m"), required=True)
    parser.add_argument("--cell-mm", type=float, required=True, help="target tetrahedral mesh size")
    parser.add_argument("--hz", type=float, nargs="+", required=True)
    parser.add_argument("--voltage-rms", type=float, default=1.0)
    parser.add_argument("--distance-m", type=float, default=1., help="on-axis distance from mouth")
    args = parser.parse_args()
    if not np.all(np.isfinite(args.hz)) or min(args.hz) <= 0:
        parser.error("frequencies must be positive and finite")
    if not np.isfinite(args.distance_m) or args.distance_m <= 0:
        parser.error("distance must be positive and finite")
    driver, front, rear = read_driver(args.driver_json, args.voltage_rms)
    mesh = mesh_air_stl(args.air_stl, units=args.units, cell_size_m=args.cell_mm*1e-3)
    points, tetra, inlet, outlet = mesh
    print(f"{len(points)} points, {len(tetra)} tetrahedra, {len(inlet)} throat and "
          f"{len(outlet)} mouth triangles", file=sys.stderr)
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["Hz", "voltage_V_rms", "distance_m", "throat_m2", "mouth_m2", "mouth_ka",
                     "Ze_real_ohm", "Ze_imag_ohm", "diaphragm_v_abs_m_s_rms",
                     "throat_v_abs_m_s_rms", "p_real_Pa_rms", "p_imag_Pa_rms", "SPL_dB"])
    prepared = prepare_cad_horn(*mesh)
    for hz in args.hz:
        horn = prepared.solve(hz)
        result = drive_chamber_horn(horn, hz, driver, throat_area_m2=horn.inlet_area_m2,
                                    front_volume_m3=front, rear_volume_m3=rear)
        p = result.exterior_pressure_rms([[0, 0, args.distance_m]])[0]
        z = result.electrical_impedance
        ka = 2*np.pi*hz*np.sqrt(horn.outlet_area_m2/np.pi)/horn.sound_speed
        writer.writerow([hz, args.voltage_rms, args.distance_m, horn.inlet_area_m2,
                         horn.outlet_area_m2, ka, z.real, z.imag,
                         abs(result.diaphragm_velocity_rms), abs(result.throat_velocity_rms),
                         p.real, p.imag, 20*np.log10(abs(p)/20e-6)])


if __name__ == "__main__":
    main()
