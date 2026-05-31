"""
补贴 uplift 模拟器。

营销里更关心“补贴是否带来增量”，而不是用户本来就会不会买。本模块
构造 control/treatment 两种购买概率，用来比较 pCVR、LTV 和 uplift 策略。
"""
from typing import List

import numpy as np
import pandas as pd


class UpliftSimulator:
    """生成用户级补贴实验并评估不同 target 策略。"""

    def __init__(self, n_users: int = 20000, subsidy_cost: float = 8.0, random_state: int = 42):
        self.n_users = n_users
        self.subsidy_cost = subsidy_cost
        self.rng = np.random.default_rng(random_state)
        self.users = self._generate_users()

    def _generate_users(self) -> pd.DataFrame:
        intent = self.rng.beta(2.0, 8.0, self.n_users)
        price_sensitivity = self.rng.beta(2.5, 3.5, self.n_users)
        ltv_score = self.rng.lognormal(mean=np.log(120.0), sigma=0.55, size=self.n_users)
        base_cvr = np.clip(0.02 + 0.45 * intent, 0.001, 0.80)

        # 高意向低敏感用户本来就会买；中意向高敏感用户更容易被补贴撬动。
        uplift = 0.18 * price_sensitivity * (1.0 - intent) + 0.04 * intent
        treatment_cvr = np.clip(base_cvr + uplift, 0.001, 0.95)
        order_value = ltv_score * self.rng.uniform(0.55, 1.10, self.n_users)

        return pd.DataFrame({
            'intent': intent,
            'price_sensitivity': price_sensitivity,
            'ltv_score': ltv_score,
            'control_cvr': base_cvr,
            'treatment_cvr': treatment_cvr,
            'uplift': treatment_cvr - base_cvr,
            'order_value': order_value,
        })

    def evaluate(self, strategy: str, treatment_budget: int = 3000) -> dict:
        df = self.users.copy()
        strategy = strategy.lower()
        if strategy == 'pcvr':
            score = df['treatment_cvr']
        elif strategy == 'ltv':
            score = df['ltv_score']
        elif strategy == 'uplift':
            score = df['uplift']
        elif strategy == 'roi_uplift':
            score = df['uplift'] * df['order_value'] / self.subsidy_cost
        else:
            raise ValueError(f'Unknown uplift strategy: {strategy}')

        selected_idx = score.nlargest(treatment_budget).index
        selected = df.loc[selected_idx]
        treated_conversions = self.rng.binomial(1, selected['treatment_cvr']).sum()
        baseline_conversions = selected['control_cvr'].sum()
        incremental_conversions = treated_conversions - baseline_conversions
        gmv = treated_conversions * selected['order_value'].mean()
        incremental_gmv = incremental_conversions * selected['order_value'].mean()
        cost = treatment_budget * self.subsidy_cost

        return {
            'strategy': strategy,
            'treated_users': treatment_budget,
            'subsidy_cost': cost,
            'treated_conversions': float(treated_conversions),
            'expected_baseline_conversions': float(baseline_conversions),
            'incremental_conversions': float(incremental_conversions),
            'gmv': float(gmv),
            'incremental_gmv': float(incremental_gmv),
            'incremental_roi': float(incremental_gmv / (cost + 1e-8)),
            'cost_per_incremental_conversion': float(cost / (incremental_conversions + 1e-8)),
            'avg_uplift': float(selected['uplift'].mean()),
            'avg_ltv': float(selected['ltv_score'].mean()),
        }

    def compare(self, strategies: List[str] = None, treatment_budget: int = 3000) -> pd.DataFrame:
        strategies = strategies or ['pcvr', 'ltv', 'uplift', 'roi_uplift']
        rows = [self.evaluate(strategy, treatment_budget) for strategy in strategies]
        return pd.DataFrame(rows).sort_values('incremental_roi', ascending=False)
