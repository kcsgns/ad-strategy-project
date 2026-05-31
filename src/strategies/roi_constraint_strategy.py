"""
ROI 约束策略: 只投 expected_value / cost >= threshold 的流量
"""
from typing import Dict, Any
from .base_strategy import BaseStrategy


class ROIConstraintStrategy(BaseStrategy):
    """ROI 约束策略"""
    
    def __init__(self, name: str = 'roi_constraint', base_bid: float = 1.0,
                 roi_threshold: float = 2.0, value_per_conversion: float = 100.0,
                 min_expected_value: float = 0.02, max_bid: float = 5.0):
        super().__init__(name, base_bid)
        self.roi_threshold = roi_threshold
        self.value_per_conversion = value_per_conversion
        self.min_expected_value = min_expected_value
        self.max_bid = max_bid
    
    def calculate_bid(self, features: Dict[str, float], p_ctr: float, p_cvr: float = 0.0,
                      bid_landscape=None, opportunity=None) -> float:
        """
        ROI 约束竞价
        预期价值 = pCTR * pCVR * value_per_conversion
        只有当预期价值 / bid >= roi_threshold 时才出价
        """
        value = getattr(opportunity, 'conversion_value', self.value_per_conversion)
        expected_value = p_ctr * p_cvr * value
        if expected_value < self.min_expected_value:
            return 0.0

        max_allowable_bid = expected_value / self.roi_threshold
        
        if max_allowable_bid > 0:
            return min(self.max_bid, self.base_bid * max_allowable_bid)
        else:
            return 0.0  # 不出价
