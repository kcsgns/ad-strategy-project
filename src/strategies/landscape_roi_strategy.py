"""
Bid landscape 感知的 ROI 策略。
"""
from typing import Dict

import numpy as np

from .base_strategy import BaseStrategy


class LandscapeROIStrategy(BaseStrategy):
    """结合预期价值和 win-rate 估计的 ROI 策略。"""

    def __init__(
        self,
        name: str = 'landscape_roi',
        base_bid: float = 1.0,
        roi_threshold: float = 1.8,
        value_per_conversion: float = 100.0,
        min_expected_value: float = 0.02,
        max_bid: float = 5.0,
        candidate_count: int = 40,
        min_win_rate: float = 0.02,
    ):
        super().__init__(name, base_bid)
        self.roi_threshold = roi_threshold
        self.value_per_conversion = value_per_conversion
        self.min_expected_value = min_expected_value
        self.max_bid = max_bid
        self.candidate_count = candidate_count
        self.min_win_rate = min_win_rate

    def calculate_bid(self, features: Dict[str, float], p_ctr: float, p_cvr: float = 0.0,
                      bid_landscape=None) -> float:
        expected_value = p_ctr * p_cvr * self.value_per_conversion
        if expected_value < self.min_expected_value:
            return 0.0

        max_roi_bid = min(self.max_bid, self.base_bid * expected_value / max(self.roi_threshold, 1e-8))
        if bid_landscape is None or max_roi_bid <= 0:
            return max(0.0, max_roi_bid)

        floor_bid = min(max_roi_bid, bid_landscape.estimate_market_price(p_ctr, p_cvr, self.min_win_rate))
        candidates = np.linspace(max(floor_bid, 0.01), max_roi_bid, self.candidate_count)

        best_bid = 0.0
        best_score = -np.inf
        for bid in candidates:
            win_rate = bid_landscape.estimate_win_rate(bid, p_ctr, p_cvr)
            if win_rate < self.min_win_rate:
                continue
            expected_profit = win_rate * (expected_value - bid)
            if expected_profit > best_score:
                best_score = expected_profit
                best_bid = bid

        return max(0.0, min(self.max_bid, best_bid))
