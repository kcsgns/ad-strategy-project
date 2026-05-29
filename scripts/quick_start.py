#!/usr/bin/env python
"""
快速启动脚本 - 简化版本的demo
"""
import sys
import os
import warnings
os.environ.setdefault('MPLCONFIGDIR', os.path.join('/tmp', 'matplotlib-cache'))
warnings.filterwarnings('ignore', category=RuntimeWarning, module='sklearn.utils.extmath')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from src.models.model_trainer import ModelTrainer, generate_synthetic_data
from src.strategies import (
    RandomStrategy, FixedBidStrategy, ECPMStrategy,
    ConversionStrategy, ROIConstraintStrategy
)
from src.budget import BudgetManager
from src.simulation import AuctionEnvironment, Simulator
from src.utils import Visualizer


def quick_start():
    """快速启动"""
    print("Ad Strategy Project - Quick Start\n")
    
    # 创建结果目录
    os.makedirs('results', exist_ok=True)
    
    # 1. 快速训练模型
    print("1. Training models...")
    n_features = 10
    X, y_click, y_conversion = generate_synthetic_data(n_samples=20000, n_features=n_features, random_state=42)
    trainer = ModelTrainer()
    trainer.train_and_compare(X, y_click, y_conversion, model_types=['lr', 'deepfm'])
    best_model_name, best_ctr_model = trainer.get_best_model()
    print(f"   Best model: {best_model_name}")
    
    # 2. 创建策略
    print("\n2. Creating strategies...")
    strategies = {
        'fixed': FixedBidStrategy('fixed', base_bid=0.8),
        'ecpm': ECPMStrategy('ecpm', base_bid=0.8, avg_ctr=float(y_click.mean()), max_bid=4.0),
        'conversion': ConversionStrategy('conversion', base_bid=1.0, value_per_conversion=100.0, target_roi=1.5, max_bid=4.0),
        'roi_constraint': ROIConstraintStrategy('roi_constraint', base_bid=1.0, roi_threshold=1.8, value_per_conversion=100.0, max_bid=4.0)
    }
    print(f"   Strategies: {list(strategies.keys())}")
    
    # 3. 创建环境和预算
    budget_manager = BudgetManager(total_budget=5000.0, n_time_slots=24)
    env = AuctionEnvironment(n_competitors=3, auction_type='second_price', n_features=n_features, random_state=42)
    
    # 4. 运行模拟
    print("\n3. Running simulation...")
    simulator = Simulator(
        environment=env,
        strategies=strategies,
        budget_manager=budget_manager,
        ctr_predictor=best_ctr_model,
        cvr_predictor=trainer.models.get(best_model_name.replace('ctr_', 'cvr_')),
        n_auctions=3000,
        revenue_per_conversion=100.0
    )
    results = simulator.run()
    
    # 5. 展示结果
    print("\n4. Results:")
    comparison_df = simulator.compare_strategies()
    print(comparison_df)
    
    comparison_df.to_csv('results/quick_start_results.csv')
    simulator.plot_comparison('results/quick_start_comparison.png')
    
    print("\nQuick start completed! Check results/ directory for output.")


if __name__ == '__main__':
    quick_start()
