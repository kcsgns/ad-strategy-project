"""
转化目标策略: bid * pCTR * pCVR
"""
from typing import Dict, Any
from .base_strategy import BaseStrategy


class ConversionStrategy(BaseStrategy):
    """转化目标策略"""
    
    def __init__(self, name: str = 'conversion', base_bid: float = 1.0, 
                 ctr_multiplier: float = 1000.0, cvr_multiplier: float = 100.0,
                 value_per_conversion: float = 100.0, target_roi: float = 1.5,
                 max_bid: float = 5.0):
        super().__init__(name, base_bid)
        self.ctr_multiplier = ctr_multiplier
        self.cvr_multiplier = cvr_multiplier
        self.value_per_conversion = value_per_conversion
        self.target_roi = target_roi
        self.max_bid = max_bid
    
    def calculate_bid(self, features: Dict[str, float], p_ctr: float, p_cvr: float = 0.0,
                      bid_landscape=None, opportunity=None) -> float:
        """按预期转化价值出价，target_roi 控制愿意支付的价值折扣。"""
        value = getattr(opportunity, 'conversion_value', self.value_per_conversion)
        expected_value = p_ctr * p_cvr * value
        bid = self.base_bid * expected_value / max(self.target_roi, 1e-8)
        return max(0.0, min(self.max_bid, bid))
