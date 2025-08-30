import numpy as np
import matplotlib.pyplot as plt
import warnings
from rk4 import rk4_step
from energy_utils import spherical_energy

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
    show_trajectory=True,
    show_vectors=False,
    ax=None,
    plot=True,
):

    """Simulate a spherical pendulum with RK4 integration.

    The angles ``theta`` and ``phi`` are defined in spherical coordinates
    with ``theta`` measured from the vertical z-axis and ``phi`` the
    azimuthal angle. The full nonlinear equations are solved so large
    excursions are supported.

    Notes
    -----
    The spherical formulation is singular when ``theta`` is exactly ``0`` or
    ``π``. If the initial angle ``theta0`` is within roughly ``1e-6`` of these
    values, the function automatically falls back to the Cartesian solver
    :func:`run_cartesian` and a warning is issued.

    Parameters
    ----------
    theta_dot0 : float, optional
        Initial polar angular velocity.
    phi_dot0 : float, optional
        Initial azimuthal angular velocity.
    force_x : float, optional
        Impulse component applied in the x direction at the start of the simulation (instantaneous change in momentum assuming unit mass).
    force_y : float, optional
        Impulse component applied in the y direction at the start of the simulation (instantaneous change in momentum assuming unit mass).
    force_z : float, optional
        Impulse component applied in the z direction at the start of the simulation (instantaneous change in momentum assuming unit mass).
    show_trajectory : bool, optional
        When ``True`` the trajectory is drawn if plotting is enabled. If
        ``False`` a scatter plot is used instead.
    show_vectors : bool, optional
        Draw arrows for gravity (blue), tension (red) and any applied impulse
        (green) at the bob's final position; all arrows are normalized to the
        same length so only their directions are depicted.
    """

    sin_theta0 = np.sin(theta0)
    if abs(sin_theta0) < 1e-6:
        warnings.warn(
            "theta0 is near a singular angle; falling back to Cartesian solver",
            RuntimeWarning,
        )
        result = run_cartesian(
            L=L,
            theta0=theta0,
            phi0=phi0,
            theta_dot0=theta_dot0,
            phi_dot0=phi_dot0,
            g=g,
            h=h,
            t_final=t_final,
            air_resistance=air_resistance,
            force_x=force_x,
            force_y=force_y,
            force_z=force_z,
            plot=plot,
        )
        (
            t_values,
            x_vals,
            y_vals,
            z_vals,
            vx_vals,
            vy_vals,
            vz_vals,
            energy_vals,
        ) = result
        theta_vals = np.arccos(-z_vals / L)
        phi_vals = np.arctan2(y_vals, x_vals)
        theta_dot_vals = (
            vx_vals * np.cos(theta_vals) * np.cos(phi_vals)
            + vy_vals * np.cos(theta_vals) * np.sin(phi_vals)
            - vz_vals * np.sin(theta_vals)
        ) / L
        sin_theta = np.sin(theta_vals)
        phi_dot_vals = np.zeros_like(sin_theta)
        mask = np.abs(sin_theta) > 1e-12
        phi_dot_vals[mask] = (
            -vx_vals[mask] * np.sin(phi_vals[mask])
            + vy_vals[mask] * np.cos(phi_vals[mask])
        ) / (L * sin_theta[mask])
        return (
            t_values,
            theta_vals,
            phi_vals,
            theta_dot_vals,
            phi_dot_vals,
            energy_vals,
        )

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
        state[3] += f_phi / (L * np.sin(theta0))

    theta_vals[0], phi_vals[0], theta_dot_vals[0], phi_dot_vals[0] = state

    energy_vals[0] = spherical_energy(
        theta_vals[0], theta_dot_vals[0], phi_dot_vals[0], L, g
    )

    for i in range(len(t_values) - 1):
        state = rk4_step(derivative, t_values[i], state, h)
        theta_vals[i+1], phi_vals[i+1], theta_dot_vals[i+1], phi_dot_vals[i+1] = state
        energy_vals[i + 1] = spherical_energy(
            theta_vals[i + 1], theta_dot_vals[i + 1], phi_dot_vals[i + 1], L, g
        )

    ax_in = ax
    if plot:
        if ax_in is None:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection="3d")
        x = L * np.sin(theta_vals) * np.cos(phi_vals)
        y = L * np.sin(theta_vals) * np.sin(phi_vals)
        z = -L * np.cos(theta_vals)

        if show_trajectory:
            ax.plot(x, y, z, color="white")

        if show_vectors:
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
        if ax_in is None:
            plt.show()
        else:
            ax.figure.canvas.draw_idle()
    return (t_values, theta_vals, phi_vals,
            theta_dot_vals, phi_dot_vals, energy_vals)


