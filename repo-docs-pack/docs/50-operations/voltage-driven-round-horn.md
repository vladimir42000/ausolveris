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

## Effect on the 1 V RMS motor

Run `python examples/round_horn_rear_volume_sweep.py --compare-webster` with the pinned kernel and environment above. The reference applies the Webster throat impedance to the same motor through the scalar electrical and mechanical equations. Each model scales its own axial pressure by its predicted diaphragm velocity. Relative phasor differences are 100 times the magnitude of the FEM-to-reference complex ratio minus one (subtraction inside the magnitude).

| Rear load | Peak frequency of electrical impedance magnitude, FEM / Webster (Hz) | Max complex electrical impedance difference (%) | Max complex diaphragm velocity difference (%) | Max absolute axial SPL difference at 1 m (dB) |
|---|---:|---:|---:|---:|
| Released | 204 / 204 | 0.1121 | 0.0622 | 0.1051 |
| Sealed, 10 cm³ | 296 / 296 | 0.1691 | 0.0752 | 0.1062 |

Each maximum covers all 221 frequencies at 1 Hz spacing, using the default 48 × 8 FEM mesh. Agreement of peak frequency is limited by that spacing. The motor sees the acoustic throat impedance multiplied by diaphragm area squared, in series with its mechanical impedance. This explains how a several-percent throat-load difference can have a much smaller effect on this particular motor.

## Rectangular straight-duct coupling

The rectangular benchmark uses a 120 × 60 mm constant section, 120 mm length, rigid walls and an infinite flush baffle. The rear pressure is zero. The motor drives the full inlet area at 1 V RMS. The finite-volume interior exchanges patch-averaged pressure and normal velocity with an area-averaged Rayleigh load at the outlet. Each mouth patch contributes its own complex velocity to the microphone pressure.

With the same Python environment as above:

```python
import numpy as np
from os_lem.model import Driver
from ausolveris.geometry.driven_round_horn import solve_driven_rectangular_duct

driver = Driver("illustrative", 6., .0001, 4., .002, .0003, 1.,
                .12*.06, "front", "rear", 1.)
for hz in (1000, 3000):
    r = solve_driven_rectangular_duct(.12, .06, .12, hz, driver, cells=(12, 6, 72))
    p = r.exterior_pressure_rms([[0., 0., 1.]])[0]
    print(hz, abs(r.electrical_impedance), 20*np.log10(abs(p)/20e-6))
```

At 1 and 3 kHz this yields 87.530 and 87.710 dB respectively. Changing the grid from 8 × 4 × 48 to 12 × 6 × 72 changes these levels by 0.036 and 0.003 dB. Local edge velocities depend more strongly on grid resolution. Tests cover the mean duct transfer, an independent hemispherical radiation-power integral and the motor power balance. A flared transition, high-frequency mesh study and external horn reference remain open.

## Linearly flared rectangular horn

Run `python examples/rectangular_horn_convergence.py` with the pinned kernel. The example linearly expands a 25 × 20 mm throat to a 120 × 60 mm mouth over 120 mm. The rigid, symmetric interior uses trilinear hexahedral pressure elements in a quarter domain. The four mirrored outlet quadrants interact through the full baffled Rayleigh load. The illustrative motor covers the throat and receives 1 V RMS with released rear pressure.

The two principal cuts sample 0–85° every 5° at 1 m. Each percentage is the L2 norm of the change in complex pressure relative to the finer cut, including amplitude and phase. Transverse counts refer to the quarter mesh. The final refinement goes from 12 × 6 × 72 to 16 × 8 × 96.

| kHz | Horizontal change (%) | Vertical change (%) |
|---:|---:|---:|
| 1 | 0.052 | 0.049 |
| 3 | 0.127 | 0.115 |
| 6 | 1.033 | 1.136 |
| 12 | 7.905 | 7.926 |
| 30 | 90.534 | 87.025 |

The two finest grids agree closely at the sampled 1 and 3 kHz points. At 30 kHz the polar predictions remain unresolved. These changes measure mesh sensitivity; independent horn validation remains open.

## Separating axial and transverse dispersion at 30 kHz

Use the same pinned kernel, drive, microphone positions and rectangular flare as above. Run each command from the repository root with the environment used for the 1 V example.

```sh
python examples/rectangular_horn_convergence.py --directional --axial-order 1
python examples/rectangular_horn_convergence.py --directional --axial-order 2
```

The first two mesh counts cover one transverse quadrant. The third is the number of axial elements. Order 2 adds a midpoint plane to each axial element, leaving the aperture basis and motor coupling unchanged. The default is order 1. Changes below use complex pressure and the finer cut as the L2 denominator.

| Axial order | Quarter mesh, from → to | Change in H / V cuts |
|---|---|---:|
| Linear | 12 × 6 × 72 → 12 × 6 × 96 | 90.23% / 87.07% |
| Linear | 12 × 6 × 96 → 16 × 8 × 96 | 3.34% / 4.56% |
| Quadratic | 12 × 6 × 36 → 12 × 6 × 48 | 31.10% / 28.60% |
| Quadratic | 24 × 12 × 80 → 24 × 12 × 96 | 1.18% / 1.08% |
| Quadratic | 20 × 10 × 96 → 24 × 12 × 96 | 1.11% / 3.36% |
| Quadratic | 20 × 10 × 80 → 24 × 12 × 96 | 1.72% / 3.45% |

The first and third comparisons use identical nodal plane counts (73 → 97). For an independent propagation check, the straight rectangular duct admits an exact transfer relation between mean mouth pressure, mean mouth velocity and mean inlet pressure. At 30 kHz the relative inlet-pressure residual on a 4 × 3 transverse quadrant was 125.37% for 96 linear elements, 14.91% for 48 quadratic elements and 0.99% for 96 quadratic elements. This test also checks input and aperture power.

The final combined quadratic refinement, 24 × 12 × 96 → 32 × 16 × 128, changes the horizontal and vertical complex cuts by 1.58% and 3.68%. On-axis SPL at 1 m changes from 56.237 to 56.127 dB. After normalizing each magnitude pattern by its own axial magnitude, the L2 changes are 1.52% and 2.28%. The vertical cut still has appreciable transverse sensitivity. The finite set of angles and mesh comparisons does not establish pointwise accuracy near nulls or agreement with measured hardware.

The directional runs use layer-by-layer Schur elimination of the real interior. This allowed the largest quadratic case to complete after the full complex sparse factorization exceeded available memory. On the 30 shared refinement pairs (15 per order) the full and layered algorithms reproduce the tabulated changes and levels to well within the printed precision. The suite with OS-LEM at 9489f19 passes 480 tests.
