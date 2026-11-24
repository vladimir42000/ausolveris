# 31 — Boundary Integral Formulation and Singular Kernel Taxonomy
Version: v0.1 with BEM-007C convention correction
Milestone: BEM-007A
Type: documentation-only freeze
Executable code changes: none

---

## 1. Exact acoustic BEM formulation

**Selected formulation: indirect single-layer (ISL) BEM**

The scattered acoustic field is represented as a single-layer potential:

```
p_s(x) = ∫_S G(x, y; k) σ(y) dS(y)     x ∉ S
```

where:
- `S` is the closed rigid-sphere surface,
- `σ(y)` is the unknown single-layer source density (units: Pa/m),
- `G(x, y; k)` is the free-space Helmholtz Green function (defined below),
- the integral is over the source surface `S`.

The boundary condition on a rigid (sound-hard) sphere is zero total normal
velocity: `∂p_total/∂n = 0` on `S`. Since `p_total = p_inc + p_s`, this gives:

```
∂p_s/∂n(x) = -∂p_inc/∂n(x)     x ∈ S
```

Applying the normal derivative of the single-layer potential and using the
jump relation, the boundary integral equation for σ is:

```
−(1/2) σ(x) + (D'σ)(x) = -∂p_inc/∂n(x)     x ∈ S
```

where `D'` is the adjoint double-layer operator. In the current controlled
prototype (BEM-004C), the `−(1/2)σ` jump term and the `D'` operator are
approximated together by the regularized algebraic prototype. A physically
correct boundary solve must implement these terms explicitly.

This formulation is selected because:
- it is consistent with the single-layer kernel already used in BEM-003
  and BEM-006A,
- the observer reconstruction `p_s(x_obs) = (Sσ)(x_obs)` uses the scalar
  Green function whose target-normal derivative enters the boundary operator,
- it avoids the Burton–Miller hypersingular integral required by some direct
  formulations, deferring hypersingular treatment to a later milestone.

No other formulation (direct, double-layer, combined) is authorized for
the next implementation path.

---

## 2. Boundary unknown x

**Selected unknown: single-layer source density σ**

`σ(y)` is the unknown surface density, physically interpreted as the
equivalent acoustic source strength per unit area distributed on `S`.
Units: Pa/m, since G dS has units of metres.

`σ` is not the boundary pressure and is not the normal velocity or the
Neumann data. These are quantities that can be recovered after σ is found,
but σ itself is an auxiliary indirect unknown.

Specifically:
- `σ` is **not** `∂p/∂n` (the Neumann data).
- `σ` is **not** `p|_S` (the Dirichlet trace).
- `σ` is the **density of a surface monopole layer** whose field equals `p_s` in the exterior.

The BEM-004C regularized algebraic prototype treats its solution vector as a
stand-in for σ but without a physical Neumann-data derivation. This is the
primary mathematical deficit identified in BEM-PHASE4-PLAN-002.

---

## 3. Boundary operator A

At a panel-centroid target x, the exterior rigid-wall equation uses
A = K′ − I/2. Each K′ entry integrates n(x) · ∇_x G over a source triangle.
The right-hand side is −n(x) · ∇p_inc. BEM-004C uses a regularized prototype
matrix. BEM-007C supplies a pointwise reference derivative and exterior jump
operation. Physical panel integration and assembly remain future work.

## 4. Observer operator H

**Single-layer evaluation at exterior points**

```
(Hσ)(x_obs) = ∫_S G(x_obs, y; k) σ(y) dS(y)     x_obs ∉ S
```

Discretized at centroid collocation (BEM-006A):

```
H[i_obs, j_panel] = G(|x_obs_i − centroid_j|, k) × area_j
```

H uses the scalar single-layer kernel.
No normal-derivative term appears in H for strictly exterior observers
(the kernel is regular since `|x_obs − y| > 0` for all such points).

**Pressure separation:**
- Incident pressure: `p_inc(x_obs) = A exp(i k d·x_obs)` — evaluated
  analytically via BEM-004F conventions or directly.
- Scattered pressure: `p_s(x_obs) = (Hσ)(x_obs)` — the H-matrix product.
- Total pressure: `p_total = p_inc + p_s`.

This separation is already implemented in BEM-006A/006B/006C and must be
preserved in all future milestones.

---

## 5. Discretization type

**Selected: centroid collocation**

Collocation is selected over Galerkin for the next implementation path.
Rationale: lower implementation complexity; no mass matrix required; directly
compatible with existing BEM-003/006A matrix build loop.

**Collocation point placement:** panel centroid.

One collocation equation per panel. The collocation point for panel `j` is
the centroid `c_j = (v_0 + v_1 + v_2) / 3` where `v_0, v_1, v_2` are the
triangle vertices. The collocation point fixes the target. Source-panel quadrature order can change independently.

Galerkin discretization is deferred and not authorized for the next
implementation path.

---

## 6. Panel geometry assumptions

**Flat triangles only**

All panels are flat (planar) triangles. Curved geometry is excluded for the
current benchmark phase. The rigid sphere is approximated by a piecewise-flat
triangulated surface.

Panel geometry is fully described by three vertex coordinates. From these:

- **Centroid:** `c = (v_0 + v_1 + v_2) / 3`
- **Outward normal:** `n̂ = (v_1 − v_0) × (v_2 − v_0) / |(v_1 − v_0) × (v_2 − v_0)|`
  (vertex ordering must be counter-clockwise when viewed from outside the sphere)
- **Area:** `|area| = (1/2) |(v_1 − v_0) × (v_2 − v_0)|`

Curved-element geometry (isoparametric mapping, NURBS) is not considered.
Any future milestone that introduces curved elements must be separately
authorized.

---

