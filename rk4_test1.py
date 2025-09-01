import numpy as np
import matplotlib.pyplot as plt
from rk4 import rk4_step

def dx_dt(t, x):
    """Differential equation dx/dt = x."""
    return x


def run(ax=None):
    """Run a simple RK4 test solving dx/dt = x.

    If *ax* is provided, plot the result on that axes and return the computed
    values instead of opening a new window.
    """
    x0 = 1
    t0 = 0
    t_end = 5
    h = 0.1
    n_steps = int((t_end - t0) / h)

    t_values = np.zeros(n_steps + 1)
    x_values = np.zeros(n_steps + 1)
    t_values[0] = t0
    x_values[0] = x0

    for i in range(n_steps):
        x_values[i + 1] = rk4_step(dx_dt, t_values[i], x_values[i], h)
        t_values[i + 1] = t_values[i] + h

    x_analytical = np.exp(t_values)

    ax_in = ax
    if ax_in is None:
        _, ax = plt.subplots()
    else:
        ax.clear()

    ax.plot(t_values, x_values, label="Runge-Kutta 4 (Numerical)", marker='o')
    ax.plot(t_values, x_analytical, label="Analytical Solution", linestyle='--')
    ax.set_xlabel("t")
    ax.set_ylabel("x(t)")
    ax.set_title("Runge-Kutta 4 vs Analytical Solution")
    ax.legend()
    ax.grid(True)

    if ax_in is None:
        plt.tight_layout()
        plt.show()
    else:
        ax.figure.canvas.draw_idle()

    return t_values, x_values


if __name__ == "__main__":
    run()
