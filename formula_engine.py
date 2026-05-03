import math
import sympy as sp
import logging

class FormulaEngine:
    def __init__(self):
        pass

    def calculate_reactive_power_compensation(self, p_kw, current_cos_phi, target_cos_phi):
        """Calculates needed capacitor power (kVAr) to improve power factor."""
        try:
            phi1 = math.acos(current_cos_phi)
            phi2 = math.acos(target_cos_phi)
            q_kvar = p_kw * (math.tan(phi1) - math.tan(phi2))
            return {
                "p_kw": p_kw,
                "current_cos_phi": current_cos_phi,
                "target_cos_phi": target_cos_phi,
                "needed_q_kvar": round(q_kvar, 2)
            }
        except Exception as e:
            logging.error(f"FormulaEngine error (Reactive): {e}")
            return None

    def hydraulic_flow_rate(self, pressure_bar, pipe_diameter_mm, length_m, viscosity_cst=32):
        """Calculates approximate flow rate based on pressure and diameter."""
        # This is a simplified calculation for internal AI utility
        try:
            area = math.pi * ((pipe_diameter_mm / 1000) / 2)**2
            # Very simplified Bernoulli/Darcy-Weisbach approximation
            # v = sqrt(2*deltaP/rho)
            velocity = math.sqrt(2 * (pressure_bar * 100000) / 900) # 900 is average oil density
            q_m3_s = area * velocity
            q_l_min = q_m3_s * 60000
            return {
                "pipe_mm": pipe_diameter_mm,
                "pressure_bar": pressure_bar,
                "flow_l_min": round(q_l_min, 2)
            }
        except Exception as e:
            logging.error(f"FormulaEngine error (Hydraulic): {e}")
            return None

    def solve_equation(self, expression_str, variable='x'):
        """Solves a symbolic math equation."""
        try:
            var = sp.symbols(variable)
            expr = sp.sympify(expression_str)
            solution = sp.solve(expr, var)
            return solution
        except Exception as e:
            logging.error(f"FormulaEngine error (Sympy): {e}")
            return str(e)

    def calculate_synchronous_speed(self, p_pole_pairs, frequency_hz=50):
        """Calculates synchronous speed of an AC motor."""
        try:
            n1 = (60 * frequency_hz) / p_pole_pairs
            return {
                "frequency_hz": frequency_hz,
                "pole_pairs": p_pole_pairs,
                "synchronous_speed_rpm": int(n1)
            }
        except Exception as e:
            logging.error(f"FormulaEngine error (Sync Speed): {e}")
            return None

    def calculate_motor_slip(self, n1_sync_rpm, n2_rotor_rpm):
        """Calculates slip (s) of an asynchronous motor."""
        try:
            slip = (n1_sync_rpm - n2_rotor_rpm) / n1_sync_rpm
            return {
                "sync_rpm": n1_sync_rpm,
                "rotor_rpm": n2_rotor_rpm,
                "slip": round(slip, 4),
                "slip_percent": round(slip * 100, 2)
            }
        except Exception as e:
            logging.error(f"FormulaEngine error (Slip): {e}")
            return None