## 7. Normal orientation and derivative convention

**Outward body normal at the target**

The trace is taken by approaching x from x + ε n(x) for positive ε.
With r = |x − y|, the target-normal kernel equals
G(r,k) (ik − 1/r) n(x) · (x − y)/r.
K′ is the principal-value integral of this kernel. The exterior trace is
K′σ − σ/2 and the interior trace with the same normal is K′σ + σ/2.
The incident-field derivative on the right-hand side uses the same target normal.

**Phase convention: `e^{-iωt}` (suppressed)**

The time factor `e^{-iωt}` is suppressed throughout. Spatial fields carry
`e^{+ikr}` for outgoing waves. This is confirmed by:

- `p_inc = A exp(+i k d·x)` in BEM-004F (`exp(1j * k * dots)`).
- `G(r,k) = exp(+ikr) / (4π r)` in BEM-001 (`helmholtz_green_function`).

All future quadrature implementations must use this same sign. A change of
sign convention must be a separately authorized and documented patch.

---

## 8. Diagonal / self-panel treatment

**For the indirect single-layer operator S only**

The kernel `G(r,k) = exp(+ikr)/(4πr)` has a weak singularity `O(1/r)` at
`r → 0`. For a flat triangular panel:

**Preferred treatment: semi-analytical singular extraction**

Decompose the diagonal integrand as:

```
G(r, k) = [G(r, k) − 1/(4π r)] + 1/(4π r)
```

The first bracket has a finite limit at `r = 0` (since `exp(ikr) − 1 = O(r)`) and
can be integrated numerically with a standard Gauss rule.
The second term `1/(4πr)` is the static Laplace kernel, whose integral over
a flat triangle has a known closed form.

**Closed-form singular integral for a flat triangle:**

For a source at the centroid `c` of a flat triangle with vertices
`v_0, v_1, v_2` and area `A`, the self-panel singular integral is:

```
∫_Δ 1/(4π|c − y|) dS(y) ≈ (1/4π) × I_singular
```

where `I_singular` is derived from the semi-analytical formula for the
Newton potential over a triangle (see Hess & Smith 1967 / Wilton et al. 1984).
Any future on-surface pressure evaluator must verify its chosen diagonal rule. It is not implemented by this document.

**What is not used:**
- Duffy transformation is not selected as the primary strategy for the
  self-panel diagonal. It would require subdividing each panel into sub-panels
  mapped to a reference square, adding implementation complexity without
  a clear accuracy advantage for the weak `O(1/r)` singularity.
- The single-layer pressure trace is continuous.
- For a target inside a flat panel, the principal-value K′ self entry is zero:
  the displacement to every distinct same-panel source is tangent. The
  exterior Neumann diagonal includes the separate −1/2 jump.

---

## 9. Regular off-diagonal quadrature order

**First upgrade: 7-point symmetric Gauss rule on triangle**

Replace the current 1-point centroid collocation for off-diagonal (regular)
entries with a deterministic 7-point Gauss–Legendre rule on the reference
triangle. This rule integrates polynomials exactly up to degree 5.

Quadrature point coordinates and weights (reference triangle with vertices
at `(0,0)`, `(1,0)`, `(0,1)`) must be hard-coded deterministic constants
taken from a published table (e.g. Dunavant 1985, degree-5 rule).

**No adaptive quadrature.** No library-generated quadrature points.
All quadrature tables must be reproducible from fixed constants stored
in the source.

The 7-point rule upgrade for regular off-diagonal entries is the work of
BEM-007B and is not implemented by this document.

---

## 10. Connection to existing milestones

| Milestone | Component | Status relative to ISL formulation |
|---|---|---|
| BEM-004B | Boundary RHS | Computes `−∂p_inc/∂n` at panel centroids — correct RHS for ISL formulation, but the operator A lacks the jump and D' terms |
| BEM-004C | Regularized boundary solve | Prototype algebraic solve; does not represent a physical σ; regularization epsilon is not a physical diagonal correction |
| BEM-006A | H-matrix (S at exterior points) | Correct ISL single-layer evaluation for strictly exterior observers; centroid collocation order-1 |
| BEM-006B | Observer reconstruction | Correct H @ σ product; limited by prototype σ quality |
| BEM-006C | Pipeline integration | Correct error norm computation; benchmark failure is expected |

**What must be corrected in future milestones:**
- BEM-004C must be replaced or supplemented by a physical ISL boundary solve
  that includes the `−(1/2)σ` jump term and the `D'σ` adjoint double-layer term.
- BEM-007B provides a separated-panel pressure quadrature utility. Future
  work must integrate the target-normal kernel for the Neumann matrix.
- Exterior observers lie off the mesh and have no self-panel diagonal.

---

## 11. Non-claim statement

- No validated BEM capability is authorized by this document.
- No singular quadrature is implemented by this document.
- No solver behaviour is changed by this document.
- `benchmark_passed = True` is not claimed.
- This document is a frozen taxonomy only. All numerical work it describes
  must be implemented in subsequent authorized milestones (BEM-007B and later).

---

## References (non-normative)

- Hess & Smith (1967): panel method self-influence integrals over flat triangles.
- Wilton et al. (1984): "Potential integrals for uniform and linear source
  distributions on polygonal and polyhedral domains," IEEE TAP.
- Dunavant (1985): "High degree efficient symmetrical Gaussian quadrature
  rules for the triangle," IJNME.
- Colton & Kress (2013): *Integral Equation Methods in Scattering Theory*.

These references are cited for context. No copyrighted material is reproduced
here.

---

## Lineage

BEM-PHASE4-PLAN-002 → **BEM-007A** → BEM-007B (regular quadrature) → BEM-007C (Neumann convention fixtures)