def run_cartesian(
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
    plot=True,
):
    """Simulate a spherical pendulum using Cartesian coordinates.

    The Cartesian formulation avoids the singularities that occur in the
    spherical equations when the pendulum approaches the vertical axis. The
    initial conditions are still specified using ``theta`` and ``phi`` but the
    integration is performed on the ``x``, ``y`` and ``z`` coordinates subject
    to the constraint ``x**2 + y**2 + z**2 = L**2``.
    """

    # Convert initial conditions to Cartesian coordinates
    x0 = L * np.sin(theta0) * np.cos(phi0)
    y0 = L * np.sin(theta0) * np.sin(phi0)
    z0 = -L * np.cos(theta0)

    vx0 = L * (
        theta_dot0 * np.cos(theta0) * np.cos(phi0)
        - phi_dot0 * np.sin(theta0) * np.sin(phi0)
    )
    vy0 = L * (
        theta_dot0 * np.cos(theta0) * np.sin(phi0)
        + phi_dot0 * np.sin(theta0) * np.cos(phi0)
    )
    vz0 = -L * theta_dot0 * np.sin(theta0)

    state = np.array([x0, y0, z0, vx0, vy0, vz0])
    # Apply impulses as instantaneous velocity changes
    state[3] += force_x
    state[4] += force_y
    state[5] += force_z

    t_values = np.arange(0, t_final + h, h)
    x_vals = np.zeros_like(t_values)
    y_vals = np.zeros_like(t_values)
    z_vals = np.zeros_like(t_values)
    vx_vals = np.zeros_like(t_values)
    vy_vals = np.zeros_like(t_values)
    vz_vals = np.zeros_like(t_values)
    energy_vals = np.zeros_like(t_values)

    x_vals[0], y_vals[0], z_vals[0], vx_vals[0], vy_vals[0], vz_vals[0] = state

    def derivative(t, st):
        x, y, z, vx, vy, vz = st
        r = np.array([x, y, z])
        v = np.array([vx, vy, vz])
        speed_sq = np.dot(v, v)

        accel = np.array([0.0, 0.0, -g]) - ((speed_sq - g * z) / L**2) * r
        if air_resistance:
            accel -= air_resistance * v * np.linalg.norm(v)
        return np.array([vx, vy, vz, *accel])

    def calc_energy(x, y, z, vx, vy, vz):
        kinetic = 0.5 * (vx**2 + vy**2 + vz**2)
        potential = g * (z + L)
        return kinetic + potential

    energy_vals[0] = calc_energy(*state)

    for i in range(len(t_values) - 1):
        state = rk4_step(derivative, t_values[i], state, h)
        # Enforce constraints after each step
        r = state[:3]
        v = state[3:]
        r = L * r / np.linalg.norm(r)
        v -= (np.dot(r, v) / L**2) * r
        state[:3], state[3:] = r, v
        x_vals[i + 1], y_vals[i + 1], z_vals[i + 1], vx_vals[i + 1], vy_vals[i + 1], vz_vals[i + 1] = state
        energy_vals[i + 1] = calc_energy(*state)

    if plot:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.plot(x_vals, y_vals, z_vals, color="white")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")
        ax.set_box_aspect([1, 1, 1])
        plt.show()

    return (
        t_values,
        x_vals,
        y_vals,
        z_vals,
        vx_vals,
        vy_vals,
        vz_vals,
        energy_vals,
    )


if __name__ == "__main__":
    run()
