"""
预算管理器
"""
import numpy as np
from typing import Dict, Any, List
from ..pacing.pid_controller import PIDController


class BudgetManager:
    """预算管理器"""
    
    def __init__(self, total_budget: float, n_time_slots: int = 24,
                 min_pacing_factor: float = 0.2, max_pacing_factor: float = 1.5):
        self.total_budget = total_budget
        self.n_time_slots = n_time_slots
        self.target_per_slot = total_budget / n_time_slots
        self.min_pacing_factor = min_pacing_factor
        self.max_pacing_factor = max_pacing_factor
        
        self.current_slot = 0
        self.spent_per_slot = np.zeros(n_time_slots)
        self.total_spent = 0.0
        
        # PID 控制器
        self.pid = PIDController(kp=0.9, ki=0.05, kd=0.2)
    
    def can_spend(self, amount: float) -> bool:
        """检查是否可以花费"""
        if self.total_spent + amount > self.total_budget:
            return False
        return True
    
    def spend(self, amount: float):
        """记录花费"""
        self.spent_per_slot[self.current_slot] += amount
        self.total_spent += amount
    
    def advance_time_slot(self):
        """进入下一个时间段"""
        if self.current_slot < self.n_time_slots - 1:
            self.current_slot += 1
    
    def get_pacing_factor(self) -> float:
        """获取 pacing 因子。

        大于 1 表示当前消耗偏慢，需要提高出价；小于 1 表示消耗偏快，需要降价。
        """
        expected_spent = min((self.current_slot + 1) * self.target_per_slot, self.total_budget)
        error = (expected_spent - self.total_spent) / max(self.total_budget, 1e-8)
        control = self.pid.update(error)
        
        factor = 1.0 + control
        return max(self.min_pacing_factor, min(self.max_pacing_factor, factor))
    
    def get_budget_utilization(self) -> float:
        """获取预算利用率"""
        return self.total_spent / self.total_budget
    
    def get_time_series_data(self) -> Dict[str, np.ndarray]:
        """获取时间序列数据"""
        time_slots = np.arange(self.n_time_slots)
        expected = np.cumsum([self.target_per_slot] * self.n_time_slots)
        actual = np.cumsum(self.spent_per_slot)
        
        return {
            'time_slot': time_slots,
            'expected_cumulative': expected,
            'actual_cumulative': actual,
            'actual_per_slot': self.spent_per_slot
        }
    
    def reset(self):
        """重置预算管理器"""
        self.current_slot = 0
        self.spent_per_slot = np.zeros(self.n_time_slots)
        self.total_spent = 0.0
        self.pid.reset()
