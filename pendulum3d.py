import numpy as np
import matplotlib.pyplot as plt


def rk4_step(f, t, state, h):
    k1 = h * f(t, state)
    k2 = h * f(t + h/2, state + k1/2)
    k3 = h * f(t + h/2, state + k2/2)
    k4 = h * f(t + h, state + k3)
    return state + (k1 + 2*k2 + 2*k3 + k4) / 6



def run(
    L=1.0,
    theta0=0.1,
    phi0=0.0,
    theta_dot0=0.0,
    phi_dot0=0.0,
    g=9.81,
    h=0.01,
    t_final=10.0,
    air_resistance=0.0,
    force_x=0.0,
    force_y=0.0,
    force_z=0.0,
    draw_mode=True,
    force_arrows=False,
    ax=None,
    plot=True,
):

    """Simulate a spherical pendulum with RK4 integration.

    The angles ``theta`` and ``phi`` are defined in spherical coordinates
    with ``theta`` measured from the vertical z-axis and ``phi`` the
    azimuthal angle. The full nonlinear equations are solved so large
    excursions are supported.

    Parameters
    ----------
    theta_dot0 : float, optional
        Initial polar angular velocity.
    phi_dot0 : float, optional
        Initial azimuthal angular velocity.
    force_x, force_y, force_z : float, optional
        Impulse components applied in the x, y and z directions at the
        start of the simulation. The values represent instantaneous
        changes in momentum (with a unit mass assumed) rather than
        continuous forces.
    draw_mode : bool, optional
        When ``True`` the trajectory is drawn as a line. If ``False`` a
        scatter plot is used instead.
    force_arrows : bool, optional
        Draw arrows for gravity (blue), tension (red) and any applied
        impulse (green) at the bob's final position. All arrows are
        normalized to the same length, so only their directions are
        depicted.
    """

    def derivative(t, state):
        theta, phi, theta_dot, phi_dot = state
        dtheta_dt = theta_dot
        dphi_dt = phi_dot

        dtheta_dot_dt = (
            np.sin(theta) * np.cos(theta) * phi_dot**2
            - (g / L) * np.sin(theta)
            - air_resistance * theta_dot * abs(theta_dot)
        )
        dphi_dot_dt = (
            -2 * theta_dot * phi_dot / np.tan(theta)
            - air_resistance * phi_dot * abs(phi_dot)
        )

        return np.array([dtheta_dt, dphi_dt, dtheta_dot_dt, dphi_dot_dt])

    t_values = np.arange(0, t_final + h, h)
    theta_vals = np.zeros_like(t_values)
    phi_vals = np.zeros_like(t_values)
    theta_dot_vals = np.zeros_like(t_values)
    phi_dot_vals = np.zeros_like(t_values)
    energy_vals = np.zeros_like(t_values)

    state = np.array([theta0, phi0, theta_dot0, phi_dot0])
    if force_x or force_y or force_z:
        # Project impulse components onto the theta/phi directions at t=0
        f_theta = (
            force_x * np.cos(theta0) * np.cos(phi0)
            + force_y * np.cos(theta0) * np.sin(phi0)
            + force_z * np.sin(theta0)
        )
        f_phi = -force_x * np.sin(phi0) + force_y * np.cos(phi0)
        state[2] += f_theta / L
        if np.abs(np.sin(theta0)) > 1e-8:
            state[3] += f_phi / (L * np.sin(theta0))

    theta_vals[0], phi_vals[0], theta_dot_vals[0], phi_dot_vals[0] = state

    def calc_energy(th, th_dot, ph_dot):
        kinetic = 0.5 * L**2 * (th_dot**2 + (np.sin(th)**2) * ph_dot**2)
        potential = g * L * (1 - np.cos(th))
        return kinetic + potential

    energy_vals[0] = calc_energy(theta_vals[0], theta_dot_vals[0],
                                 phi_dot_vals[0])

    for i in range(len(t_values) - 1):
        state = rk4_step(derivative, t_values[i], state, h)
        theta_vals[i+1], phi_vals[i+1], theta_dot_vals[i+1], phi_dot_vals[i+1] = state
        energy_vals[i+1] = calc_energy(theta_vals[i+1], theta_dot_vals[i+1],
                                       phi_dot_vals[i+1])

    if plot:
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection="3d")
        x = L * np.sin(theta_vals) * np.cos(phi_vals)
        y = L * np.sin(theta_vals) * np.sin(phi_vals)
        z = -L * np.cos(theta_vals)

        if draw_mode:
            ax.plot(x, y, z, color="white")
        else:
            ax.scatter(x, y, z, s=1)

        if force_arrows:
            theta_f = theta_vals[-1]
            phi_f = phi_vals[-1]
            theta_dot_f = theta_dot_vals[-1]
            phi_dot_f = phi_dot_vals[-1]

            # gravity vector
            g_vec = np.array([0.0, 0.0, -g])
            ax.quiver(
                x[-1],
                y[-1],
                z[-1],
                g_vec[0],
                g_vec[1],
                g_vec[2],
                color="blue",
                length=L / 2,
                normalize=True,
            )

            # tension (mass = 1)
            T = g * np.cos(theta_f) + L * (
                theta_dot_f**2 + (np.sin(theta_f)**2) * phi_dot_f**2
            )
            r_hat = np.array([
                np.sin(theta_f) * np.cos(phi_f),
                np.sin(theta_f) * np.sin(phi_f),
                -np.cos(theta_f),
            ])
            t_vec = -T * r_hat
            ax.quiver(
                x[-1],
                y[-1],
                z[-1],
                t_vec[0],
                t_vec[1],
                t_vec[2],
                color="red",
                length=L / 2,
                normalize=True,
            )

            if force_x or force_y or force_z:
                ax.quiver(
                    x[-1],
                    y[-1],
                    z[-1],
                    force_x,
                    force_y,
                    force_z,
                    color="green",
                    length=L / 2,
                    normalize=True,
                )

        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")
        ax.set_box_aspect([1, 1, 1])
        plt.show()
    return (t_values, theta_vals, phi_vals,
            theta_dot_vals, phi_dot_vals, energy_vals)


if __name__ == "__main__":
    run()
