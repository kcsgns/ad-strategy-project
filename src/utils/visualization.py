"""
可视化模块
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any


class Visualizer:
    """可视化工具"""
    
    @staticmethod
    def set_style():
        """设置绘图风格"""
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 12
    
    @staticmethod
    def plot_strategy_comparison(results: pd.DataFrame, save_path: str = None):
        """策略对比图"""
        Visualizer.set_style()
        
        metrics = ['roi', 'total_conversions', 'total_spent', 'budget_utilization', 'ecpa']
        fig, axes = plt.subplots(len(metrics), 1, figsize=(14, 4 * len(metrics)))
        
        for i, metric in enumerate(metrics):
            ax = axes[i]
            bars = ax.bar(results.index, results[metric], alpha=0.7, color=sns.color_palette('viridis', len(results)))
            ax.set_title(f'Strategy Comparison: {metric.upper()}', fontsize=14, fontweight='bold')
            ax.set_ylabel(metric.upper())
            ax.tick_params(axis='x', rotation=45)
            
            # 添加数值标签
            for j, bar in enumerate(bars):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{results[metric].iloc[j]:.2f}',
                       ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        elif matplotlib.get_backend().lower() != 'agg':
            plt.show()
        plt.close()
    
    @staticmethod
    def plot_time_series(time_series_data: Dict[str, List[Dict]], budget: float, save_path: str = None):
        """时间序列图"""
        Visualizer.set_style()
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # 累积花费
        ax1 = axes[0]
        for name, data in time_series_data.items():
            df = pd.DataFrame(data)
            ax1.plot(df['auction_idx'], df['spent'], label=name, linewidth=2, marker='.', markersize=4)
        ax1.axhline(y=budget, color='r', linestyle='--', linewidth=2, label='Budget Limit')
        ax1.set_title('Cumulative Spend Over Time', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Auction Index')
        ax1.set_ylabel('Cumulative Spend')
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # 转化数
        ax2 = axes[1]
        for name, data in time_series_data.items():
            df = pd.DataFrame(data)
            ax2.plot(df['auction_idx'], df['conversions'], label=name, linewidth=2, marker='.', markersize=4)
        ax2.set_title('Cumulative Conversions Over Time', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Auction Index')
        ax2.set_ylabel('Cumulative Conversions')
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        elif matplotlib.get_backend().lower() != 'agg':
            plt.show()
        plt.close()
    
    @staticmethod
    def plot_hourly_distribution(spend_per_hour: Dict[str, np.ndarray], save_path: str = None):
        """分时段消耗曲线图"""
        Visualizer.set_style()
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        hours = np.arange(24)
        for name, spend in spend_per_hour.items():
            ax.plot(hours, spend, label=name, linewidth=2, marker='o', markersize=6)
        
        ax.set_title('Hourly Spend Distribution', fontsize=14, fontweight='bold')
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Spend')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.set_xticks(hours)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        elif matplotlib.get_backend().lower() != 'agg':
            plt.show()
        plt.close()
