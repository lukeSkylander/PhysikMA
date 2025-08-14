## Timline
    This File contains a timeline of the commits made to this Repository. A minus or plus sign in front of Code implies deletion and creation of code.

# 16 Jun: Difference not plotted in ODE comparison
Problem: ode_solution_comparison.py computes a difference between the numerical and analytical solutions but plots the raw solution instead
Solution: In `ode_solution_comparison.py`, update the `plt.plot` call near line 27 to use the `difference` variable instead of `sol.y[0]`.Keep the label indicating the plotted quantity.
Code Changes:
 difference = sol.y[0] - analytical
    
 # Plot the difference
-plt.plot(t_eval, sol.y[0], label=r'$x_{solution}(t) - e^t$')
+plt.plot(t_eval, difference, label=r'$x_{solution}(t) - e^t$')
 plt.axhline(0, color='gray', linestyle='--')
 plt.xlabel('t')
 plt.ylabel('Difference')

# 16 Jun: Add tkinter UI for simulations
    Objective: Design a GUI to simulate and visualize the motion of a pendulum. The user can change physical parameters (length, gravity, angle, mass), view a live pendulum animation, see a plot of angular displacement over time, and access real-time calculated outputs and descriptions.
    Problems:
    1. Backend configured too late in ui.py: 
      The backend is set using matplotlib.use("TkAgg") after importing matplotlib.pyplot. Lines 1‑11 show the import order and backend call
    2. Unnecessary nonlocal in update_graph:
      update_graph declares nonlocal ani, pendulum_data, but it never reassigns these variables—only reads or mutates them.
    3. Multiple legacy scripts cause confusion
      Files such as RK4 Test 3.py, RK4Test.py, and RK4Test2.py remain alongside the newer rk4_test*.py modules. They appear to contain older versions of the same examples.
