"""
模型训练模块
支持多种模型的训练、对比和评估
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from .ctr_predictor import CTRPredictor, CVRPredictor, create_predictor


class ModelTrainer:
    """模型训练器"""
    
    def __init__(self):
        self.models = {}
        self.results = {}
    
    def train_and_compare(
        self,
        X: pd.DataFrame,
        y_click: np.ndarray,
        y_conversion: np.ndarray = None,
        model_types: List[str] = ['lr', 'deepfm'],
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """训练并对比多个模型"""
        
        # 划分训练测试集
        if y_conversion is not None:
            X_train, X_test, y_click_train, y_click_test, y_conversion_train, y_conversion_test = train_test_split(
                X, y_click, y_conversion, test_size=test_size, random_state=random_state
            )
        else:
            X_train, X_test, y_click_train, y_click_test = train_test_split(
                X, y_click, test_size=test_size, random_state=random_state
            )
            y_conversion_train = None
            y_conversion_test = None
        
        # 训练和评估每个模型
        for model_type in model_types:
            print(f"\nTraining {model_type} model...")
            
            # CTR 预测
            predictor = create_predictor(model_type, input_dim=X_train.shape[1])
            predictor.fit(X_train, y_click_train)
            
            # 评估
            metrics = predictor.evaluate(X_test, y_click_test)
            print(f"{model_type} CTR Metrics: {metrics}")
            
            # 保存
            self.models[f'ctr_{model_type}'] = predictor
            self.results[f'ctr_{model_type}'] = metrics
            
            # CVR 预测 (如果有转化数据)
            if y_conversion is not None:
                cvr_predictor = CVRPredictor(model_type)
                cvr_predictor.fit(X_train, y_conversion_train, y_click_train)
                click_mask = y_click_test == 1
                cvr_metrics = cvr_predictor.evaluate(X_test[click_mask], y_conversion_test[click_mask])
                print(f"{model_type} CVR Metrics: {cvr_metrics}")
                
                self.models[f'cvr_{model_type}'] = cvr_predictor
                self.results[f'cvr_{model_type}'] = cvr_metrics
        
        return self.results
    
    def get_best_model(self, metric: str = 'auc') -> Tuple[str, CTRPredictor]:
        """获取最佳模型"""
        best_score = -1
        best_name = None
        best_model = None
        
        for name, metrics in self.results.items():
            if name.startswith('ctr_') and metrics[metric] > best_score:
                best_score = metrics[metric]
                best_name = name
                best_model = self.models[name]
        
        return best_name, best_model
    
    def plot_model_comparison(self, save_path: str = None):
        """绘制模型对比图"""
        model_names = []
        auc_scores = []
        logloss_scores = []
        
        for name, metrics in self.results.items():
            if name.startswith('ctr_'):
                model_names.append(name.replace('ctr_', ''))
                auc_scores.append(metrics['auc'])
                logloss_scores.append(metrics['logloss'])
        
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        
        # AUC 对比
        axes[0].bar(model_names, auc_scores, alpha=0.8, color='skyblue')
        axes[0].set_title('Model AUC Comparison')
        axes[0].set_ylabel('AUC')
        axes[0].set_ylim([max(0, min(auc_scores)-0.05), 1.0])
        for i, v in enumerate(auc_scores):
            axes[0].text(i, v + 0.01, f"{v:.4f}", ha='center')
        
        # Logloss 对比
        axes[1].bar(model_names, logloss_scores, alpha=0.8, color='lightcoral')
        axes[1].set_title('Model LogLoss Comparison')
        axes[1].set_ylabel('LogLoss')
        for i, v in enumerate(logloss_scores):
            axes[1].text(i, v + 0.01, f"{v:.4f}", ha='center')
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
        elif matplotlib.get_backend().lower() != 'agg':
            plt.show()
        plt.close()


def generate_synthetic_data(n_samples: int = 10000, n_features: int = 20,
                            random_state: int = 42) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """生成模拟数据"""
    rng = np.random.default_rng(random_state)
    
    # 生成特征
    X = rng.normal(0.0, 1.0, size=(n_samples, n_features))
    feature_names = [f'feature_{i}' for i in range(n_features)]
    X_df = pd.DataFrame(X, columns=feature_names)
    
    # 生成点击标签 (CTR 均值约 4%-6%)
    weight_rng = np.random.default_rng(random_state + 1009)
    w_click = weight_rng.normal(0.0, 0.55, n_features)
    logit_click = -3.1 + np.einsum('ij,j->i', X, w_click) / np.sqrt(n_features)
    logit_click += rng.normal(0.0, 0.35, n_samples)
    p_click = 1.0 / (1.0 + np.exp(-logit_click))
    y_click = rng.binomial(1, p_click)
    
    # 生成转化标签 (点击后 CVR 均值约 15%-25%)
    w_conv = weight_rng.normal(0.0, 0.8, n_features)
    logit_conv = -1.5 + np.einsum('ij,j->i', X, w_conv) / np.sqrt(n_features)
    logit_conv += rng.normal(0.0, 0.2, n_samples)
    p_conv = 1.0 / (1.0 + np.exp(-logit_conv))
    y_conversion = y_click * rng.binomial(1, p_conv)
    
    return X_df, y_click, y_conversion
