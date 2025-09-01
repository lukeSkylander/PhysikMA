import numpy as np
import matplotlib.pyplot as plt
from rk4 import rk4_step
from energy_utils import pendulum_energy

def run(L=1.0, phi0=0.1, g=9.81, h=0.01, t_final=10.0,
        air_resistance=0.0, ax=None, plot=True):
    """Simulate a simple pendulum with RK4.

    Parameters
    ----------
    L : float
        Length of the pendulum in meters.
    phi0 : float
        Initial angle in radians.
    g : float
        Gravitational acceleration.
    h : float
        Integration step size.
    t_final : float
        End time of the simulation.
    air_resistance : float, optional
        Coefficient for quadratic air drag. ``0`` disables drag.

    When *plot* is True the results are plotted either on *ax* (if provided) or
    in a new window. Regardless of plotting, the arrays for time, angle,
    angular speed and total energy are returned so that callers can animate or
    further process the data.
    """

    def derivative(t, state):
        phi, omega = state
        dphidt = omega
        domega_dt = (-(g / L) * np.sin(phi)
                     - air_resistance * omega * np.abs(omega))
        return np.array([dphidt, domega_dt])

    t_values = np.arange(0, t_final + h, h)
    phi_values = np.zeros_like(t_values)
    omega_values = np.zeros_like(t_values)
    energy_values = np.zeros_like(t_values)

    state = np.array([phi0, 0.0])
    phi_values[0], omega_values[0] = state
    # Store the initial energy so the energy graph starts at the correct value
    energy_values[0] = pendulum_energy(phi_values[0], omega_values[0], L, g)

    for i in range(len(t_values) - 1):
        state = rk4_step(derivative, t_values[i], state, h)
        phi_values[i+1], omega_values[i+1] = state

        energy_values[i+1] = pendulum_energy(
            phi_values[i + 1], omega_values[i + 1], L, g
        )

    if plot:
        ax_in = ax
        if ax_in is None:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))
        else:
            ax1 = ax_in
            ax1.clear()
            ax2 = None

        # Pure sine wave for comparison
        w0 = np.sqrt(g / L)
        phi_sine = phi0 * np.sin(w0 * t_values)

        ax1.plot(t_values, phi_values, label='Simulation')
        ax1.plot(t_values, phi_sine, label='Pure sine wave')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('phi (rad)')
        ax1.set_title('Pendulum Angle')
        ax1.grid(True)
        ax1.legend()

        if ax2 is not None:
            ax2.plot(t_values, energy_values)
            ax2.set_xlabel('Time (s)')
            ax2.set_ylabel('Energy')
            ax2.set_title('Energy')
            ax2.grid(True)

        if ax_in is None:
            fig.tight_layout()
            plt.show()
        else:
            ax1.figure.canvas.draw_idle()

    return t_values, phi_values, omega_values, energy_values


if __name__ == "__main__":
    run()
