#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析第二层异常检测结果
"""

import pandas as pd
import numpy as np

def analyze_second_layer_results():
    """分析第二层异常检测结果"""
    
    print("=== Second Layer Results Analysis ===\n")
    
    # 读取结果文件
    patterns_df = pd.read_csv('second_layer_patterns.csv')
    aggregations_df = pd.read_csv('second_layer_aggregations.csv')
    
    # 转换时间列
    patterns_df['time'] = pd.to_datetime(patterns_df['time'])
    aggregations_df['start_time'] = pd.to_datetime(aggregations_df['start_time'])
    aggregations_df['end_time'] = pd.to_datetime(aggregations_df['end_time'])
    
    print("1. 异常模式分析")
    print("=" * 50)
    print(f"总检测到的异常模式数量: {len(patterns_df)}")
    print(f"异常模式类型: {patterns_df['type'].unique()}")
    
    # 分析尖峰异常
    spike_patterns = patterns_df[patterns_df['type'] == 'spike']
    print(f"\n尖峰异常分析:")
    print(f"  数量: {len(spike_patterns)}")
    print(f"  异常分数范围: {spike_patterns['score'].min():.2f} - {spike_patterns['score'].max():.2f}")
    print(f"  平均异常分数: {spike_patterns['score'].mean():.2f}")
    print(f"  中位数异常分数: {spike_patterns['score'].median():.2f}")
    
    # 最严重的异常
    top_anomalies = spike_patterns.nlargest(5, 'score')
    print(f"\n最严重的5个尖峰异常:")
    for idx, row in top_anomalies.iterrows():
        print(f"  {row['time']}: 值={row['value']:.0f}, 分数={row['score']:.2f}")
    
    print("\n2. 异常聚合分析")
    print("=" * 50)
    print(f"总聚合窗口数量: {len(aggregations_df)}")
    print(f"聚合窗口时间跨度: {aggregations_df['start_time'].min()} 到 {aggregations_df['end_time'].max()}")
    
    # 异常密度分析
    print(f"\n异常密度分析:")
    print(f"  平均异常密度: {aggregations_df['anomaly_density'].mean():.3f}")
    print(f"  最大异常密度: {aggregations_df['anomaly_density'].max():.3f}")
    print(f"  最小异常密度: {aggregations_df['anomaly_density'].min():.3f}")
    
    # 异常数量分析
    print(f"\n异常数量分析:")
    print(f"  平均异常数量: {aggregations_df['anomaly_count'].mean():.1f}")
    print(f"  最大异常数量: {aggregations_df['anomaly_count'].max()}")
    print(f"  最小异常数量: {aggregations_df['anomaly_count'].min()}")
    
    # 异常分数分析
    print(f"\n异常分数分析:")
    print(f"  平均最大分数: {aggregations_df['max_score'].mean():.2f}")
    print(f"  平均平均分数: {aggregations_df['mean_score'].mean():.2f}")
    print(f"  最高最大分数: {aggregations_df['max_score'].max():.2f}")
    
    # 最严重的聚合窗口
    top_aggregations = aggregations_df.nlargest(3, 'max_score')
    print(f"\n最严重的3个聚合窗口:")
    for idx, row in top_aggregations.iterrows():
        print(f"  {row['start_time']} - {row['end_time']}:")
        print(f"    异常数量: {row['anomaly_count']}")
        print(f"    异常密度: {row['anomaly_density']:.3f}")
        print(f"    最大分数: {row['max_score']:.2f}")
        print(f"    平均分数: {row['mean_score']:.2f}")
    
    print("\n3. 时间分布分析")
    print("=" * 50)
    
    # 按日期分析
    patterns_df['date'] = patterns_df['time'].dt.date
    daily_counts = patterns_df['date'].value_counts().sort_index()
    
    print("每日异常模式数量:")
    for date, count in daily_counts.items():
        print(f"  {date}: {count} 个异常")
    
    # 按小时分析
    patterns_df['hour'] = patterns_df['time'].dt.hour
    hourly_counts = patterns_df['hour'].value_counts().sort_index()
    
    print(f"\n按小时分布的异常数量:")
    for hour, count in hourly_counts.items():
        print(f"  {hour:02d}:00: {count} 个异常")
    
    print("\n4. 报警建议")
    print("=" * 50)
    
    # 基于异常分数和密度的报警建议
    high_score_patterns = spike_patterns[spike_patterns['score'] > 3.0]
    high_density_aggregations = aggregations_df[aggregations_df['anomaly_density'] > 0.05]
    
    print(f"高分数异常模式 (>3.0): {len(high_score_patterns)} 个")
    if len(high_score_patterns) > 0:
        print("建议立即关注的异常:")
        for idx, row in high_score_patterns.iterrows():
            print(f"  {row['time']}: 分数={row['score']:.2f}, 值={row['value']:.0f}")
    
    print(f"\n高密度异常窗口 (>5%): {len(high_density_aggregations)} 个")
    if len(high_density_aggregations) > 0:
        print("建议重点监控的时间段:")
        for idx, row in high_density_aggregations.iterrows():
            print(f"  {row['start_time']} - {row['end_time']}: 密度={row['anomaly_density']:.3f}")
    
    print("\n5. 与第一层对比")
    print("=" * 50)
    
    # 读取第一层结果
    first_layer_df = pd.read_csv('stl_anomaly_results.csv')
    first_layer_df['Time'] = pd.to_datetime(first_layer_df['Time'])
    
    first_layer_anomalies = first_layer_df[first_layer_df['anomaly_level'] != 'normal']
    second_layer_patterns = len(patterns_df)
    
    print(f"第一层检测到的异常点: {len(first_layer_anomalies)}")
    print(f"第二层识别的异常模式: {second_layer_patterns}")
    print(f"模式识别率: {second_layer_patterns/len(first_layer_anomalies)*100:.1f}%")
    
    # 计算误报减少
    first_layer_severe = len(first_layer_df[first_layer_df['anomaly_level'] == 'severe'])
    second_layer_critical = len(high_score_patterns)
    
    print(f"\n第一层严重异常: {first_layer_severe}")
    print(f"第二层关键异常: {second_layer_critical}")
    print(f"误报减少: {(first_layer_severe - second_layer_critical)/first_layer_severe*100:.1f}%")
    
    print("\n=== Analysis Complete ===")

if __name__ == "__main__":
    analyze_second_layer_results()
