# Horn workflow coverage, 25 November 2026

Scope is AuSolveris on PR #7 and the loudspeaker workflows relevant to a front-loaded horn. The comparator is the [AKABAK product description](https://www.randteam.de/AKABAK3/AKABAK-Introduction.html). A 30 kHz horn is our design target. A matched AKABAK project or measured reference has yet to be run.

Each row has equal weight. Stages are 0% for no working implementation in this workflow, 25% for tested components, 50% for a runnable physical benchmark, 75% for a runnable horn example, and 100% for the example meeting agreed acceptance limits against an independent reference. These are management estimates. Separate OS-LEM releases earn credit here once the workflow can use them.

| Workflow | Stage | Evidence or missing deliverable |
|---|---:|---|
| Geometry input and meshing | 25% | Geometry and YAML tools, triangulated sphere. Horn surface import or generation and mesh checks pending. |
| Exterior 3D acoustics | 50% | Physical dense Neumann solve for a rigid sphere with mesh refinement. A separate half-space piston benchmark now covers prescribed velocity. |
| Observer pressure and directivity | 50% | Executable sphere example with complex pressure at configurable exterior positions. Piston polar sweep available. Horn polar sweep pending. |
| Interior horn and mouth radiation | 0% | Coupled throat, walls, mouth and exterior needed. |
| Axisymmetric horn analysis | 0% | Profile-based radiation solve needed. |
| Driver network and acoustic feedback | 0% | Coupling to OS-LEM and a driven 1 V example needed. |
| End-user acoustic plots and export | 50% | Runnable piston example exports absolute SPL, complex pressure and relative level to CSV and directivity to PNG. The horn workflow is pending. |

Mean stage score is 175/7 = 25.0%. Zero of seven rows has reached the independently validated horn-example stage. Electronics design, room acoustics, direct sound and other parts of AKABAK are outside this comparison.

## Numerical evidence

Run from the repository root with NumPy available:

```sh
OPENBLAS_NUM_THREADS=1 PYTHONPATH=src python examples/rigid_sphere_convergence.py
```

The unit-radius sound-hard sphere receives a 1 Pa plane wave along +x. Microphones are at twice the radius at 0°, 90° and 180° to the propagation direction. Relative L2 error compares complex scattered pressures against the existing analytical partial-wave solution. The dimensionless ka values below describe wavelength relative to radius.

| Panels | ka = 0.5 | ka = 1 | ka = 2 |
|---:|---:|---:|---:|
| 20 | 23.558% | 20.009% | 42.336% |
| 80 | 3.105% | 5.818% | 9.851% |
| 320 | 3.152% | 3.932% | 4.541% |
| 1,280 | 2.398% | 2.483% | 2.838% |

The benchmark solves a single-layer boundary density with the exterior Neumann jump, then integrates pressure at each microphone. Off-diagonal rows include edge- and vertex-adjacent panels. The corrected fixture projects every mesh vertex onto the requested sphere and derives normals from the triangular faces. Its geometry hashes change. Close parallel evaluation is checked separately against the static solid angle of a square.

## Prescribed-velocity radiator

A 25.4 mm diameter circular piston centred in an infinite rigid baffle radiates into the front half-space. The example uses 1 m/s peak uniform velocity, a 1 m microphone radius, air density 1.21 kg/m³ and sound speed 343 m/s. The Rayleigh integral uses the same outgoing-wave convention as the exterior sphere benchmark. It supplies an independent half-space source model for future horn work.

```sh
PYTHONPATH=src python examples/baffled_piston_polar.py --output-dir piston-results
```

![Level versus angle for a 25.4 mm baffled piston](figures/baffled-piston-directivity.png)

The sweep exports 0° through 89° at 1, 10 and 30 kHz. Tests cover absolute complex on-axis pressure, independent off-axis disk integration in the near field, and signed far-field directivity including the first zero of the Bessel pattern. At 30 kHz the analytical far-field null lies at 33.30°. The finite-distance curve has a dip near that angle. The 1 m response relative to the axis is −3.82 dB at 15°, −21.79 dB at 30° and −17.75 dB at 45°.

The next milestone is a round horn with prescribed throat velocity, rigid walls, and a radiating mouth. Its validation should cover throat pressure divided by volume velocity as well as exterior pressure versus angle.
