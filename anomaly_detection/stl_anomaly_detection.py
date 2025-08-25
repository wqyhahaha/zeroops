#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STL分解异常检测
使用STL分解方法对yzh mirror时序数据进行异常检测
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.tsa.seasonal import STL
import warnings
import matplotlib.font_manager as fm
warnings.filterwarnings('ignore')

# 设置中文字体 - 更完善的字体配置
def setup_chinese_font():
    """设置中文字体显示"""
    # 尝试多种中文字体
    chinese_fonts = [
        'Hiragino Sans GB', # 冬青黑体 (macOS)
        'PingFang SC',      # 苹方 (macOS)
        'STHeiti',          # 华文黑体 (macOS)
        'SimHei',           # 黑体 (Windows)
        'Microsoft YaHei',  # 微软雅黑 (Windows)
        'Arial Unicode MS', # Arial Unicode
        'DejaVu Sans'       # 备用字体
    ]
    
    # 查找可用的中文字体
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    selected_font = None
    
    for font in chinese_fonts:
        if font in available_fonts:
            selected_font = font
            break
    
    if selected_font:
        plt.rcParams['font.sans-serif'] = [selected_font] + plt.rcParams['font.sans-serif']
        print(f"使用字体: {selected_font}")
    else:
        print("警告: 未找到合适的中文字体，可能显示为方块")
        # 使用系统默认字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    
    plt.rcParams['axes.unicode_minus'] = False

# 初始化字体设置
setup_chinese_font()

def load_and_preprocess_data(file_path):
    """加载和预处理数据"""
    print("正在加载数据...")
    
    # 读取CSV文件
    df = pd.read_csv(file_path, delimiter=';')
    
    # 清理列名
    df.columns = [col.strip().replace('"', '') for col in df.columns]
    
    # 转换时间列
    df['Time'] = pd.to_datetime(df['Time'])
    
    # 处理Value列，移除引号并转换为数值
    df['Value'] = df['Value'].astype(str).str.replace('"', '').astype(float)
    
    # 按时间排序
    df = df.sort_values('Time').reset_index(drop=True)
    
    # 检查缺失值
    missing_count = df['Value'].isnull().sum()
    if missing_count > 0:
        print(f"发现 {missing_count} 个缺失值，使用前向填充")
        df['Value'] = df['Value'].fillna(method='ffill')
    
    print(f"数据加载完成，共 {len(df)} 个数据点")
    print(f"时间范围：{df['Time'].min()} 到 {df['Time'].max()}")
    print(f"数值范围：{df['Value'].min():.2f} 到 {df['Value'].max():.2f}")
    
    return df

