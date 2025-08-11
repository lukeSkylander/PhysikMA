import numpy as np
import matplotlib.pyplot as plt

# Parameters
g = 9.81  # m/s²
L = 1.0    # m
m = 1.0    # kg
Phi_max_linear = 0.1  # Small angle (radians)
Phi_max_nonlinear = 1.0  # Larger angle (radians)
t_final = 10.0  # Simulation time (seconds)
h = 0.01  # Step size (small for accuracy)

# Define ODEs
def derivative_linear(t, state):
    phi, omega = state
    dphidt = omega
    domega_dt = -(g / L) * phi  # Linear approximation: sin(phi) ≈ phi
    return np.array([dphidt, domega_dt])

def derivative_nonlinear(t, state):
    phi, omega = state
    dphidt = omega
    domega_dt = -(g / L) * np.sin(phi)  # Full nonlinear term
    return np.array([dphidt, domega_dt])

# RK4 Solver
def rk4_step(f, t, state, h):
    k1 = h * f(t, state)
    k2 = h * f(t + h/2, state + k1/2)
    k3 = h * f(t + h/2, state + k2/2)
    k4 = h * f(t + h, state + k3)
    return state + (k1 + 2*k2 + 2*k3 + k4) / 6

# Simulation function
def simulate_pendulum(derivative, phi0, omega0=0.0):
    t_values = np.arange(0, t_final + h, h)
    phi_values = np.zeros_like(t_values)
    omega_values = np.zeros_like(t_values)
    energy_values = np.zeros_like(t_values)
    
    state = np.array([phi0, omega0])
    phi_values[0], omega_values[0] = state
    
    for i in range(len(t_values) - 1):
        state = rk4_step(derivative, t_values[i], state, h)
        phi_values[i+1], omega_values[i+1] = state
        
        # Compute energy
        kinetic = 0.5 * m * L**2 * omega_values[i+1]**2
        potential = m * g * L * (1 - np.cos(phi_values[i+1]))
        energy_values[i+1] = kinetic + potential
    
    return t_values, phi_values, omega_values, energy_values

# Run simulations
# Linear case (small angle)
t_linear, phi_linear, omega_linear, energy_linear = simulate_pendulum(
    derivative_linear, Phi_max_linear
)

# Nonlinear case
t_nonlinear, phi_nonlinear, omega_nonlinear, energy_nonlinear = simulate_pendulum(
    derivative_nonlinear, Phi_max_nonlinear
)

# Analytical solution for linear case (phi(t) = Phi_max * cos(w0*t))
w0 = np.sqrt(g / L)
phi_analytical = Phi_max_linear * np.cos(w0 * t_linear)

# Plot results
plt.figure(figsize=(14, 10))

# Plot linear case: Numerical vs Analytical
plt.subplot(2, 2, 1)
plt.plot(t_linear, phi_linear, 'b-', label='Numerical (RK4)')
plt.plot(t_linear, phi_analytical, 'r--', label='Analytical: $\phi_0 \cos(\omega_0 t)$')
plt.xlabel('Time (s)')
plt.ylabel('$\phi(t)$ (rad)')
plt.title('Linear Pendulum ($|\phi| \ll 1$)')
plt.legend()
plt.grid(True)

# Plot nonlinear case: Angular displacement
plt.subplot(2, 2, 2)
plt.plot(t_nonlinear, phi_nonlinear, 'g-', label='Numerical (RK4)')
plt.xlabel('Time (s)')
plt.ylabel('$\phi(t)$ (rad)')
plt.title('Nonlinear Pendulum')
plt.grid(True)

# Plot energy conservation
plt.subplot(2, 2, 3)
plt.plot(t_linear, energy_linear, 'm-', label='Linear Case')
plt.plot(t_nonlinear, energy_nonlinear, 'c-', label='Nonlinear Case')
plt.xlabel('Time (s)')
plt.ylabel('Total Energy (J)')
plt.title('Energy Conservation')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

# Print energy stability
energy_change_linear = np.max(energy_linear) - np.min(energy_linear)
energy_change_nonlinear = np.max(energy_nonlinear) - np.min(energy_nonlinear)
print(f"Linear case energy fluctuation: {energy_change_linear:.2e} J")
print(f"Nonlinear case energy fluctuation: {energy_change_nonlinear:.2e} J")
