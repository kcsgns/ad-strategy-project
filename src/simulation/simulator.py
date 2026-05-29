"""
模拟器
整合所有模块，运行端到端的模拟
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from .auction_env import AuctionEnvironment
from ..strategies.base_strategy import BaseStrategy
from ..budget.budget_manager import BudgetManager
from ..models.ctr_predictor import CTRPredictor, CVRPredictor


class Simulator:
    """模拟器"""
    
    def __init__(
        self,
        environment: AuctionEnvironment,
        strategies: Dict[str, BaseStrategy],
        budget_manager: BudgetManager,
        ctr_predictor: CTRPredictor,
        cvr_predictor: CVRPredictor = None,
        n_auctions: int = 1000,
        revenue_per_conversion: float = 100.0
    ):
        self.env = environment
        self.strategies = strategies
        self.budget_manager = budget_manager
        self.ctr_predictor = ctr_predictor
        self.cvr_predictor = cvr_predictor
        self.n_auctions = n_auctions
        self.revenue_per_conversion = revenue_per_conversion
        
        self.results = {}
        self.time_series = {name: [] for name in strategies.keys()}
    
    def run(self) -> Dict[str, Any]:
        """运行模拟"""
        print(f"Starting simulation with {len(self.strategies)} strategies...")
        
        for strategy_name, strategy in self.strategies.items():
            print(f"\nRunning strategy: {strategy_name}")
            strategy.reset()
            self.budget_manager.reset()
            self.env.reset()
            
            auction_count = 0
            time_slot = 0
            auctions_per_slot = max(1, self.n_auctions // self.budget_manager.n_time_slots)
            
            while auction_count < self.n_auctions and self.budget_manager.total_spent < self.budget_manager.total_budget:
                # 生成广告机会
                opportunity = self.env.generate_opportunity()
                
                # 预测 CTR 和 CVR
                features_df = pd.DataFrame([opportunity.features])
                p_ctr = self.ctr_predictor.predict(features_df)[0] if self.ctr_predictor.is_trained else opportunity.true_ctr
                
                p_cvr = 0.0
                if self.cvr_predictor and self.cvr_predictor.is_trained:
                    p_cvr = self.cvr_predictor.predict(features_df)[0]
                else:
                    p_cvr = opportunity.true_cvr
                
                # 计算出价
                pacing_factor = self.budget_manager.get_pacing_factor()
                raw_bid = strategy.calculate_bid(opportunity.features, p_ctr, p_cvr)
                final_bid = raw_bid * pacing_factor
                
                # 生成竞争对手出价
                competitor_bids = self.env.generate_competitor_bids(opportunity)
                
                # 运行拍卖
                won, cost, clicked, converted = self.env.run_auction(
                    final_bid, competitor_bids, opportunity
                )
                
                # 更新状态
                if won and self.budget_manager.can_spend(cost):
                    self.budget_manager.spend(cost)
                    strategy.update_state(won, cost, clicked, converted)
                else:
                    strategy.update_state(False, 0.0, False, False)
                
                # 记录时间序列数据
                self.time_series[strategy_name].append({
                    'auction_idx': auction_count,
                    'time_slot': time_slot,
                    'spent': self.budget_manager.total_spent,
                    'conversions': strategy.total_conversions,
                    'bid': final_bid
                })
                
                auction_count += 1
                
                # 每个时间 slot 有 n_auctions / n_slots 次拍卖
                if auction_count % auctions_per_slot == 0:
                    self.budget_manager.advance_time_slot()
                    time_slot += 1
            
            # 保存策略结果
            self.results[strategy_name] = strategy.get_metrics(self.revenue_per_conversion)
            self.results[strategy_name]['budget_utilization'] = self.budget_manager.get_budget_utilization()
            
            print(f"  Completed {auction_count} auctions")
            print(f"  Total spent: {self.budget_manager.total_spent:.2f}")
            print(f"  Conversions: {strategy.total_conversions}")
            print(f"  ROI: {self.results[strategy_name]['roi']:.2f}")
        
        return self.results
    
    def compare_strategies(self) -> pd.DataFrame:
        """对比策略结果"""
        df = pd.DataFrame(self.results).T
        df = df.sort_values('roi', ascending=False)
        return df
    
    def plot_comparison(self, save_path: str = None):
        """绘制策略对比图"""
        df = self.compare_strategies()
        
        # 选择关键指标
        metrics = ['roi', 'total_conversions', 'total_spent', 'budget_utilization', 'ecpa']
        fig, axes = plt.subplots(len(metrics), 1, figsize=(12, 4 * len(metrics)))
        
        for i, metric in enumerate(metrics):
            ax = axes[i]
            bars = ax.bar(df.index, df[metric], alpha=0.7, color=sns.color_palette('viridis', len(df)))
            ax.set_title(f'Strategy Comparison: {metric.upper()}')
            ax.set_ylabel(metric.upper())
            ax.tick_params(axis='x', rotation=45)
            
            # 添加数值标签
            for j, bar in enumerate(bars):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{df[metric].iloc[j]:.2f}',
                       ha='center', va='bottom')
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        elif matplotlib.get_backend().lower() != 'agg':
            plt.show()
        plt.close()
    
    def plot_time_series(self, save_path: str = None):
        """绘制时间序列数据"""
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # 累积花费
        ax1 = axes[0]
        for name, data in self.time_series.items():
            df = pd.DataFrame(data)
            ax1.plot(df['auction_idx'], df['spent'], label=name, linewidth=2, marker='.', markersize=4)
        ax1.axhline(y=self.budget_manager.total_budget, color='r', linestyle='--', label='Budget Limit')
        ax1.set_title('Cumulative Spend Over Time')
        ax1.set_xlabel('Auction Index')
        ax1.set_ylabel('Cumulative Spend')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 转化数
        ax2 = axes[1]
        for name, data in self.time_series.items():
            df = pd.DataFrame(data)
            ax2.plot(df['auction_idx'], df['conversions'], label=name, linewidth=2, marker='.', markersize=4)
        ax2.set_title('Cumulative Conversions Over Time')
        ax2.set_xlabel('Auction Index')
        ax2.set_ylabel('Cumulative Conversions')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        elif matplotlib.get_backend().lower() != 'agg':
            plt.show()
        plt.close()
