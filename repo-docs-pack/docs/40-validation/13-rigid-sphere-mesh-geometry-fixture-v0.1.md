# Rigid‑Sphere Mesh Geometry Fixture (BEM‑002)

- **Scope:** BEM‑002 adds only a deterministic rigid‑sphere geometry fixture for the benchmark
  `ben004_rigid_sphere_scattering_registered`.
- **Mesh:** closed triangular surface mesh derived from a subdivided icosahedron. All faces are
  non‑degenerate, vertices are unique, and the mesh is manifold (genus‑0 compatible).
- **Normals:** all panel normals point outward from the sphere centre into the exterior acoustic
  domain. The convention is recorded as `normal_convention = "outward_to_exterior_acoustic_domain"`.
- **Determinism:** vertex ordering, panel ordering, and the fixture hash (SHA‑256) are fully
  deterministic and repeatable.
- **No BEM computation:** the fixture does not contain BEM matrix assembly, boundary integral
  operators, Green‑function evaluations, or scattering solutions.
- **What this is not:**
  - No boundary integral operator.
  - No scattering solve.
  - No analytical scattering evaluator.
  - No SPL or impedance output.
  - No enclosure BEM or LEM coupling.
- **Future use:** BEM‑003 and BEM‑004 may consume this fixture as a trusted geometry reference.