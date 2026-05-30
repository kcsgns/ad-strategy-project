"""
拍卖环境 (模拟 AuctionGym)
"""
import numpy as np
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass


@dataclass
class AdOpportunity:
    """广告机会"""
    features: Dict[str, float]
    true_ctr: float
    true_cvr: float
    floor_price: float = 0.1


@dataclass
class AuctionResult:
    """拍卖结果"""
    winner: str
    winning_bid: float
    cost: float
    clicked: bool
    converted: bool


class AuctionEnvironment:
    """拍卖环境"""
    
    def __init__(
        self,
        n_competitors: int = 3,
        auction_type: str = 'second_price',
        n_features: int = 10,
        feature_names: List[str] = None,
        random_state: int = 42
    ):
        self.n_competitors = n_competitors
        self.auction_type = auction_type.lower()
        self.n_features = n_features
        self.feature_names = feature_names or [f'feature_{i}' for i in range(n_features)]
        self.rng = np.random.default_rng(random_state)
        weight_rng = np.random.default_rng(random_state + 1009)
        self.ctr_weights = weight_rng.normal(0.0, 0.55, n_features)
        self.cvr_weights = weight_rng.normal(0.0, 0.8, n_features)
        self.history = []
    
    def generate_opportunity(self, n_features: int = None) -> AdOpportunity:
        """生成广告机会"""
        n_features = n_features or self.n_features
        x = self.rng.normal(0.0, 1.0, n_features)
        features = {self.feature_names[i]: x[i] for i in range(n_features)}

        ctr_logit = -3.1 + x @ self.ctr_weights[:n_features] / np.sqrt(n_features)
        cvr_logit = -1.5 + x @ self.cvr_weights[:n_features] / np.sqrt(n_features)
        true_ctr = 1.0 / (1.0 + np.exp(-ctr_logit))
        true_cvr = 1.0 / (1.0 + np.exp(-cvr_logit))
        floor_price = 0.05 + self.rng.gamma(shape=1.4, scale=0.08)
        
        return AdOpportunity(
            features=features,
            true_ctr=true_ctr,
            true_cvr=true_cvr,
            floor_price=floor_price
        )
    
    def generate_competitor_bids(self, opportunity: AdOpportunity) -> List[float]:
        """生成竞争对手的出价"""
        # 竞争强度随流量质量增加，出价尺度保持在可解释的 CPM/CPA 仿真范围内。
        quality_value = opportunity.true_ctr * (1.0 + 4.0 * opportunity.true_cvr)
        base_bid = 0.05 + quality_value * 5.0
        competitor_bids = []
        
        for i in range(self.n_competitors):
            noise = self.rng.lognormal(mean=0.0, sigma=0.25)
            if i == 0:
                # 激进竞争者
                bid = base_bid * 1.20 * noise
            elif i == 1:
                # 保守竞争者
                bid = base_bid * 0.75 * noise
            else:
                # 随机竞争者
                bid = base_bid * noise
            
            competitor_bids.append(max(opportunity.floor_price, bid))
        
        return competitor_bids
    
    def run_auction(
        self, 
        our_bid: float, 
        competitor_bids: List[float], 
        opportunity: AdOpportunity
    ) -> Tuple[bool, float, bool, bool]:
        """
        运行拍卖
        
        Returns:
            (won, cost, clicked, converted)
        """
        our_bid = max(0.0, our_bid)
        competitor_bids = [max(b, opportunity.floor_price) for b in competitor_bids]
        all_bids = [our_bid] + competitor_bids
        
        # 确定赢家
        max_bid = max(all_bids)
        winner_idx = all_bids.index(max_bid) if max_bid >= opportunity.floor_price else -1
        our_won = (winner_idx == 0)
        
        # 确定成本
        if not our_won:
            cost = 0.0
        elif self.auction_type == 'second_price':
            # 第二价格拍卖，支付第二高出价
            sorted_bids = sorted(all_bids, reverse=True)
            cost = max(sorted_bids[1] if len(sorted_bids) > 1 else opportunity.floor_price, opportunity.floor_price)
        else:
            # 第一价格拍卖
            cost = our_bid
        
        # 模拟点击和转化
        clicked = False
        converted = False
        if our_won:
            clicked = self.rng.random() < opportunity.true_ctr
            if clicked:
                converted = self.rng.random() < opportunity.true_cvr
        
        # 记录历史
        self.history.append({
            'our_bid': our_bid,
            'competitor_bids': competitor_bids,
            'all_bids': all_bids,
            'won': our_won,
            'cost': cost,
            'true_ctr': opportunity.true_ctr,
            'true_cvr': opportunity.true_cvr,
            'clicked': clicked,
            'converted': converted
        })
        
        return our_won, cost, clicked, converted
    
    def reset(self):
        """重置环境"""
        self.history = []
