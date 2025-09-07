import numpy as np


def pendulum_energy(phi, omega, L, g):
    """Return total mechanical energy of a simple pendulum.

    Parameters
    ----------
    phi : array_like
        Angular displacement in radians.
    omega : array_like
        Angular velocity in radians per second.
    L : float
        Pendulum length in meters.
    g : float
        Gravitational acceleration in m/s^2.
    """
    kinetic = 0.5 * L**2 * np.asarray(omega) ** 2
    potential = g * L * (1 - np.cos(phi))
    return kinetic + potential


def spherical_energy(theta, theta_dot, phi_dot, L, g):
    """Return energy of a spherical pendulum in spherical coordinates."""
    sin_theta = np.sin(theta)
    kinetic = 0.5 * L**2 * (theta_dot ** 2 + (sin_theta ** 2) * phi_dot ** 2)
    potential = g * L * (1 - np.cos(theta))
    return kinetic + potential
