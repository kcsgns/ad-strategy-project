"""
指标计算模块
"""
import numpy as np
from typing import Dict, List, Any


class MetricsCalculator:
    """指标计算器"""
    
    @staticmethod
    def calculate_roi(revenue: float, cost: float) -> float:
        """计算 ROI"""
        if cost == 0:
            return 0.0
        return revenue / cost
    
    @staticmethod
    def calculate_budget_utilization(spent: float, budget: float) -> float:
        """计算预算利用率"""
        if budget == 0:
            return 0.0
        return spent / budget
    
    @staticmethod
    def calculate_ecpa(cost: float, conversions: int) -> float:
        """计算 eCPA"""
        if conversions == 0:
            return float('inf')
        return cost / conversions
    
    @staticmethod
    def calculate_ctr(clicks: int, impressions: int) -> float:
        """计算 CTR"""
        if impressions == 0:
            return 0.0
        return clicks / impressions
    
    @staticmethod
    def calculate_cvr(conversions: int, clicks: int) -> float:
        """计算 CVR"""
        if clicks == 0:
            return 0.0
        return conversions / clicks
    
    @staticmethod
    def calculate_all_metrics(
        total_spent: float,
        total_wins: int,
        total_clicks: int,
        total_conversions: int,
        total_budget: float,
        revenue_per_conversion: float = 100.0
    ) -> Dict[str, float]:
        """计算所有指标"""
        revenue = total_conversions * revenue_per_conversion
        
        return {
            'total_spent': total_spent,
            'total_wins': total_wins,
            'total_clicks': total_clicks,
            'total_conversions': total_conversions,
            'revenue': revenue,
            'roi': MetricsCalculator.calculate_roi(revenue, total_spent),
            'budget_utilization': MetricsCalculator.calculate_budget_utilization(total_spent, total_budget),
            'ecpa': MetricsCalculator.calculate_ecpa(total_spent, total_conversions),
            'ctr': MetricsCalculator.calculate_ctr(total_clicks, total_wins),
            'cvr': MetricsCalculator.calculate_cvr(total_conversions, total_clicks)
        }
