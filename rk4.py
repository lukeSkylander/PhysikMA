"""Runge-Kutta 4 integration utilities."""

from __future__ import annotations


def rk4_step(f, t, state, h):
    """Advance *state* by one RK4 step.

    Parameters
    ----------
    f : callable
        Function returning the derivative of *state* with respect to time,
        called as ``f(t, state)``.
    t : float
        Current time.
    state : array_like or float
        Current state value.
    h : float
        Step size.

    Returns
    -------
    array_like or float
        Updated state after one RK4 step.
    """
    k1 = h * f(t, state)
    k2 = h * f(t + h / 2, state + k1 / 2)
    k3 = h * f(t + h / 2, state + k2 / 2)
    k4 = h * f(t + h, state + k3)
    return state + (k1 + 2 * k2 + 2 * k3 + k4) / 6
