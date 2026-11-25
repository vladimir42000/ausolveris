# Voltage-driven round horn — development checkpoint

Base: AuSolveris PR #7 at b86d4a91ce2c5ef5a00bc4370d0cecb040779bd7. Branch: dev/voltage-driven-round-horn. Compatible kernel: vladimir42000/os-lem at 9489f1941cc64abac8bad2dc4f2fb86c697a91b3.

The example uses OS-LEM's coupled driver matrix, terminates the front with the complex FEM horn impedance and, by default, fixes rear pressure to zero. Electrical and mechanical equations come from the kernel. All exported phasors use exp(-i omega t) and RMS amplitudes. The direct rigid diaphragm has the same area as the throat. The motor is an illustrative linear fixture; its parameters do not characterize a commercial compression driver.

## Reproduce

From the AuSolveris branch in a virtual environment with Git access:

```sh
python -m pip install -r requirements.txt
python -m pip install 'git+https://github.com/vladimir42000/os-lem.git@9489f1941cc64abac8bad2dc4f2fb86c697a91b3'
export OPENBLAS_NUM_THREADS=1 PYTHONPATH=src
python -m unittest discover -s tests/geometry -p test_driven_round_horn.py -v
python examples/round_horn_one_volt.py > horn-1v.csv
```

The CSV contains 135 observations on the 1 m arc (0 to 88 degrees in 2-degree steps). On-axis results:

| Hz | Axial x radial cells | Input impedance, ohm | SPL at 1 m, dB re 20 µPa |
|---:|---:|---:|---:|
| 1000 | 96 x 16 | 6.116735 + 0.685931i | 76.31745 |
| 6000 | 192 x 32 | 6.003398 - 3.557607i | 75.09428 |
| 30000 | 768 x 128 | 6.000136 - 18.807114i | 57.72575 |

Three new unittest cases passed with the pinned kernel. Four existing round-horn regression functions also passed when executed directly. The independent circuit oracle checks complex electrical impedance. Mouth power integrated from annular FEM pressure and velocity closes the electrical power balance at 1 and 6 kHz. A second FEM solve checks peak-to-RMS complex microphone pressure scaling.

## Rear load and resonance sweep

Run `python examples/round_horn_rear_volume_sweep.py` in the same environment for a 140–360 Hz sweep in 1 Hz increments on the default 48 × 8 mesh. With the same horn and 1 V RMS motor, the sampled maximum of electrical impedance magnitude occurs at 204 Hz (21.9953 ohm) for released rear pressure and 296 Hz (21.9896 ohm) for a sealed 10 cm³ rear cavity. The cavity is a lumped, lossless compliance, adding mechanical stiffness rho c² Sd² / V. The circuit regression checks the complex impedance at three frequencies with this stiffness added analytically.

The full suite with the pinned kernel passed (472 tests, including the driver coupling checks). Independent full-horn validation against matched AKABAK results or measurements remains open.

## Independent low-frequency model comparison

Run `PYTHONPATH=src python examples/round_horn_webster_reference.py`. This compares the conical FEM with a one-dimensional Webster model integrated from mouth to throat. The reference uses the uniform baffled piston's Bessel–Struve mean mouth impedance and closed-form on-axis pressure at 1 m. Both models prescribe 1 m/s throat velocity, use the same air properties and assume an infinite baffle. The comparison isolates the acoustics from motor and rear-volume effects.

| Hz | Relative complex throat impedance difference (%) | Axial level FEM minus Webster (dB) | Axial phase FEM minus Webster (deg) |
|---:|---:|---:|---:|
| 140 | 6.78 | 0.014 | 0.005 |
| 204 | 6.85 | 0.032 | 0.008 |
| 296 | 7.00 | 0.070 | 0.015 |
| 360 | 7.16 | 0.108 | 0.023 |

Results use 96 axial by 16 radial cells. Doubling both counts from 48 by 8 changes the reported impedance difference by less than 0.10 percentage point at these frequencies. The persistent discrepancy concerns throat loading even where axial levels agree closely. Webster assumes sectionally uniform pressure and the reference represents the outlet as a uniform piston. This check covers four low frequencies and one observer.
