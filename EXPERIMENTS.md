# 实验报告

## 1. 实验目标

本项目评估广告投放中的几类出价策略：

- `fixed`: 固定出价 baseline。
- `ecpm`: 线性 pCTR 出价，`bid = base_bid * pCTR / avgCTR`。
- `conversion`: 按预期转化价值出价，`bid = pCTR * pCVR * conversion_value / target_roi`。
- `roi_constraint`: 用预期转化价值和 ROI threshold 限制最高出价。
- `landscape_roi`: 在 ROI 约束基础上引入 bid landscape / win-rate 估计，选择期望利润更高的出价。

实验重点不是只追求 AUC，而是验证模型分数如何影响最终业务指标：消耗、胜出数、点击、转化、ROI、eCPA 和预算利用率。

## 2. 数据与仿真设置

### Synthetic 实验

Synthetic 数据用于端到端验证。训练数据和拍卖环境使用同一套 CTR/CVR 生成机制，因此 CTR/CVR 模型学到的模式可以迁移到仿真流量。

运行命令：

```bash
python3 scripts/quick_start.py
```

### Avazu 真实 CTR 实验

Avazu 数据用于验证真实广告点击数据上的 CTR 训练链路。

运行命令：

```bash
python3 scripts/run_real_avazu.py --input data/avazu/train.csv --nrows 100000 --auctions 3000
```

注意：Avazu 只有点击标签，没有真实转化标签、成交价、竞争者出价和预算消耗。因此当前 Avazu 流程是“真实 CTR 模型 + 仿真拍卖环境”，不能被表述为完整真实线上竞价回放。

## 3. Bid Landscape / Win-Rate 预估

真实 RTB 系统除了估计 pCTR/pCVR，还需要估计市场价分布：

```text
win_rate(bid | traffic) = P(market_price <= bid | traffic)
```

本项目新增 `BidLandscapeEstimator`，通过离线采样竞争者最高价来近似 bid landscape：

1. 从拍卖环境采样广告机会。
2. 生成竞争者出价。
3. 记录 `market_price = max(competitor_bids, floor_price)`。
4. 按流量质量 `pCTR * (1 + 4 * pCVR)` 分桶。
5. 在每个桶中用经验分布估计给定 bid 的胜率。

`LandscapeROIStrategy` 在 ROI 约束允许的最高价内枚举候选 bid，用如下目标选择出价：

```text
expected_profit = win_rate(bid) * (expected_value - bid)
```

这比单纯按预期价值出价更接近真实系统，因为它显式考虑了“出这个价能不能赢”。

## 4. 实验结果

### Synthetic quick start

最近一次运行结果：

| strategy | total_spent | conversions | ROI | eCPA | budget_utilization |
|---|---:|---:|---:|---:|---:|
| landscape_roi | 1399.28 | 28 | 2.00 | 49.97 | 0.280 |
| roi_constraint | 1564.56 | 27 | 1.73 | 57.95 | 0.313 |
| fixed | 1475.84 | 25 | 1.69 | 59.03 | 0.295 |
| conversion | 1765.13 | 23 | 1.30 | 76.74 | 0.353 |
| ecpm | 1932.60 | 25 | 1.29 | 77.30 | 0.387 |

解读：

- `landscape_roi` ROI 最高，说明在已知市场价分布的仿真环境中，胜率预估可以帮助策略避开性价比不高的出价。
- `ecpm` 消耗最高但 ROI 较低，说明只按点击价值放量可能会买入过多高成本流量。
- `roi_constraint` 比普通 `conversion` 更稳，因为它限制了单位预期价值愿意支付的最高价格。

### Avazu real CTR experiment

最近一次运行读取到本地 Avazu 文件中的 12330 行样本，执行 3000 次拍卖：

| strategy | total_spent | conversions | ROI | eCPA | budget_utilization |
|---|---:|---:|---:|---:|---:|
| roi_constraint | 2040.05 | 39 | 1.91 | 52.31 | 0.408 |
| fixed | 1470.96 | 24 | 1.63 | 61.29 | 0.294 |
| ecpm | 2069.88 | 29 | 1.40 | 71.38 | 0.414 |
| conversion | 2054.23 | 26 | 1.27 | 79.01 | 0.411 |
| landscape_roi | 1993.94 | 25 | 1.25 | 79.76 | 0.399 |

解读：

- Avazu 流程验证了真实 CTR 数据加载、训练、预测和策略仿真的可运行性。
- `landscape_roi` 在这个 smoke test 中没有胜出，主要因为 Avazu 的真实 CTR 特征和仿真的 CVR/市场价没有真实联合分布；换句话说，bid landscape 是仿真的，CTR 是真实数据训练出来的，两者只是在工程链路上接通，还不是严格的真实拍卖回放。
- 这也是后续最值得增强的地方：使用带成交价的 RTB 数据集，例如 iPinYou，对 win-rate 和成本进行真实离线评估。

## 5. 结论

当前项目已经能展示完整广告策略实验链路：

- 真实 CTR 数据训练。
- 多种出价策略对比。
- 预算 pacing。
- 第二价格拍卖模拟。
- bid landscape / win-rate 预估。
- ROI、eCPA、转化、消耗等业务指标评估。

在简历或面试中，建议如实描述为：

> 基于 Avazu CTR 数据和离线拍卖仿真的广告投放策略评估系统，支持 pCTR 出价、转化价值出价、ROI 约束出价和 bid landscape 感知出价，并从 ROI/eCPA/预算利用率等业务指标评估策略表现。

不要表述为“完整复现线上广告系统”或“使用真实成交价完成投放回放”，因为当前缺少真实市场价和转化标签。

## 6. 下一步

- 接入 iPinYou 这类包含 bid price / pay price / win notice 的 RTB 数据。
- 用真实 market price 训练 win-rate 模型，而不是只从仿真环境采样。
- 将类别特征从 hash 数值改为 embedding 或 one-hot + 稀疏模型。
- 将当前 `deepfm` demo 替换为真正的 DeepFM/xDeepFM/DIN。
- 增加多随机种子实验，报告均值和置信区间，减少单次仿真的偶然性。
