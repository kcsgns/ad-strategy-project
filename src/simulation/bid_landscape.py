"""
Bid landscape / win-rate estimator.

真实 RTB 系统通常会先估计市场价分布 P(market_price <= bid | traffic)，再决定
出价。本模块用分桶经验分布近似这个过程，既保持可解释，也便于在仿真环境里复现。
"""
from typing import Dict, List

import numpy as np

from .auction_env import AuctionEnvironment


class BidLandscapeEstimator:
    """按流量质量分桶的市场价与胜率估计器。"""

    def __init__(self, n_bins: int = 10, min_samples_per_bin: int = 20):
        self.n_bins = n_bins
        self.min_samples_per_bin = min_samples_per_bin
        self.bin_edges = None
        self.market_prices: Dict[int, np.ndarray] = {}
        self.global_market_prices = np.array([])
        self.is_fitted = False

    @staticmethod
    def quality_score(p_ctr: float, p_cvr: float) -> float:
        """流量质量分数，和 auction_env 的竞争强度保持同一业务含义。"""
        return float(p_ctr * (1.0 + 4.0 * p_cvr))

    def fit_from_environment(self, environment: AuctionEnvironment, n_samples: int = 20000):
        """从拍卖环境采样竞争者最高价，形成离线 bid landscape。"""
        scores: List[float] = []
        market_prices: List[float] = []

        for _ in range(n_samples):
            opportunity = environment.generate_opportunity()
            competitor_bids = environment.generate_competitor_bids(opportunity)
            scores.append(self.quality_score(opportunity.true_ctr, opportunity.true_cvr))
            market_prices.append(max(max(competitor_bids), opportunity.floor_price))

        scores_np = np.asarray(scores)
        prices_np = np.asarray(market_prices)
        self.global_market_prices = np.sort(prices_np)

        quantiles = np.linspace(0.0, 1.0, self.n_bins + 1)
        self.bin_edges = np.quantile(scores_np, quantiles)
        self.bin_edges[0] = -np.inf
        self.bin_edges[-1] = np.inf

        self.market_prices = {}
        bin_ids = np.digitize(scores_np, self.bin_edges[1:-1], right=True)
        for bin_id in range(self.n_bins):
            bin_prices = prices_np[bin_ids == bin_id]
            if len(bin_prices) >= self.min_samples_per_bin:
                self.market_prices[bin_id] = np.sort(bin_prices)

        self.is_fitted = True
        return self

    def _prices_for_score(self, score: float) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError('BidLandscapeEstimator is not fitted')

        bin_id = int(np.digitize([score], self.bin_edges[1:-1], right=True)[0])
        return self.market_prices.get(bin_id, self.global_market_prices)

    def estimate_win_rate(self, bid: float, p_ctr: float, p_cvr: float = 0.0) -> float:
        """估计给定出价在相似流量上的胜率。"""
        if bid <= 0:
            return 0.0
        score = self.quality_score(p_ctr, p_cvr)
        prices = self._prices_for_score(score)
        won = np.searchsorted(prices, bid, side='right')
        return float(won / max(len(prices), 1))

    def estimate_market_price(self, p_ctr: float, p_cvr: float = 0.0, win_rate: float = 0.5) -> float:
        """估计达到目标胜率所需的市场价分位点。"""
        score = self.quality_score(p_ctr, p_cvr)
        prices = self._prices_for_score(score)
        win_rate = min(max(win_rate, 0.0), 1.0)
        return float(np.quantile(prices, win_rate))

    def summary(self) -> Dict[str, float]:
        """返回 landscape 的整体统计，便于报告和日志展示。"""
        if not self.is_fitted:
            return {}
        return {
            'samples': float(len(self.global_market_prices)),
            'market_price_p25': float(np.quantile(self.global_market_prices, 0.25)),
            'market_price_p50': float(np.quantile(self.global_market_prices, 0.50)),
            'market_price_p75': float(np.quantile(self.global_market_prices, 0.75)),
            'market_price_p90': float(np.quantile(self.global_market_prices, 0.90)),
        }
