"""
Avazu CTR 数据集加载器。

Avazu 的原始 Kaggle 文件只有点击标签，没有转化标签；因此这里用于训练 CTR
模型，后续策略仿真仍由本项目的拍卖环境补充成本、点击后转化等在线反馈。
"""
import hashlib
from typing import Tuple

import numpy as np
import pandas as pd


DEFAULT_DROP_COLUMNS = {'id', 'click'}


def _stable_hash(value: object, hash_bucket_size: int) -> float:
    """将高基数类别特征稳定映射到 [0, 1)。"""
    digest = hashlib.md5(str(value).encode('utf-8')).hexdigest()
    return (int(digest[:8], 16) % hash_bucket_size) / hash_bucket_size


def load_avazu_ctr_data(
    csv_path: str,
    nrows: int = None,
    hash_bucket_size: int = 100000,
) -> Tuple[pd.DataFrame, np.ndarray]:
    """读取 Avazu CTR CSV 并转换成模型可用的数值特征。

    Args:
        csv_path: Avazu `train.csv` 路径。
        nrows: 可选抽样行数，适合本地快速实验。
        hash_bucket_size: 类别特征哈希桶大小。

    Returns:
        (X, y_click)，其中 X 是数值型 DataFrame，y_click 是 0/1 点击标签。
    """
    df = pd.read_csv(csv_path, nrows=nrows)
    if 'click' not in df.columns:
        raise ValueError("Avazu data must contain a 'click' column")

    y_click = df['click'].astype(int).to_numpy()
    features = df.drop(columns=[col for col in DEFAULT_DROP_COLUMNS if col in df.columns]).copy()

    if 'hour' in features.columns:
        hour_text = features['hour'].astype(str).str.zfill(8)
        features['day'] = hour_text.str[4:6].astype(float)
        features['hour_of_day'] = hour_text.str[6:8].astype(float)
        features = features.drop(columns=['hour'])

    for col in features.columns:
        numeric = pd.to_numeric(features[col], errors='coerce')
        if numeric.notna().all():
            features[col] = numeric.astype(float)
        else:
            features[col] = features[col].map(lambda value: _stable_hash(value, hash_bucket_size))

    return features.astype(float), y_click
