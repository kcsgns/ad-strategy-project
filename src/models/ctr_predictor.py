"""
CTR/CVR 预测模块
支持 DeepFM、xDeepFM、LR 等多种模型
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from sklearn.metrics import roc_auc_score, log_loss


class CTRPredictor:
    """CTR 预测器基类"""
    
    def __init__(self, model_type: str = 'lr'):
        self.model_type = model_type.lower()
        self.model = None
        self.feature_names = None
        self.is_trained = False
    
    def fit(self, X: pd.DataFrame, y: np.ndarray):
        """训练模型"""
        raise NotImplementedError
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测点击率"""
        raise NotImplementedError
    
    def evaluate(self, X: pd.DataFrame, y: np.ndarray) -> Dict[str, float]:
        """评估模型"""
        y_pred = self.predict(X)
        return {
            'auc': roc_auc_score(y, y_pred),
            'logloss': log_loss(y, y_pred)
        }


class LogisticRegressionPredictor(CTRPredictor):
    """逻辑回归预测器"""
    
    def __init__(self):
        super().__init__(model_type='lr')
        from sklearn.linear_model import LogisticRegression
        self.model = LogisticRegression(max_iter=1000, solver='liblinear')
    
    def fit(self, X: pd.DataFrame, y: np.ndarray):
        self.feature_names = X.columns.tolist()
        self.model.fit(X, y)
        self.is_trained = True
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Model not trained")
        return self.model.predict_proba(X)[:, 1]


class SimpleNNPredictor(CTRPredictor):
    """简单神经网络预测器 (模拟 DeepFM)"""
    
    def __init__(self, input_dim: int = 10, random_state: int = 42):
        super().__init__(model_type='deepfm')
        self.input_dim = input_dim
        rng = np.random.default_rng(random_state)
        self.weights = rng.normal(0.0, 0.01, input_dim)
        self.bias = 0.0
    
    def fit(self, X: pd.DataFrame, y: np.ndarray, epochs: int = 100, lr: float = 0.01):
        self.feature_names = X.columns.tolist()
        X_np = X.values
        
        # 简单的梯度下降训练
        for epoch in range(epochs):
            y_pred = self._sigmoid(np.einsum('ij,j->i', X_np, self.weights) + self.bias)
            error = y_pred - y
            # 更新权重
            self.weights -= lr * np.einsum('ij,i->j', X_np, error) / len(X)
            self.bias -= lr * np.mean(error)
        
        self.is_trained = True
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Model not trained")
        return self._sigmoid(np.einsum('ij,j->i', X.values, self.weights) + self.bias)
    
    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-np.clip(x, -10, 10)))


class CVRPredictor(CTRPredictor):
    """CVR 预测器 (与 CTR 类似，但目标不同)"""
    
    def __init__(self, model_type: str = 'lr'):
        super().__init__(model_type)
        self.ctr_predictor = None  # 可以依赖 CTR 预测
    
    def fit(self, X: pd.DataFrame, y_conversion: np.ndarray, y_click: np.ndarray = None):
        if y_click is not None:
            # 只在点击样本上训练 CVR
            click_mask = y_click == 1
            X_cvr = X[click_mask]
            y_cvr = y_conversion[click_mask]
        else:
            X_cvr = X
            y_cvr = y_conversion
        
        # 使用与 CTR 相同的逻辑
        from sklearn.linear_model import LogisticRegression
        self.model = LogisticRegression(max_iter=1000, solver='liblinear')
        self.feature_names = X.columns.tolist()
        self.model.fit(X_cvr, y_cvr)
        self.is_trained = True
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Model not trained")
        return self.model.predict_proba(X)[:, 1]


def create_predictor(model_type: str, **kwargs) -> CTRPredictor:
    """工厂函数创建预测器"""
    model_type = model_type.lower()
    
    if model_type == 'lr':
        return LogisticRegressionPredictor()
    elif model_type in ['deepfm', 'xdeepfm', 'nn']:
        return SimpleNNPredictor(**kwargs)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
