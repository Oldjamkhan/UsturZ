import numpy as np
from scipy import optimize
import logging
import math

class MathEngine:
    def __init__(self):
        pass

    def calculate_transformer_efficiency(self, s_kva, p_fe_w, p_cu_w, load_factor=1.0, cos_phi=0.8):
        """Calculates transformer efficiency curve."""
        try:
            p_out = load_factor * s_kva * 1000 * cos_phi
            p_loss = p_fe_w + (load_factor**2 * p_cu_w)
            efficiency = (p_out / (p_out + p_loss)) * 100
            return round(efficiency, 2)
        except Exception as e:
            logging.error(f"MathEngine Error: {e}")
            return None

    def find_optimal_compensation(self, cost_per_kvar, saving_per_kw_reduced, total_kw):
        """Optimization example using scipy."""
        try:
            res = optimize.minimize_scalar(lambda x: (x * cost_per_kvar) - (math.log(x+1) * saving_per_kw_reduced * total_kw))
            return res.x
        except Exception as e:
            logging.error(f"MathEngine Scipy Error: {e}")
            return None

    def calculate_motor_nominal_torque(self, p_kw, n_rpm):
        """Calculates nominal torque of a motor in N.m."""
        try:
            if n_rpm == 0:
                return 0
            torque = 9550 * p_kw / n_rpm
            return round(torque, 2)
        except Exception as e:
            logging.error(f"MathEngine Error (Torque): {e}")
            return None

    def calculate_motor_current(self, p_kw, u_volts, efficiency=0.9, cos_phi=0.85):
        """Calculates nominal line current of a 3-phase AC motor in Amperes."""
        try:
            i_nom = (p_kw * 1000) / (math.sqrt(3) * u_volts * efficiency * cos_phi)
            return round(i_nom, 2)
        except Exception as e:
            logging.error(f"MathEngine Error (Current): {e}")
            return None
