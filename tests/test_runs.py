import importlib.util
import pathlib
import sys
import numpy as np


def load_module(name):
    root = pathlib.Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    path = root / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pendulum = load_module("pendulum")
pendulum3d = load_module("pendulum3d")
rk4_test1 = load_module("rk4_test1")
rk4_test2 = load_module("rk4_test2")
rk4_test3 = load_module("rk4_test3")
energy_utils = load_module("energy_utils")
selftest = load_module("selftest")


def test_pendulum_default():
    t, phi, omega, energy = pendulum.run(plot=False)
    # All returned arrays should have the same length
    assert t.shape == phi.shape == omega.shape == energy.shape
    # expected number of steps (10/h + 1)
    assert len(t) == 1001
    # initial conditions
    assert t[0] == 0
    assert np.isclose(phi[0], 0.1)
    # final time
    assert np.isclose(t[-1], 10)
    # final angle close to analytical small angle prediction
    expected_phi_end = 0.1 * np.cos(np.sqrt(9.81) * 10)
    assert np.isclose(phi[-1], expected_phi_end, atol=1e-3)
    # energy should stay positive
    assert energy[-1] > 0


def test_pendulum_energy_conservation():
    t, phi, omega, energy = pendulum.run(plot=False)
    # total mechanical energy should remain nearly constant
    assert np.max(np.abs(energy - energy[0])) < 1e-5


def test_pendulum3d_default():
    t, theta, phi, theta_dot, phi_dot, energy = pendulum3d.run(plot=False)
    assert t.shape == theta.shape == phi.shape == theta_dot.shape == phi_dot.shape == energy.shape
    assert len(t) == 1001
    assert np.isclose(theta[0], 0.1)
    assert np.isclose(phi[0], 0.0)
    expected_theta_end = 0.1 * np.cos(np.sqrt(9.81) * 10)
    assert np.isclose(theta[-1], expected_theta_end, atol=1e-3)


def test_pendulum3d_cartesian_default():
    result = pendulum3d.run_cartesian(plot=False)
    t, x, y, z, vx, vy, vz, energy = result
    assert (
        t.shape
        == x.shape
        == y.shape
        == z.shape
        == vx.shape
        == vy.shape
        == vz.shape
        == energy.shape
    )
    assert len(t) == 1001
    L = 1.0
    theta = np.arccos(-z / L)
    phi = np.arctan2(y, x)
    assert np.isclose(theta[0], 0.1)
    assert np.isclose(phi[0], 0.0)
    expected_theta_end = 0.1 * np.cos(np.sqrt(9.81) * 10)
    assert np.isclose(theta[-1], expected_theta_end, atol=1e-3)


def test_pendulum3d_cartesian_near_vertical_phi_velocity():
    """Run the Cartesian solver near the inverted position."""
    theta0 = np.deg2rad(175)
    result = pendulum3d.run_cartesian(theta0=theta0, phi_dot0=1.0, plot=False)
    # All returned arrays should contain only finite values
    for arr in result:
        assert np.all(np.isfinite(arr))
    energy = result[-1]
    # Energy should stay approximately constant
    assert np.isclose(energy[0], energy[-1], atol=1e-5)


def test_pendulum3d_run_cartesian_fallback():
    result = pendulum3d.run(theta0=0.0, force_y=0.2, plot=False)
    t, theta, phi, theta_dot, phi_dot, energy = result
    for arr in result:
        assert np.all(np.isfinite(arr))
    assert np.any(np.abs(phi_dot) > 0)
    assert np.isclose(energy[0], energy[-1], atol=1e-5)


def test_pendulum3d_impulses_length():
    result = pendulum3d.run(force_x=0.5, force_y=-0.2, force_z=0.1, plot=False)
    t, theta, phi, theta_dot, phi_dot, energy = result
    assert t.shape == theta.shape == phi.shape == theta_dot.shape == phi_dot.shape == energy.shape
    assert len(t) == 1001


def test_pendulum3d_trajectory_and_vectors():
    result = pendulum3d.run(show_trajectory=False, show_vectors=True, plot=False)
    t, theta, phi, theta_dot, phi_dot, energy = result
    assert t.shape == theta.shape == phi.shape == theta_dot.shape == phi_dot.shape == energy.shape


def test_pendulum3d_initial_phi_velocity():
    result = pendulum3d.run(phi_dot0=0.5, air_resistance=0.1, plot=False)
    _, _, phi, _, _, _ = result
    assert not np.isclose(phi[0], phi[-1])


def test_energy_utils_pendulum():
    phi = np.pi / 3
    omega = 0.4
    L = 2.0
    g = 9.81
    expected = 0.5 * L**2 * omega**2 + g * L * (1 - np.cos(phi))
    computed = energy_utils.pendulum_energy(phi, omega, L, g)
    assert np.isclose(computed, expected)


def test_energy_utils_spherical():
    theta = np.pi / 4
    theta_dot = 0.1
    phi_dot = 0.2
    L = 1.5
    g = 9.81
    expected = 0.5 * L**2 * (
        theta_dot**2 + (np.sin(theta) ** 2) * phi_dot**2
    ) + g * L * (1 - np.cos(theta))
    computed = energy_utils.spherical_energy(theta, theta_dot, phi_dot, L, g)
    assert np.isclose(computed, expected)


def test_rk4_test1_default():
    t, x = rk4_test1.run(ax=None)
    assert len(t) == len(x) == 51
    assert t[0] == 0
    assert np.isclose(x[0], 1)
    assert np.isclose(t[-1], 5)
    assert np.isclose(x[-1], np.exp(t[-1]), atol=1e-3)


def test_rk4_test2_default():
    t, x = rk4_test2.run(ax=None)
    assert len(t) == len(x) == 51
    assert np.isclose(t[0], 0)
    assert np.isclose(x[0], 5)
    assert np.isclose(x[-1], t[-1] + 5)


def test_selftest_fps():
    fps = selftest.run_selftest(duration=0.1)
    assert fps > 0


def test_rk4_test3_default():
    t, x, y = rk4_test3.run(ax=None)
    assert t.shape == x.shape == y.shape
    assert len(t) == 1001
    assert np.isclose(t[0], 0)
    assert np.isclose(x[0], 5)
    assert np.isclose(y[0], 0)
    # check last step roughly matches analytical solution
    assert np.allclose([x[-1], y[-1]],
                       [5 * np.cos(t[-1]), -5 * np.sin(t[-1])],
                       atol=1e-6)
