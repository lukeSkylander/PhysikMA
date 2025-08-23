"""Export 3D pendulum projections to A4-sized SVG files."""

import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pendulum3d

A4_SIZE = (8.27, 11.69)  # inches (210mm × 297mm)


def export_projections(out_floor='floor_projection.svg', out_wall='wall_projection.svg', **kwargs):
    """Simulate a 3D pendulum and save floor and wall projections as SVG."""
    _, theta, phi, theta_dot, phi_dot, _ = pendulum3d.run(plot=False, **kwargs)
    L = kwargs.get('L', 1.0)
    x = L * np.sin(theta) * np.cos(phi)
    y = L * np.sin(theta) * np.sin(phi)
    z = -L * np.cos(theta)

    with plt.style.context('default'):
        # Floor projection (x-y plane)
        fig, ax = plt.subplots(figsize=A4_SIZE)
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        ax.plot(x, y, color='black')
        ax.set_aspect('equal', adjustable='box')
        ax.axis('off')
        fig.savefig(out_floor, format='svg')
        plt.close(fig)

        # Wall projection (y-z plane)
        fig, ax = plt.subplots(figsize=A4_SIZE)
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        ax.plot(y, z, color='black')
        ax.set_aspect('equal', adjustable='box')
        ax.axis('off')
        fig.savefig(out_wall, format='svg')
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description='Export pendulum projections to SVG.')
    parser.add_argument('--out-floor', default='floor_projection.svg', help='Output SVG for floor projection')
    parser.add_argument('--out-wall', default='wall_projection.svg', help='Output SVG for wall projection')
    parser.add_argument('--L', type=float, default=1.0, help='Pendulum length')
    parser.add_argument('--theta0', type=float, default=0.1, help='Initial polar angle (rad)')
    parser.add_argument('--phi0', type=float, default=0.0, help='Initial azimuth angle (rad)')
    parser.add_argument('--theta-dot0', type=float, default=0.0, help='Initial polar angular velocity')
    parser.add_argument('--phi-dot0', type=float, default=0.0, help='Initial azimuth angular velocity')
    parser.add_argument('--g', type=float, default=9.81, help='Gravitational acceleration')
    parser.add_argument('--h', type=float, default=0.01, help='Time step')
    parser.add_argument('--t-final', type=float, default=10.0, help='Simulation duration')
    parser.add_argument('--air-resistance', type=float, default=0.0, help='Air resistance coefficient')
    parser.add_argument('--force-x', type=float, default=0.0, help='Impulse along x')
    parser.add_argument('--force-y', type=float, default=0.0, help='Impulse along y')
    parser.add_argument('--force-z', type=float, default=0.0, help='Impulse along z')
    args = parser.parse_args()
    export_projections(
        out_floor=args.out_floor,
        out_wall=args.out_wall,
        L=args.L,
        theta0=args.theta0,
        phi0=args.phi0,
        theta_dot0=args.theta_dot0,
        phi_dot0=args.phi_dot0,
        g=args.g,
        h=args.h,
        t_final=args.t_final,
        air_resistance=args.air_resistance,
        force_x=args.force_x,
        force_y=args.force_y,
        force_z=args.force_z,
    )


if __name__ == '__main__':
    main()
