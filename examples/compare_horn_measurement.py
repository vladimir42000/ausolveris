"""Compare a CAD horn sweep with measured impedance and on-axis SPL.

Both CSVs need Hz, Ze_real_ohm, Ze_imag_ohm, SPL_dB, voltage_V_rms and
distance_m. Use the same constant RMS voltage and mouth-to-microphone distance.
CAD impedance uses exp(-iωt). Choose positive-time for measurements using
exp(+iωt) (positive inductive reactance) to conjugate them into CAD convention.

Residuals are CAD minus measured, at measured frequencies within the CAD range.
Interpolate CAD real impedance, imaginary impedance and SPL in dB linearly in Hz.
Stdout contains residual CSV; stderr reports unweighted RMS and maximum absolute
residuals. Absolute SPL assumes matching microphone calibration and dB re 20 µPa.
"""
import argparse
import csv
import sys

import numpy as np


FIELDS = ("Hz", "Ze_real_ohm", "Ze_imag_ohm", "SPL_dB", "voltage_V_rms", "distance_m")


def read_sweep(path, label):
    rows = []
    seen = set()
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream, strict=True)
        headers = reader.fieldnames or []
        for field in FIELDS:
            if field not in headers:
                raise ValueError(f"{label}: missing column {field}")
            if headers.count(field) > 1:
                raise ValueError(f"{label}: duplicate column {field}")
        for row in reader:
            values = []
            for field in FIELDS:
                try:
                    value = float(row[field])
                except (ValueError, TypeError):
                    raise ValueError(f"{label} line {reader.line_num}: invalid {field}") from None
                if not np.isfinite(value):
                    raise ValueError(f"{label} line {reader.line_num}: nonfinite {field}")
                if field in ("Hz", "voltage_V_rms", "distance_m") and value <= 0:
                    raise ValueError(f"{label} line {reader.line_num}: {field} must be positive")
                values.append(value)
            if values[0] in seen:
                raise ValueError(f"{label}: duplicate frequency {values[0]:g} Hz")
            seen.add(values[0])
            rows.append(values)
    if not rows:
        raise ValueError(f"{label}: no data rows")
    return np.array(sorted(rows))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cad_csv")
    parser.add_argument("measured_csv")
    parser.add_argument("--measured-phasor", required=True, choices=("positive-time", "negative-time"))
    args = parser.parse_args(argv)
    try:
        cad = read_sweep(args.cad_csv, "CAD")
        measured = read_sweep(args.measured_csv, "measured")
        for col in (4, 5):
            if np.any(cad[:, col] != cad[0, col]) or np.any(measured[:, col] != cad[0, col]):
                raise ValueError(f"{FIELDS[col]} must be constant and identical in both sweeps")
        hz = measured[:, 0]
        measured = measured[(hz >= cad[0, 0]) & (hz <= cad[-1, 0])]
        if not len(measured):
            raise ValueError("no measured frequencies within the CAD frequency range")
    except (ValueError, OSError, csv.Error) as exc:
        parser.error(str(exc))

    if args.measured_phasor == "positive-time":
        measured[:, 2] *= -1
    hz = measured[:, 0]
    residual = np.column_stack([np.interp(hz, cad[:, 0], cad[:, col]) - measured[:, col]
                                for col in (1, 2, 3)])
    writer = csv.writer(sys.stdout)
    writer.writerow(["Hz", *(f"residual_{name}" for name in FIELDS[1:4])])
    writer.writerows(np.column_stack((hz, residual)))
    for name, values in zip((*FIELDS[1:4], "complex_Z_ohm"),
                            (*residual.T, np.hypot(residual[:, 0], residual[:, 1]))):
        rms = np.sqrt(np.mean(values**2))
        print(f"{name} RMS={rms:.9g} max_abs={np.max(np.abs(values)):.9g}", file=sys.stderr)


if __name__ == "__main__":
    main()
