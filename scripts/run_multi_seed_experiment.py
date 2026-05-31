#!/usr/bin/env python3
"""多随机种子策略稳定性实验。"""
import os
import sys
import warnings

os.environ.setdefault('MPLCONFIGDIR', os.path.join('/tmp', 'matplotlib-cache'))
warnings.filterwarnings('ignore', category=RuntimeWarning, module='sklearn.utils.extmath')
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.budget import BudgetManager
from src.models.model_trainer import ModelTrainer, generate_synthetic_data
from src.simulation import AuctionEnvironment, BidLandscapeEstimator, Simulator
from src.strategies import (
    ConversionStrategy,
    ECPMStrategy,
    FixedBidStrategy,
    LandscapeROIStrategy,
    ROIConstraintStrategy,
)


def run_one_seed(seed: int) -> pd.DataFrame:
    n_features = 10
    X, y_click, y_conversion = generate_synthetic_data(
        n_samples=12000,
        n_features=n_features,
        random_state=seed,
    )
    trainer = ModelTrainer()
    trainer.train_and_compare(X, y_click, y_conversion, model_types=['lr'], random_state=seed)
    _, best_ctr_model = trainer.get_best_model()

    strategies = {
        'fixed': FixedBidStrategy('fixed', base_bid=0.8),
        'ecpm': ECPMStrategy('ecpm', base_bid=0.8, avg_ctr=float(y_click.mean()), max_bid=4.0),
        'conversion': ConversionStrategy('conversion', base_bid=1.0, value_per_conversion=100.0, target_roi=1.5, max_bid=4.0),
        'roi_constraint': ROIConstraintStrategy('roi_constraint', base_bid=1.0, roi_threshold=1.8, value_per_conversion=100.0, max_bid=4.0),
        'landscape_roi': LandscapeROIStrategy('landscape_roi', base_bid=1.0, roi_threshold=1.8, value_per_conversion=100.0, max_bid=4.0),
    }

    landscape_env = AuctionEnvironment(n_competitors=3, auction_type='second_price', n_features=n_features, random_state=seed + 1000)
    bid_landscape = BidLandscapeEstimator(n_bins=10).fit_from_environment(landscape_env, n_samples=10000)
    env = AuctionEnvironment(n_competitors=3, auction_type='second_price', n_features=n_features, random_state=seed)
    simulator = Simulator(
        environment=env,
        strategies=strategies,
        budget_manager=BudgetManager(total_budget=5000.0, n_time_slots=24),
        ctr_predictor=best_ctr_model,
        cvr_predictor=trainer.models.get('cvr_lr'),
        bid_landscape=bid_landscape,
        n_auctions=2000,
        revenue_per_conversion=100.0,
    )
    simulator.run()
    df = simulator.compare_strategies().reset_index().rename(columns={'index': 'strategy'})
    df['seed'] = seed
    return df


def main():
    os.makedirs('results', exist_ok=True)
    seeds = [11, 22, 33, 44, 55]
    all_results = pd.concat([run_one_seed(seed) for seed in seeds], ignore_index=True)
    metrics = ['roi', 'gmv', 'ecpa', 'total_conversions', 'budget_utilization', 'high_value_win_ratio']
    summary = all_results.groupby('strategy')[metrics].agg(['mean', 'std']).sort_values(('roi', 'mean'), ascending=False)

    all_results.to_csv('results/multi_seed_raw.csv', index=False)
    summary.to_csv('results/multi_seed_summary.csv')
    print('Multi-seed Summary:')
    print(summary)
    print('\nSaved results/multi_seed_raw.csv and results/multi_seed_summary.csv')


if __name__ == '__main__':
    main()
