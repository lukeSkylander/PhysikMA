# PhysikSim
This project contains small simulations and demos used for my Maturaarbeit. Most examples rely on the Runge–Kutta method to solve simple ordinary differential equations.

## Running tests

The test suite requires `numpy`, `matplotlib` and `pytest`. After installing
these dependencies you can execute all tests with:

```bash
pytest
```

This repository contains several small scripts demonstrating the Runge-Kutta
(RK4) method. The files `rk4_test1.py`, `rk4_test2.py` and `rk4_test3.py`
are the current examples used for experimentation.


## Prerequisites

- **Python** 3.8 or newer. The examples were tested with Python 3.11.
- The Python modules **numpy** and **matplotlib** must be installed.
- **tkinter** is required for the GUI contained in `ui.py` (usually included with standard Python installations).

Install the dependencies with:

```bash
pip install numpy matplotlib
```

## Running the GUI

The main entry point is `ui.py`. Start it from the repository root with:

```bash
python3 ui.py
```

A window will open with a dropdown to choose one of the RK4 tests or one of the pendulum simulations. When the "Pendulum" option is selected, sliders become active which allow adjusting the pendulum length `L`, the initial polar angle `theta0` (specified in degrees), gravity `g`, the integrator step size `h`, an optional air resistance coefficient, and the animation speed. The "3D Pendulum" entry exposes an additional slider for the azimuth angle `psi0` and shows a rotatable 3D animation. Impulses can be passed to `pendulum3d.run` via the `force_x`, `force_y` and `force_z` parameters (treated as instantaneous changes in momentum rather than continuous forces). Choose which variable to plot (angle, angular velocity, angular acceleration or energy) from the second dropdown and press **Run** to update the animation and plot. The pendulum simulations use the full nonlinear equations (optionally including air drag) so large-angle motion is simulated accurately.

Note that the spherical formulation of the 3D pendulum becomes singular when the
initial polar angle `theta0` is exactly `0°` or `180°`. In these cases the GUI
and the `pendulum3d.run` function automatically fall back to a Cartesian solver
which avoids the singularity but produces equivalent results.

## Running the example modules

All demonstration scripts can also be executed individually. The most commonly used are:

```bash
python3 rk4_test1.py
python3 rk4_test2.py
python3 rk4_test3.py
python3 pendulum.py
python3 pendulum3d.py
python3 save_projection_svg.py
```

Each script will open its own matplotlib window with the corresponding plots.
`save_projection_svg.py` instead saves SVG files of the floor and wall
projections on A4-sized pages.

### Legacy examples

Additional, optional demo scripts are kept in `examples/legacy/`:

- `2D_P-KleineWinkel.py` compares the small-angle approximation with the full
  nonlinear pendulum model using RK4.
- `ode_solution_comparison.py` solves a simple differential equation with
  SciPy and plots the deviation from the analytical solution.

These files are provided for reference only and are not used by the main
modules or tests.

## License
This project is licensed under the [MIT License](LICENSE).
