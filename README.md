# 面向 ROI 约束的离线广告策略仿真与评估系统

## 项目概述

这是一个基于公开 CTR 数据与离线拍卖仿真的广告策略评估项目，集成了 CTR/CVR 预测 demo、竞价策略优化、预算 pacing 和第二价格拍卖模拟。项目参考 RTB benchmark 的离线评估思路，用可复现实验比较固定出价、pCTR 线性出价、转化价值出价和 ROI 约束出价在消耗、转化、ROI、eCPA 等业务指标上的表现。

## 技术栈与开源库

### CTR/CVR 预测
- 当前实现: Logistic Regression 与一个轻量级神经网络 demo，用于展示训练、评估和策略接入链路
- 当前未实现: 生产级 DeepFM/xDeepFM/DIN，仅在接口和依赖层面预留扩展空间
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
│   ├── models/          # CTR/CVR 预测与训练
│   ├── strategies/      # 出价策略
│   ├── budget/          # 预算管理
│   ├── pacing/          # PID / 时间 pacing
│   ├── simulation/      # 拍卖环境与模拟器
│   ├── data/            # 数据加载
│   ├── allocation/      # 多场景预算分配
│   ├── uplift/          # uplift 补贴实验
│   └── utils/           # 指标与可视化
├── scripts/             # 实验脚本入口
└── data/                # 本地数据目录
```

## 核心功能模块

### 1. CTR/CVR 预测模块
- 当前稳定支持 LR；另包含一个轻量级神经网络 demo，用于模拟更复杂模型的接入方式
- `deepfm`/`xdeepfm` 在当前仓库中并非真实工业实现，更多是接口占位与实验演示
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
- 当前重点是离线仿真评估，不是线上投放系统，也不是对真实竞价日志的完整回放

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

说明：Avazu 提供点击标签，但不包含转化、成交价、竞争对手出价和真实预算消耗字段；因此当前流程仅使用 Avazu 训练 CTR 模型，再接入项目内的拍卖仿真环境评估策略。

这意味着：
- 该实验可以证明“真实 CTR 数据训练链路可运行”
- 但不能证明“真实线上竞价回放”或“真实 ROI/成本评估”
- 涉及 CVR、market price、win rate 的部分，当前仍来自仿真环境而非 Avazu 原始数据

### 训练模型

```bash
python3 scripts/quick_start.py
python3 scripts/main.py
python3 scripts/run_channel_allocation.py
python3 scripts/run_uplift_experiment.py
python3 scripts/run_multi_seed_experiment.py
```

实验设计、结果解读和当前局限见 [EXPERIMENTS.md](EXPERIMENTS.md)。

## 当前边界

- 这是一个离线策略仿真项目，不是线上广告系统实现
- 真实数据接入目前主要覆盖 CTR 训练，不覆盖真实成交价回放
- 当前 `deepfm` 是轻量级 demo，不应表述为完整 DeepFM 工业实现
- 项目更适合展示策略思路、实验设计和工程抽象，而不是宣称“完整复现生产广告平台”

## 贡献指南

欢迎提交 Issue 和 Pull Request!

## 许可证

MIT License
