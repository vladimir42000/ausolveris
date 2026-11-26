import csv
import importlib.util
import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np


script = Path(__file__).resolve().parents[1] / "examples" / "compare_horn_measurement.py"
spec = importlib.util.spec_from_file_location("compare_horn_measurement", script)
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


class ComparisonTest(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.cad = Path(directory.name) / "cad.csv"
        self.measured = Path(directory.name) / "measured.csv"
        self.rows = [[200, 8, -6, 90, 2, 1], [100, 4, -2, 80, 2, 1]]
        self.write(self.cad, self.rows)

    @staticmethod
    def write(path, rows, fields=comparison.FIELDS):
        with path.open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(fields)
            writer.writerows(rows)

    def run_cli(self, *options):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                comparison.main([str(self.cad), str(self.measured), *options])
            except SystemExit as exc:
                self.assertEqual(exc.code, 2)
                self.assertEqual(out.getvalue(), "")
                return None, err.getvalue()
        return out.getvalue(), err.getvalue()

    def test_interpolation_sign_and_overlap(self):
        for convention, sign in (("positive-time", 1), ("negative-time", -1)):
            with self.subTest(convention=convention):
                rows = [[250, 0, 0, 0, 2, 1], [200, 8, sign*6, 90, 2, 1],
                        [150, 3, sign*8, 87, 2, 1], [50, 0, 0, 0, 2, 1]]
                self.write(self.measured, rows)
                out, err = self.run_cli("--measured-phasor", convention)
                report = list(csv.reader(io.StringIO(out)))
                self.assertEqual(report[0], ["Hz", "residual_Ze_real_ohm", "residual_Ze_imag_ohm",
                                             "residual_SPL_dB"])
                np.testing.assert_allclose(np.array(report[1:], float), [[150, 3, 4, -2], [200, 0, 0, 0]])
                for name, magnitude in (("Ze_real_ohm", 3), ("Ze_imag_ohm", 4),
                                        ("SPL_dB", 2), ("complex_Z_ohm", 5)):
                    self.assertIn(f"{name} RMS={magnitude/np.sqrt(2):.9g} max_abs={magnitude}", err)

    def test_errors(self):
        row = self.rows[0]
        cases = [
            ([row, row], "measured: duplicate frequency 200 Hz"),
            ([[0, *row[1:]]], "measured line 2: Hz must be positive"),
            ([["nan", *row[1:]]], "measured line 2: nonfinite Hz"),
            ([[200, "bad", *row[2:]]], "measured line 2: invalid Ze_real_ohm"),
            ([[*row[:4], 1, 1]], "voltage_V_rms must be constant and identical in both sweeps"),
            ([row, [100, 4, -2, 80, 2, 3]], "distance_m must be constant and identical in both sweeps"),
            ([[250, *row[1:]]], "no measured frequencies within the CAD frequency range"),
            ([], "measured: no data rows"),
        ]
        for rows, message in cases:
            with self.subTest(message=message):
                self.write(self.measured, rows)
                out, err = self.run_cli("--measured-phasor", "negative-time")
                self.assertIsNone(out)
                self.assertTrue(err.rstrip().endswith(message), err)

    def test_required_phasor_and_columns(self):
        self.assertIn("required: --measured-phasor", self.run_cli()[1])
        self.write(self.measured, [], fields=comparison.FIELDS[:-1])
        self.assertIn("measured: missing column distance_m",
                      self.run_cli("--measured-phasor", "positive-time")[1])
