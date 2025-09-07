"""Export 3D pendulum projections to A4-sized SVG files."""

import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pendulum3d

A4_SIZE = (8.27, 11.69)  # inches (210mm × 297mm)


def export_projections(out_floor='floor_projection.svg', out_wall_yz='wall_yz_projection.svg',
                      out_wall_xz='wall_xz_projection.svg', trajectory_data=None, **kwargs):
    """
    Simulate a 3D pendulum and save floor and wall projections as SVG.
    
    Args:
        out_floor: Output filename for floor projection SVG (X-Y plane)
        out_wall_yz: Output filename for YZ wall projection SVG
        out_wall_xz: Output filename for XZ wall projection SVG
        trajectory_data: Optional dict with actual trajectory data from simulation
                        Should contain 'x', 'y', 'z' arrays
        **kwargs: Simulation parameters (used if trajectory_data is None)
    """
    
    if trajectory_data is not None:
        # Use actual trajectory data from the running simulation (includes impulses)
        x = trajectory_data['x']
        y = trajectory_data['y'] 
        z = trajectory_data['z']
        print("Using actual simulation trajectory data (includes impulses)")
    else:
        # Fallback: Run fresh simulation with initial parameters only
        print("Running fresh simulation (no impulse effects)")
        _, theta, phi, theta_dot, phi_dot, _ = pendulum3d.run(plot=False, **kwargs)
        L = kwargs.get('L', 1.0)
        x = L * np.sin(theta) * np.cos(phi)
        y = L * np.sin(theta) * np.sin(phi)
        z = -L * np.cos(theta)

    # Clean white background style
    with plt.style.context('default'):
        # Floor projection (X-Y plane)
        fig, ax = plt.subplots(figsize=A4_SIZE)
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        # Remove all axes, ticks, and labels for clean output
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        # Plot trajectory
        ax.plot(x, y, color='black', linewidth=2)
        ax.set_aspect('equal', adjustable='box')
        
        # Add start and end markers
        ax.plot(x[0], y[0], 'go', markersize=10, label='Start', zorder=5)
        ax.plot(x[-1], y[-1], 'ro', markersize=10, label='End', zorder=5)
        
        # Add title at the top
        ax.text(0.5, 0.95, 'Floor Projection (X-Y Plane)', 
                transform=ax.transAxes, fontsize=16, fontweight='bold', 
                ha='center', va='top')
        
        # Adjust layout to remove extra whitespace
        fig.tight_layout()
        fig.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05)
        
        fig.savefig(out_floor, format='svg', bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close(fig)

        # YZ wall projection (side view)
        fig, ax = plt.subplots(figsize=A4_SIZE)
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        # Remove all axes, ticks, and labels for clean output
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        # Plot trajectory
        ax.plot(y, z, color='black', linewidth=2)
        ax.set_aspect('equal', adjustable='box')
        
        # Add start and end markers
        ax.plot(y[0], z[0], 'go', markersize=10, label='Start', zorder=5)
        ax.plot(y[-1], z[-1], 'ro', markersize=10, label='End', zorder=5)
        
        # Add title at the top
        ax.text(0.5, 0.95, 'Wall Projection (Y-Z Plane)', 
                transform=ax.transAxes, fontsize=16, fontweight='bold', 
                ha='center', va='top')
        
        # Adjust layout to remove extra whitespace
        fig.tight_layout()
        fig.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05)
        
        fig.savefig(out_wall_yz, format='svg', bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close(fig)

        # XZ wall projection (front view)
        fig, ax = plt.subplots(figsize=A4_SIZE)
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        # Remove all axes, ticks, and labels for clean output
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        # Plot trajectory
        ax.plot(x, z, color='black', linewidth=2)
        ax.set_aspect('equal', adjustable='box')
        
        # Add start and end markers
        ax.plot(x[0], z[0], 'go', markersize=10, label='Start', zorder=5)
        ax.plot(x[-1], z[-1], 'ro', markersize=10, label='End', zorder=5)
        
        # Add title at the top
        ax.text(0.5, 0.95, 'Wall Projection (X-Z Plane)', 
                transform=ax.transAxes, fontsize=16, fontweight='bold', 
                ha='center', va='top')
        
        # Adjust layout to remove extra whitespace
        fig.tight_layout()
        fig.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05)
        
        fig.savefig(out_wall_xz, format='svg', bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close(fig)
    
    print(f"Exported floor projection to: {out_floor}")
    print(f"Exported YZ wall projection to: {out_wall_yz}")
    print(f"Exported XZ wall projection to: {out_wall_xz}")


def main():
    parser = argparse.ArgumentParser(description='Export pendulum projections to SVG.')
    parser.add_argument('--out-floor', default='floor_projection.svg', help='Output SVG for floor projection')
    parser.add_argument('--out-wall-yz', default='wall_yz_projection.svg', help='Output SVG for YZ wall projection')
    parser.add_argument('--out-wall-xz', default='wall_xz_projection.svg', help='Output SVG for XZ wall projection')
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
        out_wall_yz=args.out_wall_yz,
        out_wall_xz=args.out_wall_xz,
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
