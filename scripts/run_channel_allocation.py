#!/usr/bin/env python3
"""运行多场景电商营销预算分配实验。"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.allocation import MarketingBudgetAllocator


def main():
    os.makedirs('results', exist_ok=True)
    allocator = MarketingBudgetAllocator(
        channels=MarketingBudgetAllocator.default_channels(),
        total_budget=10000.0,
        random_state=42,
    )
    detail_frames = []
    for method in ['uniform', 'traffic', 'value', 'roi']:
        detail_frames.append(allocator.simulate(method))
    detail_df = __import__('pandas').concat(detail_frames, ignore_index=True)
    summary_df = allocator.compare(['uniform', 'traffic', 'value', 'roi'])

    detail_df.to_csv('results/channel_allocation_detail.csv', index=False)
    summary_df.to_csv('results/channel_allocation_summary.csv')

    print('Channel Allocation Summary:')
    print(summary_df)
    print('\nSaved results/channel_allocation_detail.csv and results/channel_allocation_summary.csv')


if __name__ == '__main__':
    main()
