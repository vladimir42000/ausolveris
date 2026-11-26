# AuSolveris restart audit and BEM-007C proposal

The full test suite at main commit f9d56a3 passed on 25 November 2026 (439 passed, Python 3.12). BEM-007B evaluates a single-layer pressure integral between separated triangular panels. The rigid-sphere scattering benchmark is still open.

## Proposed BEM-007C task

Reconcile sections 1, 3 and 7 of [the BEM-007A formulation](../40-validation/31-boundary-integral-formulation-taxonomy-v0.1.md) and pin the exterior Neumann trace convention with an independent analytical test fixture. Doing this before selecting a self-panel quadrature prevents inserting an accurate pressure integral into the wrong matrix.

For the outgoing kernel $G=e^{ikr}/(4\pi r)$, take the body normal pointing into the exterior and define $K'$ using $n(x)\cdot\nabla_x G(x,y)$ at the target. The exterior normal trace of the single-layer potential is $(-I/2+K')\sigma$. The observer pressure uses $G$ directly. With coordinates in metres and pressure in Pa, $G\,dS$ has units of metres and the density has units of Pa/m.

### Acceptance checks

1. Use a point source at the origin and target at (0,0,2) m with outward target normal (0,0,1) and source normal (1,0,0). At zero wavenumber the target derivative is $-1/(16\pi)$ in inverse square metres, while the source-normal derivative is zero. Repeat at finite wavenumber against a centred finite difference of the scalar Green function in the target-normal direction.
2. For a sphere of radius $a$ with constant unit density at zero wavenumber, the single-layer potential is $a$ inside and $a^2/r$ outside. At the surface the outward derivatives are 0 from inside and −1 from outside. Require the chosen trace convention to recover both limits. This fixture is an independent identity and does not establish numerical mesh convergence.
3. Record which operator consumes each self term. For a flat triangle and its interior centroid, the target-normal derivative kernel vanishes away from coincidence on the same plane. The exterior trace still has its jump contribution. The weakly singular pressure integral of $G$ has a different diagonal.

The proposed deliverables are a corrected formulation and reference fixtures. Assembly, meshed-sphere comparison and enclosure coupling are subsequent milestones. For the trace convention see [Huybrechs, Theorem 2.6.5](https://www.sam.math.ethz.ch/zss/zss2006/News/Huybrechs_Thesis.pdf).
