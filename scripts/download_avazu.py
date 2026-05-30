#!/usr/bin/env python
"""自动下载 Avazu CTR 数据集"""
import os
import shutil
import kagglehub


def download_avazu(dest_dir='data/avazu'):
    """下载 Avazu 数据集"""
    print("正在下载 Avazu CTR 数据集...")
    
    # 创建目标目录
    os.makedirs(dest_dir, exist_ok=True)
    
    # 下载数据集 (正确的 Kaggle 数据集名称)
    path = kagglehub.dataset_download('avazu/avazu-ctr-prediction')
    print(f"数据集下载到: {path}")
    
    # 找到 train.csv 文件
    import glob
    train_files = glob.glob(os.path.join(path, '*.csv'))
    
    if train_files:
        train_file = train_files[0]
        print(f"找到训练文件: {train_file}")
        
        # 复制到目标目录
        dest_path = os.path.join(dest_dir, 'train.csv')
        shutil.copy(train_file, dest_path)
        print(f"已复制到: {dest_path}")
        
        # 检查文件大小
        file_size = os.path.getsize(dest_path) / (1024 * 1024)
        print(f"文件大小: {file_size:.2f} MB")
        
        return dest_path
    else:
        print("未找到 train.csv 文件")
        return None


if __name__ == '__main__':
    download_avazu()