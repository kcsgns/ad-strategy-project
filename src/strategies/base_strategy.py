"""
竞价策略基类
"""
import numpy as np
from typing import Dict, Any, List
from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """竞价策略基类"""
    
    def __init__(self, name: str, base_bid: float = 1.0):
        self.name = name
        self.base_bid = base_bid
        self.total_spent = 0.0
        self.total_wins = 0
        self.total_clicks = 0
        self.total_conversions = 0
        self.total_gmv = 0.0
        self.total_ltv = 0.0
        self.high_value_wins = 0
        self.channel_spend = {}
        self.history = []
    
    @abstractmethod
    def calculate_bid(self, features: Dict[str, float], p_ctr: float, p_cvr: float = 0.0,
                      bid_landscape=None, opportunity=None) -> float:
        """计算竞价"""
        pass
    
    def update_state(self, won: bool, cost: float, clicked: bool = False, converted: bool = False,
                     revenue: float = 0.0, opportunity=None):
        """更新策略状态"""
        if won:
            self.total_wins += 1
            self.total_spent += cost
            if opportunity is not None:
                self.total_ltv += getattr(opportunity, 'ltv_score', 0.0)
                if getattr(opportunity, 'user_segment', '') == 'high_value':
                    self.high_value_wins += 1
                channel = getattr(opportunity, 'traffic_channel', 'unknown')
                self.channel_spend[channel] = self.channel_spend.get(channel, 0.0) + cost
            if clicked:
                self.total_clicks += 1
                if converted:
                    self.total_conversions += 1
                    self.total_gmv += revenue
        
        # 记录历史
        self.history.append({
            'won': won,
            'cost': cost,
            'clicked': clicked,
            'converted': converted,
            'revenue': revenue,
            'total_spent': self.total_spent
        })
    
    def get_metrics(self, revenue_per_conversion: float = 100.0) -> Dict[str, float]:
        """获取策略指标"""
        revenue = self.total_gmv if self.total_gmv > 0 else self.total_conversions * revenue_per_conversion
        roi = revenue / (self.total_spent + 1e-8)
        
        return {
            'total_spent': self.total_spent,
            'total_wins': self.total_wins,
            'total_clicks': self.total_clicks,
            'total_conversions': self.total_conversions,
            'roi': roi,
            'revenue': revenue,
            'gmv': revenue,
            'roas': roi,
            'cvr': self.total_conversions / (self.total_clicks + 1e-8),
            'ctr': self.total_clicks / (self.total_wins + 1e-8),
            'ecpa': self.total_spent / (self.total_conversions + 1e-8),
            'avg_order_value': revenue / (self.total_conversions + 1e-8),
            'avg_ltv_per_win': self.total_ltv / (self.total_wins + 1e-8),
            'high_value_win_ratio': self.high_value_wins / (self.total_wins + 1e-8)
        }
    
    def reset(self):
        """重置策略状态"""
        self.total_spent = 0.0
        self.total_wins = 0
        self.total_clicks = 0
        self.total_conversions = 0
        self.total_gmv = 0.0
        self.total_ltv = 0.0
        self.high_value_wins = 0
        self.channel_spend = {}
        self.history = []
