#!/usr/bin/env python3
"""
使用 Avazu 真实 CTR 数据训练模型，并接入现有竞价策略仿真。
"""
import argparse
import os
import sys
import warnings

os.environ.setdefault('MPLCONFIGDIR', os.path.join('/tmp', 'matplotlib-cache'))
warnings.filterwarnings('ignore', category=RuntimeWarning, module='sklearn.utils.extmath')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.budget import BudgetManager
from src.data import load_avazu_ctr_data
from src.models.model_trainer import ModelTrainer
from src.simulation import AuctionEnvironment, Simulator
from src.strategies import (
    ConversionStrategy,
    ECPMStrategy,
    FixedBidStrategy,
    ROIConstraintStrategy,
)


def parse_args():
    parser = argparse.ArgumentParser(description='Train CTR model on real Avazu data and run strategy simulation.')
    parser.add_argument('--input', required=True, help='Path to Avazu train.csv')
    parser.add_argument('--nrows', type=int, default=100000, help='Rows to read for local experiments')
    parser.add_argument('--auctions', type=int, default=3000, help='Number of simulated auctions')
    parser.add_argument('--budget', type=float, default=5000.0, help='Simulation budget')
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs('results', exist_ok=True)

    print('Loading Avazu CTR data...')
    X, y_click = load_avazu_ctr_data(args.input, nrows=args.nrows)
    print(f'  rows={len(X)}, features={X.shape[1]}, click_rate={y_click.mean():.4f}')

    print('\nTraining CTR models on real data...')
    trainer = ModelTrainer()
    trainer.train_and_compare(X, y_click, model_types=['lr', 'deepfm'])
    trainer.plot_model_comparison('results/avazu_model_comparison.png')
    best_model_name, best_ctr_model = trainer.get_best_model()
    print(f'\nBest CTR model: {best_model_name}')

    avg_ctr = float(y_click.mean())
    strategies = {
        'fixed': FixedBidStrategy('fixed', base_bid=0.8),
        'ecpm': ECPMStrategy('ecpm', base_bid=0.8, avg_ctr=avg_ctr, max_bid=4.0),
        'conversion': ConversionStrategy('conversion', base_bid=1.0, value_per_conversion=100.0, target_roi=1.5, max_bid=4.0),
        'roi_constraint': ROIConstraintStrategy('roi_constraint', base_bid=1.0, roi_threshold=1.8, value_per_conversion=100.0, max_bid=4.0),
    }

    print('\nRunning strategy simulation with real-data CTR model...')
    env = AuctionEnvironment(
        n_competitors=3,
        auction_type='second_price',
        n_features=X.shape[1],
        feature_names=X.columns.tolist(),
        random_state=42,
    )
    budget_manager = BudgetManager(total_budget=args.budget, n_time_slots=24)
    simulator = Simulator(
        environment=env,
        strategies=strategies,
        budget_manager=budget_manager,
        ctr_predictor=best_ctr_model,
        cvr_predictor=None,
        n_auctions=args.auctions,
        revenue_per_conversion=100.0,
    )
    simulator.run()
    comparison_df = simulator.compare_strategies()
    print('\nStrategy Comparison:')
    print(comparison_df)

    comparison_df.to_csv('results/avazu_strategy_comparison.csv')
    simulator.plot_comparison('results/avazu_strategy_comparison.png')
    simulator.plot_time_series('results/avazu_time_series.png')
    print('\nSaved Avazu experiment results under results/.')


if __name__ == '__main__':
    main()
