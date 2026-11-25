# FreeCAD horn prototype

Open conical-fixture/horn.FCStd and edit the Dimensions spreadsheet. The reference cone has a 20 mm throat diameter, 60 mm mouth diameter and 80 mm length. The AirVolume solid fills the bore and closes both ports. PrintableWall contains the wall and mouth flange. Export each object separately after editing. The included STLs use millimetres.

From the repository root, install requirements.txt, gmsh and the OS-LEM kernel at 9489f1941cc64abac8bad2dc4f2fb86c697a91b3. Run:

```sh
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python examples/cad_horn_sweep.py examples/freecad/conical-fixture/air-volume.stl examples/freecad/illustrative-driver.json --units mm --cell-mm 6 --hz 125 250 500 750 1000 1500 > prediction.csv
```

The inlet and mouth are simply connected flat caps at the z extrema. The solver assumes rigid walls and a uniform equivalent circular piston in an infinite baffle. The generic driver and lumped front and rear volumes are illustrative. The calculated on-axis pressure is at 1 m from the mouth with 1 V RMS at the motor. These curves describe a numerical fixture. A physical comparison needs the actual driver, chamber, mounting conditions and measurement geometry.

For a measured CSV with the same frequency, voltage, distance, complex impedance and SPL columns, run the following if the instrument reports a positive imaginary inductive impedance:

```sh
python examples/compare_horn_measurement.py prediction.csv measured.csv --measured-phasor positive-time
```

A prototype check should use the voltage at the speaker terminals, a sealed adapter, a documented baffle and rear load, and calibrated microphone coordinates measured from the mouth. Compare complex input impedance and SPL before inspecting angular response. In subwavelength chambers the lumped model couples the cone volume flow to the actual throat flow. Higher modes, cone breakup, leaks, wall vibration and finite baffle diffraction can require a different physical model as frequency increases.

On the included cone, a 6 mm target generated 12,012 tetrahedra. At 125, 250, 500, 750, 1000 and 1500 Hz, the on-axis levels differed by at most 0.132 dB from the native axisymmetric solver at 96 axial × 16 radial cells using the same nominal geometry and motor. This is a numerical cross-check limited to those six samples, not an experimental accuracy claim.
