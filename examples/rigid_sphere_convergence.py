"""Run with PYTHONPATH=src python examples/rigid_sphere_convergence.py."""
import numpy as np

from ausolveris.geometry.bem import AnalyticalRigidSphereReferenceEvaluator
from ausolveris.geometry.sphere_scattering import rigid_sphere_scattered_pressure


if __name__ == "__main__":
    observers = [(2, 0, 0), (0, 2, 0), (-2, 0, 0)]
    print("ka  panels  relative L2 error in complex scattered pressure")
    for k in (0.5, 1.0, 2.0):
        ref = AnalyticalRigidSphereReferenceEvaluator(1, k, 1, (1, 0, 0))
        exact = np.array(ref.evaluate(observers)["scattered_pressure"])
        for level in range(4):
            pressure = rigid_sphere_scattered_pressure(k, level, observers)
            error = np.linalg.norm(pressure - exact) / np.linalg.norm(exact)
            print(f"{k:3.1f} {20 * 4**level:6d}  {error:.3%}", flush=True)
