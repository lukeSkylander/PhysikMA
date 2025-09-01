import numpy as np
import matplotlib.pyplot as plt
from rk4 import rk4_step

def derivative(t, x):
    return 1


def run(ax=None):
    """Second RK4 test solving dx/dt=1.

    If *ax* is provided, plot the solution on that axes and return the data
    arrays for further use. Otherwise a new window with two subplots is shown.
    """
    t0 = 0.0
    x0 = 5.0
    h = 0.1
    t_final = 5.0
    n_steps = int((t_final - t0) / h)

    t_values = np.zeros(n_steps + 1)
    x_values = np.zeros(n_steps + 1)
    t_values[0] = t0
    x_values[0] = x0

    for i in range(n_steps):
        x_values[i+1] = rk4_step(derivative, t_values[i], x_values[i], h)
        t_values[i+1] = t_values[i] + h

    analytical_x = t_values + 5
    error = x_values - analytical_x

    ax_in = ax
    if ax_in is None:
        fig = plt.figure(figsize=(10, 6))
        ax1 = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2)
    else:
        ax1 = ax_in
        ax1.clear()
        ax2 = None

    ax1.plot(t_values, x_values, 'b.-', label='RK4 Solution')
    ax1.plot(t_values, analytical_x, 'r--', label='Analytical Solution')
    ax1.set_xlabel('t')
    ax1.set_ylabel('x(t)')
    ax1.set_title('Solution of dx/dt = 1')
    ax1.legend()
    ax1.grid(True)

    if ax2 is not None:
        ax2.plot(t_values, error, 'g.-', label='Numerical Error')
        ax2.set_xlabel('t')
        ax2.set_ylabel('Error (x_numerical - (t + 5))')
        ax2.set_title('Error Verification')
        ax2.legend()
        ax2.grid(True)

    if ax_in is None:
        fig.tight_layout()
        plt.show()
    else:
        ax1.figure.canvas.draw_idle()

    max_error = np.max(np.abs(error))
    if __name__ == "__main__":
        print(f"Maximum error: {max_error:.2e}")

    return t_values, x_values


if __name__ == "__main__":
    run()
