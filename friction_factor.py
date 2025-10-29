import math

# Given values
epsilon = 0.00085  # ft (roughness for cast iron)
D = 6.065/12  # ft (3.830 inches)
V = 7.077 # ft/s
Re = 337437.14

# Calculate relative roughness
relative_roughness = epsilon / D
print(f"Pipe diameter D = {D:.6f} ft = {D * 12:.4f} in")
print(f"Velocity V = {V:.6f} ft/s")
print(f"Roughness ε = {epsilon} ft")
print(f"Relative roughness ε/D = {relative_roughness:.6f}")
print()

# Colebrook-White equation: 1/√f = -2.0 log(ε/D / 3.7 + 2.51 / (Re√f))
def solve_friction_factor(Re, tolerance=1e-8, max_iterations=100):
    """
    Solve for friction factor f given Reynolds number Re
    Uses fixed-point iteration
    """
    # Initial guess for f
    f = 0.02
    
    for _ in range(max_iterations):
        # Rearrange Colebrook equation to solve for f iteratively
        # 1/√f = -2.0 log(ε/D / 3.7 + 2.51 / (Re√f))
        # √f = 1 / (-2.0 log(...))
        # f = 1 / (-2.0 log(...))^2
        
        sqrt_f = math.sqrt(f)
        log_term = relative_roughness / 3.7 + 2.51 / (Re * sqrt_f)
        f_new = 1 / (-2.0 * math.log10(log_term))**2
        
        # Check convergence
        if abs(f_new - f) < tolerance:
            return f_new
        
        f = f_new
    
    print(f"Warning: Did not converge after {max_iterations} iterations")
    return f

# Given Reynolds number

# Solve for friction factor
f = solve_friction_factor(Re)

print(f"Given:")
print(f"  Reynolds Number (Re) = {Re}")
print()
print(f"Solution:")
print(f"  Friction factor (f) = {f:.6f}")
print()

# Verify the solution by plugging back into Colebrook equation
sqrt_f = math.sqrt(f)
left_side = 1 / sqrt_f
right_side = -2.0 * math.log10(relative_roughness / 3.7 + 2.51 / (Re * sqrt_f))
print(f"Verification (both sides should be equal):")
print(f"  1/√f = {left_side:.6f}")
print(f"  -2.0 log(...) = {right_side:.6f}")
print(f"  Difference = {abs(left_side - right_side):.2e}")

