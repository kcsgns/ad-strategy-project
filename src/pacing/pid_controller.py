"""
PID 控制器
用于预算 pacing 控制
"""


class PIDController:
    """PID 控制器"""
    
    def __init__(self, kp: float = 1.0, ki: float = 0.0, kd: float = 0.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        
        self.integral = 0.0
        self.last_error = 0.0
    
    def update(self, error: float) -> float:
        """更新控制器，返回控制量"""
        self.integral += error
        derivative = error - self.last_error
        
        output = (self.kp * error + 
                  self.ki * self.integral + 
                  self.kd * derivative)
        
        self.last_error = error
        
        return output
    
    def reset(self):
        """重置控制器"""
        self.integral = 0.0
        self.last_error = 0.0
