#!/usr/bin/env python
"""
主运行脚本
训练模型并运行模拟
"""
import sys
import os
import warnings
os.environ.setdefault('MPLCONFIGDIR', os.path.join('/tmp', 'matplotlib-cache'))
warnings.filterwarnings('ignore', category=RuntimeWarning, module='sklearn.utils.extmath')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import numpy as np

from src.models.model_trainer import ModelTrainer, generate_synthetic_data
from src.data import load_avazu_ctr_data
from src.strategies import (
    RandomStrategy, FixedBidStrategy, ECPMStrategy,
    ConversionStrategy, ROIConstraintStrategy
)
from src.budget import BudgetManager
from src.simulation import AuctionEnvironment, Simulator
from src.utils import Visualizer


def load_config(config_dir: str = 'config'):
    """加载配置文件"""
    configs = {}
    for config_file in ['model_config.yaml', 'strategy_config.yaml', 'budget_config.yaml']:
        with open(os.path.join(config_dir, config_file), 'r') as f:
            configs[config_file.replace('.yaml', '')] = yaml.safe_load(f)
    return configs


def main(use_avazu=False, avazu_path=None):
    print("="*60)
    print("Ad Strategy Project - Starting")
    print("="*60)
    
    # 创建结果目录
    os.makedirs('results', exist_ok=True)
    
    # 加载配置
    print("\nLoading configurations...")
    configs = load_config()
    
    # 1. 加载数据并训练模型
    print("\n" + "="*60)
    print("Step 1: Loading Data and Training CTR/CVR Models")
    print("="*60)
    
    model_config = configs['model_config']
    
    # 判断使用真实数据还是模拟数据
    if use_avazu and avazu_path and os.path.exists(avazu_path):
        print(f"Loading real Avazu CTR data from: {avazu_path}")
        X, y_click = load_avazu_ctr_data(avazu_path, nrows=model_config['data']['n_samples'])
        # Avazu 没有转化标签，模拟生成转化数据
        np.random.seed(model_config['training']['random_state'])
        y_conversion = (y_click * np.random.rand(len(y_click)) > 0.7).astype(int)
        print(f"Loaded {len(y_click)} samples from Avazu data")
        print(f"Click rate: {y_click.mean():.4f}")
        print(f"Conversion rate: {y_conversion.mean():.4f}")
    else:
        if use_avazu and not avazu_path:
            print("Warning: Avazu path not provided, using synthetic data instead")
        elif use_avazu and not os.path.exists(avazu_path):
            print(f"Warning: Avazu file not found at {avazu_path}, using synthetic data instead")
        
        print("Generating synthetic data for training...")
        X, y_click, y_conversion = generate_synthetic_data(
            n_samples=model_config['data']['n_samples'],
            n_features=model_config['data']['n_features'],
            random_state=model_config['training']['random_state']
        )
    
    trainer = ModelTrainer()
    results = trainer.train_and_compare(
        X, y_click, y_conversion,
        model_types=model_config['model_types'],
        test_size=model_config['training']['test_size'],
        random_state=model_config['training']['random_state']
    )
    
    print("\nModel Comparison Results:")
    for name, metrics in results.items():
        print(f"  {name}: AUC={metrics.get('auc', 'N/A'):.4f}, LogLoss={metrics.get('logloss', 'N/A'):.4f}")
    
    trainer.plot_model_comparison('results/model_comparison.png')
    
    # 获取最佳模型
    best_model_name, best_ctr_model = trainer.get_best_model()
    print(f"\nBest model: {best_model_name}")
    
    # 2. 创建策略
    print("\n" + "="*60)
    print("Step 2: Creating Bidding Strategies")
    print("="*60)
    
    strategy_config = configs['strategy_config']
    strategies = {}
    
    avg_ctr = float(y_click.mean())
    strategies['random'] = RandomStrategy(name='random', base_bid=0.8, random_range=0.5)
    strategies['fixed'] = FixedBidStrategy(name='fixed', base_bid=0.8)
    strategies['ecpm'] = ECPMStrategy(name='ecpm', base_bid=0.8, avg_ctr=avg_ctr, max_bid=4.0)
    strategies['conversion'] = ConversionStrategy(
        name='conversion', base_bid=1.0,
        value_per_conversion=strategy_config['revenue_per_conversion'],
        target_roi=1.5, max_bid=4.0
    )
    strategies['roi_constraint'] = ROIConstraintStrategy(
        name='roi_constraint', base_bid=1.0,
        roi_threshold=1.8, value_per_conversion=strategy_config['revenue_per_conversion'],
        max_bid=4.0
    )
    
    print(f"Created {len(strategies)} strategies: {list(strategies.keys())}")
    
    # 3. 创建预算管理器和环境
    budget_config = configs['budget_config']
    budget_manager = BudgetManager(
        total_budget=budget_config['total_budget'],
        n_time_slots=budget_config['n_time_slots']
    )
    
    # 获取特征名称（用于匹配训练数据）
    feature_names = X.columns.tolist() if hasattr(X, 'columns') else None
    
    env = AuctionEnvironment(
        n_competitors=3,
        auction_type='second_price',
        n_features=len(feature_names) if feature_names else model_config['data']['n_features'],
        feature_names=feature_names,
        random_state=model_config['training']['random_state']
    )
    
    # 4. 运行模拟
    print("\n" + "="*60)
    print("Step 3: Running Simulation")
    print("="*60)
    
    simulator = Simulator(
        environment=env,
        strategies=strategies,
        budget_manager=budget_manager,
        ctr_predictor=best_ctr_model,
        cvr_predictor=trainer.models.get(f'cvr_{best_model_name.split("_")[1]}', None),
        n_auctions=2000,
        revenue_per_conversion=strategy_config['revenue_per_conversion']
    )
    
    simulation_results = simulator.run()
    
    # 5. 展示结果
    print("\n" + "="*60)
    print("Step 4: Results")
    print("="*60)
    
    comparison_df = simulator.compare_strategies()
    print("\nStrategy Comparison (sorted by ROI):")
    print(comparison_df)
    
    # 保存结果
    comparison_df.to_csv('results/strategy_comparison.csv')
    print(f"\nResults saved to:")
    print(f"  - results/strategy_comparison.csv")
    print(f"  - results/model_comparison.png")
    
    # 可视化
    print("\nGenerating visualizations...")
    simulator.plot_comparison('results/strategy_comparison_plot.png')
    simulator.plot_time_series('results/time_series_plot.png')
    
    print("\n" + "="*60)
    print("Done! All results saved in 'results/' directory.")
    print("="*60)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Ad Strategy Simulation')
    parser.add_argument('--avazu', action='store_true', help='Use Avazu real CTR data')
    parser.add_argument('--avazu-path', type=str, default='data/avazu/train.csv', 
                        help='Path to Avazu train.csv')
    args = parser.parse_args()
    
    main(use_avazu=args.avazu, avazu_path=args.avazu_path)
