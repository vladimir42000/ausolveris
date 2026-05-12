# BEM-007B regular off-diagonal triangle quadrature v0.1

## Scope

BEM-007B implements pairwise regular off-diagonal triangle quadrature only.
It is for separated flat triangles under the indirect single-layer formulation
frozen by BEM-007A. The implemented scalar kernel is the regular Helmholtz
single-layer Green function evaluated from a separated source triangle to a
target collocation point.

The implemented utility is a pairwise mathematical evaluator. It is not an
assembled A matrix. It is not a solver result. It is not a validated BEM result.

## Quadrature rule

The implementation uses a fixed hardcoded deterministic seven-point triangle
quadrature rule on the reference triangle with area convention 0.5. Physical
integration is obtained by multiplying reference weights by the source-triangle
Jacobian. No SciPy, adaptive integration, stochastic sampling, or runtime rule
selection is used.

## Explicit exclusions

BEM-007B does not implement singular quadrature. It does not implement
near-singular quadrature. It does not use a Duffy transformation. It does not
perform self-panel diagonal treatment. It does not assemble the full A matrix.
It does not solve a BEM system. It does not compare against the analytical rigid
sphere benchmark. It does not validate BEM capability.

## Metadata and claim surface

The result metadata intentionally states:

```json
{
  "quadrature_stage": "bem007b_regular_off_diagonal_prototype",
  "benchmark_id": "ben004_rigid_sphere_scattering_registered",
  "regular_quadrature_implemented": true,
  "singular_quadrature_implemented": false,
  "physical_a_matrix_assembled": false,
  "adaptive_integration_used": false,
  "flat_panels_only": true,
  "benchmark_passed": false,
  "non_physical": true
}
```

The utility returns a deterministic SHA-256 package identifier derived from the
source panel, target panel, wavenumber, fixed rule identifier, and metadata. It
does not use Python's built-in `hash()`.

## Validation posture

The BEM-007B validation surface is limited to deterministic mathematical utility
checks in `tests/geometry/test_regular_quadrature.py`. These tests check valid
separated panels, controlled rejection of self/touching/invalid panels, fixed
quadrature-rule weight convention, deterministic complex output, deterministic
SHA-256 package IDs, and non-physical metadata boundaries.
