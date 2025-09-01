#!/usr/bin/env python3
"""
Test script to verify PhysikSim simulation integrity after UI modernization.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_pendulum_simulation():
    """Test that the pendulum simulation produces expected results."""
    try:
        import pendulum as mod
        import numpy as np
        
        # Test parameters
        L = 1.0
        phi0 = np.radians(30)  # 30 degrees
        g = 9.81
        h = 0.001
        t_final = 5.0
        air_resistance = 0.0
        
        # Run simulation
        t, phi, omega, energy = mod.run(
            L=L,
            phi0=phi0,
            g=g,
            h=h,
            t_final=t_final,
            air_resistance=air_resistance,
            plot=False,
        )
        
        # Verify results
        assert len(t) > 0, "Time array should not be empty"
        assert len(phi) == len(t), "Angle array should match time array length"
        assert len(omega) == len(t), "Omega array should match time array length"
        assert len(energy) == len(t), "Energy array should match time array length"
        
        # Check conservation of energy (with small tolerance for air resistance)
        energy_variation = np.max(energy) - np.min(energy)
        assert energy_variation < 0.1, f"Energy should be conserved (variation: {energy_variation})"
        
        # Check that pendulum oscillates
        assert np.max(np.abs(phi)) > 0.1, "Pendulum should oscillate"
        
        # Check that simulation runs for expected time
        assert abs(t[-1] - t_final) < 0.1, f"Simulation should run for {t_final}s, got {t[-1]}s"
        
        print("✅ 2D Pendulum simulation integrity verified!")
        return True
        
    except Exception as e:
        print(f"❌ 2D Pendulum simulation test failed: {e}")
        return False

def test_pendulum3d_simulation():
    """Test that the 3D pendulum simulation produces expected results."""
    try:
        import pendulum3d as mod
        import numpy as np
        
        # Test parameters
        L = 1.0
        theta0 = np.radians(30)
        phi0 = np.radians(45)
        phi_dot0 = np.radians(10)
        g = 9.81
        h = 0.001
        t_final = 3.0
        air_resistance = 0.0
        
        # Run simulation
        (t, theta, psi, theta_dot, phi_dot, energy) = mod.run(
            L=L,
            theta0=theta0,
            phi0=phi0,
            phi_dot0=phi_dot0,
            g=g,
            h=h,
            t_final=t_final,
            air_resistance=air_resistance,
            force_x=0.0,
            force_y=0.0,
            force_z=0.0,
            plot=False,
        )
        
        # Verify results
        assert len(t) > 0, "Time array should not be empty"
        assert len(theta) == len(t), "Theta array should match time array length"
        assert len(psi) == len(t), "Psi array should match time array length"
        assert len(energy) == len(t), "Energy array should match time array length"
        
        # Check conservation of energy
        energy_variation = np.max(energy) - np.min(energy)
        assert energy_variation < 0.1, f"Energy should be conserved (variation: {energy_variation})"
        
        # Check that pendulum moves
        assert np.max(np.abs(theta)) > 0.1, "Pendulum should move in theta"
        
        # Check that simulation runs for expected time
        assert abs(t[-1] - t_final) < 0.1, f"Simulation should run for {t_final}s, got {t[-1]}s"
        
        print("✅ 3D Pendulum simulation integrity verified!")
        return True
        
    except Exception as e:
        print(f"❌ 3D Pendulum simulation test failed: {e}")
        return False

def test_timing_accuracy():
    """Test that simulation timing matches user settings."""
    try:
        import pendulum as mod
        import numpy as np
        
        # Test different time settings
        time_settings = [1.0, 5.0, 10.0, 20.0]
        
        for t_final in time_settings:
            t, phi, omega, energy = mod.run(
                L=1.0,
                phi0=np.radians(30),
                g=9.81,
                h=0.001,
                t_final=t_final,
                air_resistance=0.0,
                plot=False,
            )
            
            actual_time = t[-1]
            time_error = abs(actual_time - t_final)
            
            assert time_error < 0.1, f"Time setting {t_final}s should match actual time {actual_time}s"
            
        print("✅ Simulation timing accuracy verified!")
        return True
        
    except Exception as e:
        print(f"❌ Timing accuracy test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing PhysikSim simulation integrity...")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Run tests
    all_tests_passed &= test_pendulum_simulation()
    all_tests_passed &= test_pendulum3d_simulation()
    all_tests_passed &= test_timing_accuracy()
    
    print("=" * 50)
    if all_tests_passed:
        print("🎉 All simulation integrity tests passed!")
        print("✅ The UI modernization has not affected simulation accuracy")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the simulation code.")
        sys.exit(1)
