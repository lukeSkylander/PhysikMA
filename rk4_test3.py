import numpy as np
import matplotlib.pyplot as plt
from rk4 import rk4_step

def derivative(t, state):
    x, y = state
    dxdt = y
    dydt = -x
    return np.array([dxdt, dydt])


def run(ax=None):
    """Third RK4 test solving a simple harmonic oscillator.

    If *ax* is provided, plot the x-component on that axes and return the
    computed arrays. Otherwise a new window with three subplots is created.
    """
    t0 = 0.0
    initial_state = np.array([5.0, 0.0])
    h = 0.01
    t_final = 10.0
    n_steps = int((t_final - t0) / h)

    t_values = np.zeros(n_steps + 1)
    x_values = np.zeros(n_steps + 1)
    y_values = np.zeros(n_steps + 1)
    t_values[0] = t0
    x_values[0], y_values[0] = initial_state

    state = initial_state.copy()
    for i in range(n_steps):
        state = rk4_step(derivative, t_values[i], state, h)
        t_values[i+1] = t_values[i] + h
        x_values[i+1], y_values[i+1] = state

    x_analytical = 5 * np.cos(t_values)
    y_analytical = -5 * np.sin(t_values)

    x_error = x_values - x_analytical
    y_error = y_values - y_analytical

    ax_in = ax
    if ax_in is None:
        fig = plt.figure(figsize=(12, 8))
        ax1 = fig.add_subplot(2, 2, 1)
        ax2 = fig.add_subplot(2, 2, 2)
        ax3 = fig.add_subplot(2, 2, 3)
    else:
        ax1 = ax_in
        ax1.clear()
        ax2 = ax3 = None

    ax1.plot(t_values, x_values, 'b.-', label='RK4 Solution')
    ax1.plot(t_values, x_analytical, 'r--', label='Analytical')
    ax1.set_xlabel('t')
    ax1.set_ylabel('x(t)')
    ax1.set_title('Solution for x(t) = 5cos(t)')
    ax1.legend()
    ax1.grid(True)

    if ax2 is not None:
        ax2.plot(t_values, y_values, 'g.-', label='RK4 Solution')
        ax2.plot(t_values, y_analytical, 'm--', label='Analytical')
        ax2.set_xlabel('t')
        ax2.set_ylabel('y(t)')
        ax2.set_title('Solution for y(t) = -5sin(t)')
        ax2.legend()
        ax2.grid(True)

        ax3.plot(t_values, x_error, 'c.-', label='x Error')
        ax3.plot(t_values, y_error, 'y.-', label='y Error')
        ax3.set_xlabel('t')
        ax3.set_ylabel('Error')
        ax3.set_title('Numerical Error')
        ax3.legend()
        ax3.grid(True)

    if ax_in is None:
        fig.tight_layout()
        plt.show()
    else:
        ax1.figure.canvas.draw_idle()

    return t_values, x_values, y_values


if __name__ == "__main__":
    run()
