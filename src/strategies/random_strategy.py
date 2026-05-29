"""
随机策略 / 固定出价策略 (Baseline)
"""
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy


class RandomStrategy(BaseStrategy):
    """随机策略"""
    
    def __init__(self, name: str = 'random', base_bid: float = 1.0, 
                 random_range: float = 0.5):
        super().__init__(name, base_bid)
        self.random_range = random_range
    
    def calculate_bid(self, features: Dict[str, float], p_ctr: float, p_cvr: float = 0.0) -> float:
        """随机出价"""
        return self.base_bid * (1 + np.random.uniform(-self.random_range, self.random_range))


class FixedBidStrategy(BaseStrategy):
    """固定出价策略"""
    
    def __init__(self, name: str = 'fixed', base_bid: float = 1.0):
        super().__init__(name, base_bid)
    
    def calculate_bid(self, features: Dict[str, float], p_ctr: float, p_cvr: float = 0.0) -> float:
        """固定出价"""
        return self.base_bid
