# 面向 ROI 约束的广告投放排序与预算控制系统

## 项目概述

这是一个面向 ROI 约束的广告投放策略仿真项目，集成了 CTR/CVR 预测、竞价策略优化、预算 pacing 和第二价格拍卖模拟。项目参考 RTB benchmark 的离线评估思路，用可复现实验比较固定出价、pCTR 线性出价、转化价值出价和 ROI 约束出价在消耗、转化、ROI、eCPA 等业务指标上的表现。

## 技术栈与开源库

### CTR/CVR 预测
- 当前实现: Logistic Regression 与一个轻量级神经网络 demo，用于展示训练、评估和策略接入链路
- 可扩展方向: DeepCTR-Torch、DeepFM、xDeepFM、DIN 等模型
- 可替换数据集: iPinYou、Criteo、Avazu、Ali-CCP

### 预算控制
- 当前实现: 自定义 BudgetManager + PID pacing 乘子
- 可扩展方向: AuctionGym、rtbcontrol、真实分小时流量曲线

### 竞价策略
- 随机投放 / 固定出价 (Baseline)
- 固定出价 / 随机出价 baseline
- pCTR 线性出价: `bid = base_bid * pCTR / avgCTR`
- 转化价值出价: `bid = pCTR * pCVR * conversion_value / target_roi`
- ROI 约束: 根据预期转化价值和 ROI threshold 控制最高出价
- Bid landscape 感知 ROI: 估计 `P(market_price <= bid | traffic)`，在 ROI 约束内选择期望利润更高的出价

## 项目结构

```
ad-strategy-project/
├── README.md
├── requirements.txt
├── config/
│   ├── model_config.yaml
│   ├── strategy_config.yaml
│   └── budget_config.yaml
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ctr_predictor.py      # CTR/CVR 预测模型
│   │   └── model_trainer.py      # 模型训练器
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base_strategy.py      # 策略基类
│   │   ├── random_strategy.py    # 随机策略
│   │   ├── ecpm_strategy.py      # eCPM 策略
│   │   ├── conversion_strategy.py # 转化目标策略
│   │   └── roi_constraint_strategy.py # ROI约束策略
│   ├── budget/
│   │   ├── __init__.py
│   │   └── budget_manager.py     # 预算管理器
│   ├── pacing/
│   │   ├── __init__.py
│   │   ├── pid_controller.py     # PID 控制器
│   │   └── time_pacing.py        # 时间 pacing
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── auction_env.py        # 拍卖环境
│   │   └── simulator.py          # 模拟器
│   └── utils/
│       ├── __init__.py
│       ├── metrics.py            # 指标计算
│       └── visualization.py      # 可视化
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_model_training.ipynb
│   ├── 03_strategy_comparison.ipynb
│   └── 04_results_analysis.ipynb
├── data/
├── results/
└── scripts/
    ├── run_simulation.sh
    └── train_models.sh
```

## 核心功能模块

### 1. CTR/CVR 预测模块
- 支持 DeepFM、xDeepFM、LR 等多种模型
- 使用 AUC、Logloss 评估模型效果
- 特征工程: 用户特征、广告特征、上下文特征

### 2. 竞价策略模块
- 多种策略实现与对比
- 可自定义策略
- 策略性能评估

### 3. 预算控制模块
- PID 控制算法
- 时间 pacing 算法
- 平滑预算消耗

### 4. 模拟环境
- 自定义第二价格拍卖环境
- 训练数据和在线流量使用同一套 CTR/CVR 生成机制，保证模型分数能影响策略结果
- 支持用户价值分层、流量渠道、商品价格、GMV/LTV proxy 等电商营销要素
- 支持固定随机种子，输出可复现实验结果

## 评估指标

### 传统指标
- AUC
- Logloss

### 业务指标
- 总消耗
- 转化数
- ROI (投资回报率)
- 预算利用率
- eCPA (有效转化成本)
- 分时段消耗曲线

## 简历亮点

### 1. 技术深度
- 机器学习建模 (CTR/CVR)
- 控制理论 (PID 控制)
- 强化学习/ bandit 策略

### 2. 业务理解
- 广告生态系统
- ROI 优化
- 预算管理

### 3. 工程能力
- 模块化设计
- 可扩展性
- 实验框架

### 4. 数据驱动
- 完整的实验对比
- 业务指标评估
- 可视化分析

## 快速开始

### 安装依赖

```bash
pip3 install -r requirements.txt
```

### 使用真实 CTR 数据

下载 Kaggle Avazu Click-Through Rate Prediction 数据集，并将 `train.csv` 放到：

```text
data/raw/avazu/train.csv
```

运行真实 CTR 数据实验：

```bash
python3 scripts/run_real_avazu.py --input data/raw/avazu/train.csv --nrows 100000
```

说明：Avazu 提供点击标签，但不包含转化和成交价字段；因此当前流程使用 Avazu 训练 CTR 模型，再接入项目内的拍卖仿真环境评估策略。

### 训练模型

```bash
python3 scripts/quick_start.py
python3 scripts/main.py
python3 scripts/run_channel_allocation.py
python3 scripts/run_uplift_experiment.py
python3 scripts/run_multi_seed_experiment.py
```

实验设计和最近一次结果见 [EXPERIMENTS.md](EXPERIMENTS.md)。

## 贡献指南

欢迎提交 Issue 和 Pull Request!

## 许可证

MIT License
