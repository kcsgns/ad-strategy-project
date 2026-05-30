#!/usr/bin/env python
"""下载公开的 CTR 数据集用于演示"""
import os
import urllib.request
import zipfile


def download_open_ctr_data(dest_dir='data/open_ctr'):
    """下载公开的 CTR 数据集"""
    print("正在下载公开 CTR 数据集...")
    
    # 创建目标目录
    os.makedirs(dest_dir, exist_ok=True)
    
    # 使用公开可用的 CTR 数据集 (来自 UCI 或其他来源)
    # 这里使用一个小型的公开 CTR 数据集
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00468/online_shoppers_intention.csv"
    
    try:
        print(f"下载数据 from: {url}")
        file_path = os.path.join(dest_dir, 'online_shoppers.csv')
        urllib.request.urlretrieve(url, file_path)
        print(f"已下载到: {file_path}")
        
        # 转换为类似 Avazu 的格式
        import pandas as pd
        df = pd.read_csv(file_path)
        
        # 创建类 Avazu 格式的数据集
        avazu_like_df = pd.DataFrame()
        avazu_like_df['click'] = (df['Revenue']).astype(int)  # 用购买行为作为点击标签
        
        # Avazu hour 格式: YYMMDDHH (8位数字)
        month_map = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','June':'06','Jun':'06','Jul':'07','August':'08','Aug':'08','Sep':'09','Oct':'10','Nov':'11','December':'12','Dec':'12'}
        avazu_like_df['hour'] = '14' + df['Month'].astype(str).apply(lambda x: month_map.get(x, '01')) + '15' + df['Region'].astype(str).str.zfill(2)
        
        avazu_like_df['site_id'] = df['TrafficType'].astype(str)
        avazu_like_df['site_category'] = df['OperatingSystems'].astype(str)
        avazu_like_df['app_id'] = df['Browser'].astype(str)
        avazu_like_df['device_type'] = df['Weekend'].astype(str)  # 使用 Weekend 作为设备类型特征
        avazu_like_df['C1'] = df['Region'].astype(str)
        avazu_like_df['C2'] = df['TrafficType'].astype(str)
        
        # 保存为 train.csv 格式
        train_path = os.path.join(dest_dir, 'train.csv')
        avazu_like_df.to_csv(train_path, index=False)
        print(f"已转换为类 Avazu 格式: {train_path}")
        
        return train_path
        
    except Exception as e:
        print(f"下载失败: {e}")
        return None


if __name__ == '__main__':
    download_open_ctr_data()