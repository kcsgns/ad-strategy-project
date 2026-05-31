#!/usr/bin/env python3
"""运行补贴 uplift / 增量 ROI 实验。"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.uplift import UpliftSimulator


def main():
    os.makedirs('results', exist_ok=True)
    simulator = UpliftSimulator(n_users=20000, subsidy_cost=8.0, random_state=42)
    df = simulator.compare(treatment_budget=3000)
    df.to_csv('results/uplift_experiment_summary.csv', index=False)
    print('Uplift Experiment Summary:')
    print(df)
    print('\nSaved results/uplift_experiment_summary.csv')


if __name__ == '__main__':
    main()