def perform_stl_decomposition(data, seasonal_period=144):
    """执行STL分解"""
    print("正在执行STL分解...")
    
    # 设置窗口大小
    trend_window = max(seasonal_period + 1, len(data) // 10)
    seasonal_window = max(7, seasonal_period // 2)
    # 确保窗口都是奇数
    if trend_window % 2 == 0:
        trend_window += 1
    if seasonal_window % 2 == 0:
        seasonal_window += 1
    
    print(f"趋势窗口大小: {trend_window}")
    print(f"季节性窗口大小: {seasonal_window}")
    print(f"季节性周期: {seasonal_period}")
    
    # 执行STL分解
    stl = STL(
        data['Value'], 
        period=seasonal_period,
        trend=trend_window,
        seasonal=seasonal_window,
        robust=True
    )
    
    stl_result = stl.fit()
    
    # 计算残差
    data['trend'] = stl_result.trend
    data['seasonal'] = stl_result.seasonal
    data['residual'] = stl_result.resid
    
    print("STL分解完成")
    
    return data, stl_result

def calculate_anomaly_scores(data, method='zscore'):
    """计算异常分数"""
    print(f"正在计算异常分数，使用 {method} 方法...")
    
    residuals = data['residual'].values
    
    if method == 'zscore':
        # 基于Z-Score的异常分数
        z_scores = np.abs(stats.zscore(residuals))
        anomaly_scores = z_scores
        
    elif method == 'iqr':
        # 基于IQR的异常分数
        Q1 = np.percentile(residuals, 25)
        Q3 = np.percentile(residuals, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # 计算到边界的距离
        distances = np.maximum(
            (lower_bound - residuals) / IQR,
            (residuals - upper_bound) / IQR
        )
        anomaly_scores = np.maximum(distances, 0)
        
    elif method == 'modified_zscore':
        # 基于Modified Z-Score的异常分数
        median = np.median(residuals)
        mad = np.median(np.abs(residuals - median))
        modified_z_scores = np.abs(0.6745 * (residuals - median) / mad)
        anomaly_scores = modified_z_scores
    
    # 将异常分数添加到数据中
    data['anomaly_score'] = anomaly_scores
    
    # 设置异常阈值
    thresholds = {
        'mild': np.percentile(anomaly_scores, 95),      # 95%分位数
        'moderate': np.percentile(anomaly_scores, 98),  # 98%分位数
        'severe': np.percentile(anomaly_scores, 99.5)   # 99.5%分位数
    }
    
    print(f"异常阈值设置完成:")
    print(f"  轻微异常: {thresholds['mild']:.3f}")
    print(f"  明显异常: {thresholds['moderate']:.3f}")
    print(f"  严重异常: {thresholds['severe']:.3f}")
    
    return data, thresholds

def detect_anomalies(data, thresholds):
    """检测异常点"""
    print("正在检测异常点...")
    
    # 标记异常点
    data['anomaly_level'] = 'normal'
    
    # 基于阈值标记异常
    data.loc[data['anomaly_score'] >= thresholds['severe'], 'anomaly_level'] = 'severe'
    data.loc[(data['anomaly_score'] >= thresholds['moderate']) & 
             (data['anomaly_score'] < thresholds['severe']), 'anomaly_level'] = 'moderate'
    data.loc[(data['anomaly_score'] >= thresholds['mild']) & 
             (data['anomaly_score'] < thresholds['moderate']), 'anomaly_level'] = 'mild'
    
    # 统计异常点
    anomaly_counts = data['anomaly_level'].value_counts()
    print("异常检测完成:")
    for level, count in anomaly_counts.items():
        print(f"  {level}: {count} 个点 ({count/len(data)*100:.2f}%)")
    
    return data

def create_visualizations(data, thresholds, save_path='stl_analysis_results'):
    """创建可视化图表"""
    print("正在生成可视化图表...")
    
    # 设置图表样式
    plt.style.use('default')
    sns.set_palette("husl")
    
    # 1. STL分解结果图
    plot_stl_decomposition(data, save_path)
    
    # 2. 异常分数分布图
    plot_anomaly_scores(data, thresholds, save_path)
    
    # 3. 异常点标记图
    plot_anomaly_points(data, save_path)
    
    # 4. 残差分析图
    plot_residual_analysis(data, save_path)
    
    print(f"可视化图表已保存到 {save_path}_*.png")

def plot_stl_decomposition(data, save_path):
    """绘制STL分解结果"""
    fig, axes = plt.subplots(4, 1, figsize=(15, 12))
    
    # 原始数据
    axes[0].plot(data['Time'], data['Value'], 'b-', linewidth=0.8)
    axes[0].set_title('Original Time Series Data', fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Value')
    axes[0].grid(True, alpha=0.3)
    
    # 趋势组件
    axes[1].plot(data['Time'], data['trend'], 'r-', linewidth=1.2)
    axes[1].set_title('Trend Component', fontsize=14, fontweight='bold')
    axes[1].set_ylabel('Trend Value')
    axes[1].grid(True, alpha=0.3)
    
    # 季节性组件
    axes[2].plot(data['Time'], data['seasonal'], 'g-', linewidth=0.8)
    axes[2].set_title('Seasonal Component', fontsize=14, fontweight='bold')
    axes[2].set_ylabel('Seasonal Value')
    axes[2].grid(True, alpha=0.3)
    
    # 残差组件
    axes[3].plot(data['Time'], data['residual'], 'purple', linewidth=0.8)
    axes[3].set_title('Residual Component', fontsize=14, fontweight='bold')
    axes[3].set_ylabel('Residual Value')
    axes[3].set_xlabel('Time')
    axes[3].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{save_path}_stl_decomposition.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_anomaly_scores(data, thresholds, save_path):
    """绘制异常分数分布"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 异常分数时间序列
    axes[0, 0].plot(data['Time'], data['anomaly_score'], 'b-', linewidth=0.8)
    axes[0, 0].axhline(y=thresholds['mild'], color='orange', linestyle='--', label='Mild Anomaly Threshold')
    axes[0, 0].axhline(y=thresholds['moderate'], color='red', linestyle='--', label='Moderate Anomaly Threshold')
    axes[0, 0].axhline(y=thresholds['severe'], color='darkred', linestyle='--', label='Severe Anomaly Threshold')
    axes[0, 0].set_title('Anomaly Score Time Series', fontsize=14, fontweight='bold')
    axes[0, 0].set_ylabel('Anomaly Score')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 异常分数分布直方图
    axes[0, 1].hist(data['anomaly_score'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    axes[0, 1].axvline(x=thresholds['mild'], color='orange', linestyle='--', label='Mild Anomaly Threshold')
    axes[0, 1].axvline(x=thresholds['moderate'], color='red', linestyle='--', label='Moderate Anomaly Threshold')
    axes[0, 1].axvline(x=thresholds['severe'], color='darkred', linestyle='--', label='Severe Anomaly Threshold')
    axes[0, 1].set_title('Anomaly Score Distribution', fontsize=14, fontweight='bold')
    axes[0, 1].set_xlabel('Anomaly Score')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 异常分数箱线图
    anomaly_data = [data[data['anomaly_level'] == level]['anomaly_score'].values 
                   for level in ['normal', 'mild', 'moderate', 'severe']]
    labels = ['Normal', 'Mild', 'Moderate', 'Severe']
    axes[1, 0].boxplot(anomaly_data, labels=labels)
    axes[1, 0].set_title('Anomaly Score Boxplot', fontsize=14, fontweight='bold')
    axes[1, 0].set_ylabel('Anomaly Score')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 异常等级统计
    anomaly_counts = data['anomaly_level'].value_counts()
    colors = ['lightgreen', 'orange', 'red', 'darkred']
    axes[1, 1].pie(anomaly_counts.values, labels=anomaly_counts.index, autopct='%1.1f%%', 
                  colors=colors, startangle=90)
    axes[1, 1].set_title('Anomaly Level Distribution', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{save_path}_anomaly_scores.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_anomaly_points(data, save_path):
    """绘制异常点标记图"""
    fig, axes = plt.subplots(2, 1, figsize=(15, 10))
    
    # 原始数据与异常点
    normal_data = data[data['anomaly_level'] == 'normal']
    mild_data = data[data['anomaly_level'] == 'mild']
    moderate_data = data[data['anomaly_level'] == 'moderate']
    severe_data = data[data['anomaly_level'] == 'severe']
    
    axes[0].plot(normal_data['Time'], normal_data['Value'], 'b-', linewidth=0.8, label='Normal Data')
    axes[0].scatter(mild_data['Time'], mild_data['Value'], c='orange', s=20, label='Mild Anomaly', alpha=0.7)
    axes[0].scatter(moderate_data['Time'], moderate_data['Value'], c='red', s=30, label='Moderate Anomaly', alpha=0.8)
    axes[0].scatter(severe_data['Time'], severe_data['Value'], c='darkred', s=40, label='Severe Anomaly', alpha=0.9)
    axes[0].set_title('Original Data with Anomaly Points', fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Value')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 残差与异常点
    axes[1].plot(normal_data['Time'], normal_data['residual'], 'b-', linewidth=0.8, label='Normal Residual')
    axes[1].scatter(mild_data['Time'], mild_data['residual'], c='orange', s=20, label='Mild Anomaly', alpha=0.7)
    axes[1].scatter(moderate_data['Time'], moderate_data['residual'], c='red', s=30, label='Moderate Anomaly', alpha=0.8)
    axes[1].scatter(severe_data['Time'], severe_data['residual'], c='darkred', s=40, label='Severe Anomaly', alpha=0.9)
    axes[1].axhline(y=0, color='black', linestyle='-', alpha=0.5)
    axes[1].set_title('Residuals with Anomaly Points', fontsize=14, fontweight='bold')
    axes[1].set_ylabel('Residual Value')
    axes[1].set_xlabel('Time')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{save_path}_anomaly_points.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_residual_analysis(data, save_path):
    """绘制残差分析图"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 残差分布直方图
    axes[0, 0].hist(data['residual'], bins=50, alpha=0.7, color='lightblue', edgecolor='black')
    axes[0, 0].set_title('Residual Distribution', fontsize=14, fontweight='bold')
    axes[0, 0].set_xlabel('Residual Value')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Q-Q图
    stats.probplot(data['residual'], dist="norm", plot=axes[0, 1])
    axes[0, 1].set_title('Residual Q-Q Plot', fontsize=14, fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 残差自相关图
    from statsmodels.graphics.tsaplots import plot_acf
    plot_acf(data['residual'].dropna(), lags=50, ax=axes[1, 0])
    axes[1, 0].set_title('Residual Autocorrelation', fontsize=14, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 残差与拟合值散点图
    fitted_values = data['trend'] + data['seasonal']
    axes[1, 1].scatter(fitted_values, data['residual'], alpha=0.6, s=10)
    axes[1, 1].axhline(y=0, color='red', linestyle='--')
    axes[1, 1].set_title('Residual vs Fitted Values', fontsize=14, fontweight='bold')
    axes[1, 1].set_xlabel('Fitted Values')
    axes[1, 1].set_ylabel('Residual Values')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{save_path}_residual_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """主函数"""
    print("=== STL分解异常检测 ===")
    
    # 加载数据
    data = load_and_preprocess_data('yzh_mirror_data.csv')
    
    # 执行STL分解
    data, stl_result = perform_stl_decomposition(data, seasonal_period=144)
    
    # 计算异常分数
    data, thresholds = calculate_anomaly_scores(data, method='zscore')
    
    # 检测异常点
    data = detect_anomalies(data, thresholds)
    
    # 创建可视化
    create_visualizations(data, thresholds)
    
    # 保存结果
    result_columns = ['Time', 'Value', 'trend', 'seasonal', 'residual', 
                     'anomaly_score', 'anomaly_level']
    data[result_columns].to_csv('stl_anomaly_results.csv', index=False)
    
    # 打印摘要
    print("\n=== 异常检测摘要 ===")
    anomaly_counts = data['anomaly_level'].value_counts()
    print(f"总数据点: {len(data)}")
    print(f"异常点统计:")
    for level, count in anomaly_counts.items():
        percentage = count / len(data) * 100
        print(f"  {level}: {count} 个点 ({percentage:.2f}%)")
    
    print(f"\n异常阈值:")
    for level, threshold in thresholds.items():
        print(f"  {level}: {threshold:.3f}")
    
    print("\n=== 分析完成 ===")
    print("结果已保存到 stl_anomaly_results.csv")

if __name__ == "__main__":
    main()
