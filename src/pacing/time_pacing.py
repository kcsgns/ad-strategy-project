"""
时间 Pacing 模块
"""
import numpy as np
from typing import List, Dict


class TimePacing:
    """时间 Pacing"""
    
    def __init__(self, n_slots: int = 24, budget_profile: List[float] = None):
        self.n_slots = n_slots
        
        if budget_profile is None:
            # 默认均匀分布
            self.budget_profile = np.ones(n_slots) / n_slots
        else:
            assert len(budget_profile) == n_slots
            self.budget_profile = np.array(budget_profile) / sum(budget_profile)
    
    def get_target_spend(self, total_budget: float, current_slot: int) -> float:
        """获取到当前时刻的目标累积花费"""
        return total_budget * np.sum(self.budget_profile[:current_slot + 1])
    
    def get_slot_budget(self, total_budget: float, slot: int) -> float:
        """获取某个时间段的预算"""
        return total_budget * self.budget_profile[slot]


def create_daily_pattern(n_slots: int = 24) -> List[float]:
    """创建日流量模式 (早晚高峰)"""
    # 模拟早晚高峰的流量分布
    pattern = np.ones(n_slots)
    
    # 早高峰 7-10
    morning_peak = slice(7, 10)
    pattern[morning_peak] *= 1.5
    
    # 晚高峰 18-22
    evening_peak = slice(18, 22)
    pattern[evening_peak] *= 1.8
    
    # 低谷 0-6
    low_night = slice(0, 6)
    pattern[low_night] *= 0.3
    
    return pattern.tolist()
