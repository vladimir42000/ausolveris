"""BEM‑001 acceptance tests for scalar Helmholtz Green‑function utility."""

import math
import pytest
from ausolveris.geometry.bem import helmholtz_green_function, helmholtz_wavenumber


def test_known_r_k_returns_expected_value():
    r = 1.0
    k = 2.0
    expected = math.e ** (1j * k * r) / (4.0 * math.pi * r)
    result = helmholtz_green_function(r, k)
    assert result == expected


def test_k_zero_returns_real_inverse_distance():
    r = 3.5
    result = helmholtz_green_function(r, 0.0)
    expected = 1.0 / (4.0 * math.pi * r)
    assert result == expected
    assert isinstance(result, complex)
    assert result.imag == 0.0


def test_magnitude_is_independent_of_k():
    r = 2.0
    for k in [0.0, 1.0, 10.0, 100.0]:
        g = helmholtz_green_function(r, k)
        assert abs(g) == pytest.approx(1.0 / (4.0 * math.pi * r))


def test_far_field_decay_ratio():
    r1 = 1.0
    r2 = 10.0
    k = 5.0
    g1 = helmholtz_green_function(r1, k)
    g2 = helmholtz_green_function(r2, k)
    # Magnitude should decay as 1/r
    ratio = abs(g2) / abs(g1)
    expected_ratio = r1 / r2
    assert ratio == pytest.approx(expected_ratio, rel=1e-12)


def test_deterministic_repeated_evaluation():
    import random
    random.seed(42)
    r = random.uniform(0.5, 5.0)
    k = random.uniform(0.0, 50.0)
    values = [helmholtz_green_function(r, k) for _ in range(10)]
    assert all(v == values[0] for v in values)


def test_rejects_non_positive_r():
    with pytest.raises(ValueError, match="strictly positive"):
        helmholtz_green_function(0.0, 1.0)
    with pytest.raises(ValueError, match="strictly positive"):
        helmholtz_green_function(-0.1, 1.0)
    with pytest.raises(ValueError, match="strictly positive"):
        helmholtz_green_function(-1e6, 1.0)


def test_rejects_non_finite_r():
    for bad_r in [float('inf'), float('-inf'), float('nan')]:
        with pytest.raises(ValueError):
            helmholtz_green_function(bad_r, 1.0)


def test_rejects_negative_or_non_finite_k():
    for bad_k in [-0.1, -10.0, float('inf'), float('-inf'), float('nan')]:
        with pytest.raises(ValueError):
            helmholtz_green_function(1.0, bad_k)


def test_helmholtz_wavenumber_correctness_and_validation():
    # Correct value
    k = helmholtz_wavenumber(1000.0, 343.0)
    assert k == pytest.approx(2 * math.pi * 1000 / 343)
    # Valid edge: f=0 returns 0
    assert helmholtz_wavenumber(0.0, 343.0) == 0.0
    # Invalid frequency
    for bad_f in [-0.1, float('inf'), float('-inf'), float('nan')]:
        with pytest.raises(ValueError):
            helmholtz_wavenumber(bad_f, 343.0)
    # Invalid speed
    for bad_c in [0.0, -1.0, float('inf'), float('-inf'), float('nan')]:
        with pytest.raises(ValueError):
            helmholtz_wavenumber(1000.0, bad_c)


def test_bem_module_exposes_only_utility():
    import ausolveris.geometry.bem as bem
    public = [name for name in dir(bem) if not name.startswith('_')]
    # Must expose the two utility functions
    assert 'helmholtz_green_function' in public
    assert 'helmholtz_wavenumber' in public
    # Must not expose any matrix, operator, scattering, or solver objects
    forbidden = [
        'HelmholtzMatrix',
        'BoundaryOperator',
        'ScatteringSolver',
        'Solver',
        'Assembler',
        'BEM',
        'Operator',
    ]
    for name in forbidden:
        assert name not in public, f"Module bem unexpectedly contains {name}"
        
