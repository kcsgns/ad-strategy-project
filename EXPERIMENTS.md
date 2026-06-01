# 实验报告

项目名称：面向 ROI 约束的离线广告策略仿真与评估系统

项目简介：基于公开 CTR 数据与离线拍卖仿真的广告策略评估项目，支持 pCTR 出价、ROI 约束竞价、预算 pacing 和 bid landscape 实验。

## 1. 实验目标

本项目评估广告投放中的几类出价策略：

- `fixed`: 固定出价 baseline。
- `ecpm`: 线性 pCTR 出价，`bid = base_bid * pCTR / avgCTR`。
- `conversion`: 按预期转化价值出价，`bid = pCTR * pCVR * conversion_value / target_roi`。
- `roi_constraint`: 用预期转化价值和 ROI threshold 限制最高出价。
- `landscape_roi`: 在 ROI 约束基础上引入 bid landscape / win-rate 估计，选择期望利润更高的出价。

实验重点不是只追求 AUC，而是验证模型分数如何影响最终业务指标：消耗、胜出数、点击、转化、GMV、ROI/ROAS、eCPA、LTV 价值和预算利用率。

需要强调的是：本项目的核心价值在于“离线实验框架和策略比较”，而不是对真实广告投放日志做严格回放。

## 2. 数据与仿真设置

### Synthetic 实验

Synthetic 数据用于端到端验证。训练数据和拍卖环境使用同一套 CTR/CVR 生成机制，因此 CTR/CVR 模型学到的模式可以迁移到仿真流量。

这类实验适合验证：

- 策略实现是否正确
- 模型分数是否会通过出价逻辑影响业务指标
- 预算控制、拍卖机制和指标统计链路是否闭环

但它不能替代真实 RTB 日志上的离线 replay 评估。

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

更具体地说：

- CTR 特征与点击标签来自真实公开数据
- CVR、conversion value、market price、win-rate 估计来自项目内仿真环境
- 因此该流程更适合说明“真实 CTR 数据训练与策略链路打通”，而不是说明“真实成本与 ROI 已被准确离线评估”

### 电商价值体系

最新仿真环境不再使用固定转化价值，而是为每次广告机会生成：

- `user_segment`: low/mid/high value 用户分层。
- `traffic_channel`: search、recommendation、short_video、live_commerce、shelf。
- `item_price`: 商品价格。
- `ltv_score`: 用户长期价值 proxy。
- `conversion_value`: 当次成交 GMV 与 LTV 的加权价值。

因此策略指标同时包含 GMV、ROAS、AOV、高价值用户赢量占比等，更贴近电商智能营销场景。

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

但这里的 bid landscape 仍然是仿真估计，不是基于真实 win notice / pay price 日志训练得到的生产级模型。

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

这些结论成立的前提是：训练分布与仿真分布存在一致性，因此更适合作为机制验证，不应直接外推为真实线上结论。

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

因此，这组结果更适合被描述为“工程 smoke test + 策略方向性观察”，不适合被描述为真实线上效果排序。

### 多场景预算分配

运行命令：

```bash
python3 scripts/run_channel_allocation.py
```

该实验比较四种预算分配方法：

- `uniform`: 各场景平均分配。
- `traffic`: 按流量规模分配。
- `value`: 按单次曝光预期价值分配。
- `roi`: 按预估 ROI 分配。

它把项目从单一广告竞价扩展到多场景电商营销预算分配，对应搜索、推荐、短视频、直播和货架等不同流量入口。

### 补贴 Uplift 实验

运行命令：

```bash
python3 scripts/run_uplift_experiment.py
```

该实验比较：

- `pcvr`: 给最可能购买的人发补贴。
- `ltv`: 给长期价值最高的人发补贴。
- `uplift`: 给最可能被补贴撬动的人发补贴。
- `roi_uplift`: 按增量 GMV / 补贴成本排序。

这个实验用于说明营销算法为什么不能只看 CVR，还要看“补贴是否真的带来增量”。

### 多随机种子稳定性实验

运行命令：

```bash
python3 scripts/run_multi_seed_experiment.py
```

该脚本会对核心策略跑 5 个随机种子，并输出 `results/multi_seed_summary.csv`，包含 ROI、GMV、eCPA、转化数、预算利用率和高价值用户占比的均值与标准差。

## 5. 结论

当前项目已经能展示较完整的离线广告策略实验链路：

- 真实 CTR 数据训练。
- 多种出价策略对比。
- 预算 pacing。
- 第二价格拍卖模拟。
- bid landscape / win-rate 预估。
- GMV/LTV 用户价值体系。
- 多场景预算分配。
- 补贴 uplift 增量实验。
- 多随机种子稳定性评估。
- ROI、ROAS、eCPA、转化、消耗等业务指标评估。

但它的边界也要说清楚：

- 不是线上广告投放系统
- 不是基于真实成交价日志的严格 replay
- 不是生产级 DeepFM / DIN 建模实现

在简历或面试中，建议如实描述为：

> 基于公开 CTR 数据与离线拍卖仿真的广告策略评估项目，支持 pCTR 出价、转化价值出价、ROI 约束出价、bid landscape 感知出价、多场景预算分配与 uplift 补贴实验，并从 GMV/ROI/ROAS/eCPA/预算利用率等业务指标评估策略表现。

不要表述为“完整复现线上广告系统”或“使用真实成交价完成投放回放”，因为当前缺少真实市场价和转化标签。

## 6. 下一步

- 接入 iPinYou 这类包含 bid price / pay price / win notice 的 RTB 数据。
- 用真实 market price 训练 win-rate 模型，而不是只从仿真环境采样。
- 将类别特征从 hash 数值改为 embedding 或 one-hot + 稀疏模型。
- 将当前 `deepfm` demo 替换为真正的 DeepFM/xDeepFM/DIN。
- 将多随机种子结果进一步扩展为 95% 置信区间和显著性检验。
