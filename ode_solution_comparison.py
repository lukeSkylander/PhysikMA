
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Define the differential equation: dx/dt = x
def ode(t, x):
    return x

# Initial condition x(0) = 1
x0 = [1]

# Time range
t_span = (0, 2)
t_eval = np.linspace(*t_span, 400)

# Solve the ODE
sol = solve_ivp(ode, t_span, x0, t_eval=t_eval)

# Analytical solution e^t
analytical = np.exp(t_eval)

# Difference between numerical and analytical solutions
difference = sol.y[0] - analytical

# Plot the difference
plt.plot(t_eval, difference, label=r'$x_{solution}(t) - e^t$')
plt.axhline(0, color='gray', linestyle='--')
plt.xlabel('t')
plt.ylabel('Difference')
plt.title('Numerical vs Analytical Solution')
plt.legend()
plt.grid(True)
plt.show()
