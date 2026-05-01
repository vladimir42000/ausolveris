# BEM-PHASE3-PLAN-001 — Phase 3 Path Freeze & Scaffolding Plan (Option A)

**Status:** Authorized by Director on 2026‑05‑01 – frozen forever (Option A).
**Type:** Control‑plane documentation and contract freeze – **zero executable code.**

---

## 1. Path Selection

- **Selected Option:** Option A – Analytical Reference Evaluator and Observer Reconstruction Scaffolding.
- **Rationale:** The mathematically defensible sequence is to establish the analytical truth and the exact observer evaluation frameworks before engineering any singular‑quadrature machinery.
- **Option B (singular quadrature first) is permanently locked out of the current operational phase.**
- All future Phase 3 tasks will operate under the Option A umbrella until and unless a new Director‑level plan is authorized.

---

## 2. Observer Coordinate Framework (Contract Freeze)

### 2.1 Convention
- Observers are specified as a deterministic Cartesian point cloud $\{\mathbf{x}_i = (x_i, y_i, z_i)\}$.
- All observer points MUST be explicitly marked with the metadata tag `"domain": "exterior_domain"`.

### 2.2 Rejection Guardrail
The future observer‑reconstruction interface **must** reject any observer point that violates:
- $\|\mathbf{x}_i\| \le a$ where $a$ is the sphere radius of the
  `ben004_rigid_sphere_scattering_registered` fixture (default $a = 1.0~\text{m}$).
- Points exactly on the boundary ($\|\mathbf{x}_i\| = a$) are treated as **invalid** because the analytical free‑space Green function encounters a non‑integrable singularity.

### 2.3 Metadata Frozen Fields
Any observer‑scaffold object created in Phase 3 MUST carry the following fields, among others to be defined in the implementation milestone:

```yaml
observer_scaffold:
  scaffold_stage: "bem004e_observer_scaffold"
  benchmark_id: "ben004_rigid_sphere_scattering_registered"
  sphere_radius: 1.0               # metres
  domain: "exterior_domain"
  observer_positions:                # list of [x, y, z]
  domain_validation:
    interior_points_rejected: true
    boundary_points_rejected: true
3. Analytical Reference Formulation (Scaffold Contracts)
3.1 Physical Model
The future analytical evaluator will implement the classical rigid‑sphere acoustic scattering series expansion for a plane‑wave incident field:

Incident field: 
p
inc
(
x
)
=
A
e
i
k
d
⋅
x
p 
inc
​
 (x)=Ae 
ikd⋅x
 

Scattered field: 
p
scat
(
x
)
=
∑
n
=
0
∞
…
p 
scat
​
 (x)=∑ 
n=0
∞
​
 … using spherical Bessel & Hankel functions, with coefficients determined by the sound‑hard Neumann condition 
∂
(
p
inc
+
p
scat
)
/
∂
n
=
0
∂(p 
inc
​
 +p 
scat
​
 )/∂n=0 on 
r
=
a
r=a.

3.2 Input Contract (Frozen)
The analytical evaluator must accept a single canonical input package that binds:

Wavenumber 
k
k (non‑negative, finite)

Incident direction 
d
d (unit vector)

Amplitude 
A
A (complex)

Sphere radius 
a
a (positive, finite)

Observer positions (validated exterior‑domain points)

3.3 Output Contract (Frozen)
The evaluator will produce an AnalyticalReferencePackage containing:

analytical_total_pressure at each observer (complex)

analytical_scattered_pressure at each observer (complex)

evaluation_status: "computed"

Deterministic package ID (SHA‑256)

However, until the evaluator is implemented, the only allowed marker in any scaffold is:

analytical_evaluator_implemented = false

analytical_pressure_evaluated = false

reference_matching_performed = false

4. Boundary‑to‑Observer Interface Freeze
4.1 Purpose
After boundary solution unknowns (e.g., from BEM‑004C prototype, or a future full‑sphere solve) become available, a reconstruction operator 
H
H will map the boundary data 
x
x to exterior observer pressures:
p
obs
=
H
x
p 
obs
​
 =Hx

4.2 Contract for observer_pressure_reconstruction_scaffold
A future reconstruction scaffold will hold:

A deterministic reconstruction matrix or operator descriptor.

References to the source boundary solve package and the observer scaffold.

A reconstruction_performed boolean flag, initially false.

An explicit statement that no pressure values are computed until the reconstruction is executed.

The package ID will be derived via SHA‑256 from the concatenation of the input boundary package ID, observer‑scaffold ID, and the matrix descriptor.

5. Tolerance Policy Continuity
The complex‑pressure tolerance policy declared in BEM‑004A remains in effect:

policy_status = "declared_not_applied"

future_application_stage = "BEM-004D" (now extended: analytical matching will be in a later Phase 3 milestone, e.g., BEM‑004F/G).

No tolerance policy execution (pressure or reference matching) may occur until an explicit Director‑level approval of the analytical evaluator and matching harness.

6. Hard Out‑of‑Scope (Enforcement)
No Implementation of Code – BEM-PHASE3-PLAN-001 is a documentation‑only milestone. No .py or test files are authored.

No Singular Quadrature – Option B is entirely locked out; no near/far‑singular BEM integration work is planned in this plan.

No Validation Claims – All complex‑pressure tolerances remain declared_not_applied; no error computation against analytical reference may be performed.

No Modification of Existing BEM‑001 through BEM‑004D – The existing utility chain is frozen and must not require changes in Phase 3 planning.

7. Sign‑Off & Freeze
Director Authorization: 2026‑05‑01

Auditor Acceptance: Pending

Next Step: Await Director approval, then file under repo-docs-pack/docs/40-validation/ and commit. Subsequent BEM‑004E, BEM‑004F, etc. will be defined as concrete implementation milestones derived from this plan.
