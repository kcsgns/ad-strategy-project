# 项目设置指南

## 安装依赖

```bash
cd ad-strategy-project

# 使用 pip 安装依赖
pip3 install -r requirements.txt

# 或者使用 conda 创建环境
conda create -n ad-strategy python=3.8
conda activate ad-strategy
pip install -r requirements.txt
```

## 快速开始

### 1. 运行快速示例

```bash
python3 scripts/quick_start.py
```

这将：
- 生成模拟数据
- 训练简单的模型
- 创建几种策略
- 运行模拟
- 生成可视化结果

### 2. 运行完整流程

```bash
python3 scripts/main.py
```

### 3. 使用 Avazu 真实 CTR 数据

将 Kaggle Avazu `train.csv` 放到 `data/raw/avazu/train.csv`，然后运行：

```bash
python3 scripts/run_real_avazu.py --input data/raw/avazu/train.csv --nrows 100000
```

Avazu 只有点击标签，没有转化和成交价字段。本项目会用 Avazu 训练 CTR 模型，再把 CTR 分数接入现有拍卖仿真环境做策略对比。

### 4. 运行电商营销扩展实验

```bash
python3 scripts/run_channel_allocation.py
python3 scripts/run_uplift_experiment.py
python3 scripts/run_multi_seed_experiment.py
```

这些脚本分别用于多场景预算分配、补贴 uplift 增量评估和多随机种子稳定性实验。

## 项目文件说明

### 核心模块

- `src/models/` - CTR/CVR 预估模型
  - `ctr_predictor.py` - 模型定义
  - `model_trainer.py` - 模型训练和对比
  
- `src/strategies/` - 竞价策略
  - `base_strategy.py` - 策略基类
  - `random_strategy.py` - 随机/固定出价策略
  - `ecpm_strategy.py` - eCPM 策略
  - `conversion_strategy.py` - 转化目标策略
  - `roi_constraint_strategy.py` - ROI 约束策略
  
- `src/budget/` - 预算管理
  - `budget_manager.py` - 预算管理器
  
- `src/pacing/` - 预算 pacing
  - `pid_controller.py` - PID 控制器
  - `time_pacing.py` - 时间 pacing
  
- `src/simulation/` - 模拟环境
  - `auction_env.py` - 拍卖环境
  - `simulator.py` - 端到端模拟器

### 配置文件

- `config/model_config.yaml` - 模型配置
- `config/strategy_config.yaml` - 策略配置
- `config/budget_config.yaml` - 预算配置

### 脚本

- `scripts/quick_start.py` - 快速开始脚本
- `scripts/main.py` - 完整流程脚本

## 进阶使用

### 1. 集成 DeepCTR-Torch

```bash
pip install deepctr-torch
```

然后修改 `src/models/ctr_predictor.py` 集成真实的 DeepFM 模型。

### 2. 使用真实数据

可以使用：
- iPinYou 数据集
- Avazu 点击率预测数据集
- Ali-CCP 转化率预测数据集

### 3. 添加新策略

继承 `BaseStrategy` 类，实现 `calculate_bid` 方法。

### 4. 自定义实验

修改 `scripts/main.py` 添加更多策略或调整参数。

## 项目输出

运行后会在 `results/` 目录生成：
- `strategy_comparison.csv` - 策略对比表格
- `model_comparison.png` - 模型对比图
- `strategy_comparison_plot.png` - 策略对比可视化
- `time_series_plot.png` - 时间序列图

## 常见问题

### 1. 缺少模块

```bash
pip install numpy pandas scikit-learn matplotlib seaborn
```

### 2. 图无法显示

确保安装了 matplotlib，并且有 GUI 后端。
