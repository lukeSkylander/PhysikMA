import numpy as np
import matplotlib.pyplot as plt


def dx_dt(t, x):
    """Differential equation dx/dt = x."""
    return x


def runge_kutta_4(f, x0, t0, t_end, h):
    t_values = np.arange(t0, t_end + h, h)
    x_values = []
    x = x0
    for t in t_values:
        x_values.append(x)
        k1 = h * f(t, x)
        k2 = h * f(t + h / 2, x + k1 / 2)
        k3 = h * f(t + h / 2, x + k2 / 2)
        k4 = h * f(t + h, x + k3)
        x += (k1 + 2 * k2 + 2 * k3 + k4) / 6
    return t_values, np.array(x_values)


def run(ax=None):
    """Run a simple RK4 test solving dx/dt = x.

    If *ax* is provided, plot the result on that axes and return the computed
    values instead of opening a new window.
    """
    x0 = 1
    t0 = 0
    t_end = 5
    h = 0.1
    t_values, x_values = runge_kutta_4(dx_dt, x0, t0, t_end, h)
    x_analytical = np.exp(t_values)

    if ax is None:
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

    if ax is None:
        plt.tight_layout()
        plt.show()
    else:
        ax.figure.canvas.draw_idle()

    return t_values, x_values


if __name__ == "__main__":
    run()
