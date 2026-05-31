"""
多场景营销预算分配。

这里把电商流量拆成 search / recommendation / short_video / live_commerce / shelf，
比较平均分配、按流量分配、按 ROI 预估分配三种策略。
"""
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd


@dataclass
class ChannelProfile:
    name: str
    traffic_volume: int
    avg_ctr: float
    avg_cvr: float
    avg_order_value: float
    avg_cost: float
    ltv_multiplier: float

    @property
    def expected_value_per_impression(self) -> float:
        return self.avg_ctr * self.avg_cvr * self.avg_order_value * self.ltv_multiplier

    @property
    def expected_roi(self) -> float:
        return self.expected_value_per_impression / max(self.avg_cost, 1e-8)


class MarketingBudgetAllocator:
    """根据渠道画像模拟预算分配和产出。"""

    def __init__(self, channels: List[ChannelProfile], total_budget: float, random_state: int = 42):
        self.channels = channels
        self.total_budget = total_budget
        self.rng = np.random.default_rng(random_state)

    @staticmethod
    def default_channels() -> List[ChannelProfile]:
        return [
            ChannelProfile('search', 12000, 0.055, 0.130, 115.0, 0.42, 1.10),
            ChannelProfile('recommendation', 22000, 0.046, 0.095, 88.0, 0.34, 1.00),
            ChannelProfile('short_video', 16000, 0.052, 0.075, 76.0, 0.36, 0.95),
            ChannelProfile('live_commerce', 7000, 0.041, 0.155, 138.0, 0.52, 1.25),
            ChannelProfile('shelf', 5000, 0.032, 0.070, 65.0, 0.25, 0.85),
        ]

    def allocate(self, method: str) -> Dict[str, float]:
        method = method.lower()
        if method == 'uniform':
            weights = np.ones(len(self.channels))
        elif method == 'traffic':
            weights = np.array([channel.traffic_volume for channel in self.channels], dtype=float)
        elif method == 'roi':
            weights = np.array([channel.expected_roi for channel in self.channels], dtype=float)
        elif method == 'value':
            weights = np.array([channel.expected_value_per_impression for channel in self.channels], dtype=float)
        else:
            raise ValueError(f'Unknown allocation method: {method}')

        weights = weights / weights.sum()
        return {
            channel.name: float(self.total_budget * weight)
            for channel, weight in zip(self.channels, weights)
        }

    def simulate(self, method: str) -> pd.DataFrame:
        budgets = self.allocate(method)
        rows = []

        for channel in self.channels:
            budget = budgets[channel.name]
            max_impressions_by_budget = int(budget / max(channel.avg_cost, 1e-8))
            impressions = min(channel.traffic_volume, max_impressions_by_budget)
            spend = impressions * channel.avg_cost

            clicks = self.rng.binomial(impressions, channel.avg_ctr) if impressions > 0 else 0
            conversions = self.rng.binomial(clicks, channel.avg_cvr) if clicks > 0 else 0
            avg_order = channel.avg_order_value * self.rng.lognormal(mean=0.0, sigma=0.08)
            gmv = conversions * avg_order * channel.ltv_multiplier

            rows.append({
                'method': method,
                'channel': channel.name,
                'allocated_budget': budget,
                'spend': spend,
                'impressions': impressions,
                'clicks': clicks,
                'conversions': conversions,
                'gmv': gmv,
                'roi': gmv / (spend + 1e-8),
                'ecpa': spend / (conversions + 1e-8),
                'budget_utilization': spend / (budget + 1e-8),
            })

        return pd.DataFrame(rows)

    def compare(self, methods: List[str] = None) -> pd.DataFrame:
        methods = methods or ['uniform', 'traffic', 'value', 'roi']
        df = pd.concat([self.simulate(method) for method in methods], ignore_index=True)
        return df.groupby('method').agg({
            'allocated_budget': 'sum',
            'spend': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'conversions': 'sum',
            'gmv': 'sum',
        }).assign(
            roi=lambda x: x['gmv'] / (x['spend'] + 1e-8),
            ecpa=lambda x: x['spend'] / (x['conversions'] + 1e-8),
            budget_utilization=lambda x: x['spend'] / (x['allocated_budget'] + 1e-8),
        ).sort_values('roi', ascending=False)
