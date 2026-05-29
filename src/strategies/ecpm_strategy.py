"""
eCPM 策略: bid * pCTR
"""
from typing import Dict, Any
from .base_strategy import BaseStrategy


class ECPMStrategy(BaseStrategy):
    """eCPM 策略"""
    
    def __init__(self, name: str = 'ecpm', base_bid: float = 1.0, 
                 ctr_multiplier: float = 1000.0, avg_ctr: float = 0.05,
                 max_bid: float = 5.0):
        super().__init__(name, base_bid)
        self.ctr_multiplier = ctr_multiplier
        self.avg_ctr = avg_ctr
        self.max_bid = max_bid
    
    def calculate_bid(self, features: Dict[str, float], p_ctr: float, p_cvr: float = 0.0) -> float:
        """线性 pCTR 出价，参考 RTB benchmark 常用的 bid = base_bid * pCTR / avgCTR。"""
        bid = self.base_bid * (p_ctr / max(self.avg_ctr, 1e-8))
        return max(0.0, min(self.max_bid, bid))
