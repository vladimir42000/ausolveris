# Exterior Observer Scaffold (BEM‑004E)

- **Scope:** BEM‑004E implements only the exterior observer coordinate scaffold and domain validation.
- Observers are Cartesian points (x, y, z) in metres, strictly in the exterior domain.
- Points with distance from origin ≤ sphere_radius are rejected (InvalidObserverDomainError).
- No analytical reference evaluator, observer pressure, reconstruction operator, or BEM solve is performed.
- No SPL, directivity, or impedance is computed.
- The scaffold is deterministic; observer order is preserved; package IDs use SHA‑256.