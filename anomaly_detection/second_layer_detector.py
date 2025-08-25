#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二层异常模式识别策略 - 简化版本
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from collections import defaultdict

class SecondLayerDetector:
    def __init__(self):
        self.patterns = []
        self.aggregations = []
        
    def load_data(self, file_path):
        """加载第一层结果"""
        print("Loading first layer results...")
        self.data = pd.read_csv(file_path)
        self.data['Time'] = pd.to_datetime(self.data['Time'])
        print(f"Loaded {len(self.data)} data points")
        
    def detect_spike_patterns(self):
        """检测尖峰模式"""
        spikes = []
        for i in range(1, len(self.data) - 1):
            current = self.data.iloc[i]
            if (current['anomaly_level'] != 'normal' and 
                self.data.iloc[i-1]['anomaly_level'] == 'normal' and
                self.data.iloc[i+1]['anomaly_level'] == 'normal'):
                spikes.append({
                    'time': current['Time'],
                    'value': current['Value'],
                    'score': current['anomaly_score'],
                    'type': 'spike'
                })
        return spikes
    
    def detect_trend_patterns(self, window_size=144):
        """检测趋势模式"""
        trends = []
        for i in range(0, len(self.data) - window_size, window_size//2):
            window = self.data.iloc[i:i+window_size]
            if len(window) < 10:
                continue
                
            # 线性回归检测趋势
            x = np.arange(len(window)).reshape(-1, 1)
            y = window['Value'].values
            reg = LinearRegression()
            reg.fit(x, y)
            
            # 计算异常比例
            anomaly_ratio = len(window[window['anomaly_level'] != 'normal']) / len(window)
            
            if abs(reg.coef_[0]) > 10 and anomaly_ratio > 0.2:
                trends.append({
                    'start_time': window.iloc[0]['Time'],
                    'end_time': window.iloc[-1]['Time'],
                    'slope': reg.coef_[0],
                    'anomaly_ratio': anomaly_ratio,
                    'type': 'trend'
                })
        return trends
    
    def aggregate_anomalies(self, window_size=144):
        """聚合异常"""
        aggregations = []
        for i in range(0, len(self.data) - window_size, window_size//2):
            window = self.data.iloc[i:i+window_size]
            anomalies = window[window['anomaly_level'] != 'normal']
            
            if len(anomalies) > 0:
                agg = {
                    'start_time': window.iloc[0]['Time'],
                    'end_time': window.iloc[-1]['Time'],
                    'anomaly_count': len(anomalies),
                    'anomaly_density': len(anomalies) / len(window),
                    'max_score': anomalies['anomaly_score'].max(),
                    'mean_score': anomalies['anomaly_score'].mean()
                }
                aggregations.append(agg)
        return aggregations
    
    def analyze_patterns(self):
        """分析所有模式"""
        print("Analyzing patterns...")
        
        # 检测尖峰模式
        spikes = self.detect_spike_patterns()
        self.patterns.extend(spikes)
        
        # 检测趋势模式
        trends = self.detect_trend_patterns()
        self.patterns.extend(trends)
        
        # 聚合异常
        self.aggregations = self.aggregate_anomalies()
        
        print(f"Detected {len(self.patterns)} patterns")
        print(f"Generated {len(self.aggregations)} aggregations")
        
    def create_visualizations(self):
        """创建可视化"""
        print("Creating visualizations...")
        
        # 模式时间线
        fig, ax = plt.subplots(figsize=(15, 8))
        ax.plot(self.data['Time'], self.data['Value'], 'b-', alpha=0.6, linewidth=1)
        
        # 标记模式
        colors = {'spike': 'red', 'trend': 'orange'}
        for pattern in self.patterns:
            time = pattern.get('time', pattern.get('start_time'))
            value = pattern.get('value', 0)
            ax.scatter(time, value, c=colors[pattern['type']], s=50, alpha=0.8)
        
        ax.set_title('Anomaly Patterns Timeline', fontsize=16, fontweight='bold')
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('second_layer_patterns.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # 聚合统计
        if self.aggregations:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            densities = [agg['anomaly_density'] for agg in self.aggregations]
            ax1.hist(densities, bins=20, alpha=0.7, color='skyblue')
            ax1.set_title('Anomaly Density Distribution')
            ax1.set_xlabel('Anomaly Density')
            ax1.set_ylabel('Frequency')
            
            counts = [agg['anomaly_count'] for agg in self.aggregations]
            ax2.hist(counts, bins=20, alpha=0.7, color='lightgreen')
            ax2.set_title('Anomaly Count Distribution')
            ax2.set_xlabel('Anomaly Count')
            ax2.set_ylabel('Frequency')
            
            max_scores = [agg['max_score'] for agg in self.aggregations]
            ax3.hist(max_scores, bins=20, alpha=0.7, color='lightcoral')
            ax3.set_title('Max Anomaly Score Distribution')
            ax3.set_xlabel('Max Score')
            ax3.set_ylabel('Frequency')
            
            mean_scores = [agg['mean_score'] for agg in self.aggregations]
            ax4.hist(mean_scores, bins=20, alpha=0.7, color='lightyellow')
            ax4.set_title('Mean Anomaly Score Distribution')
            ax4.set_xlabel('Mean Score')
            ax4.set_ylabel('Frequency')
            
            plt.tight_layout()
            plt.savefig('second_layer_aggregations.png', dpi=300, bbox_inches='tight')
            plt.show()
    
    def save_results(self):
        """保存结果"""
        # 保存模式
        patterns_df = pd.DataFrame(self.patterns)
        if not patterns_df.empty:
            patterns_df.to_csv('second_layer_patterns.csv', index=False)
        
        # 保存聚合
        aggregations_df = pd.DataFrame(self.aggregations)
        if not aggregations_df.empty:
            aggregations_df.to_csv('second_layer_aggregations.csv', index=False)
        
        print("Results saved to second_layer_*.csv")
    
    def print_summary(self):
        """打印摘要"""
        print("\n=== Second Layer Summary ===")
        print(f"Patterns detected: {len(self.patterns)}")
        print(f"Aggregations: {len(self.aggregations)}")
        
        if self.patterns:
            types = [p['type'] for p in self.patterns]
            type_counts = pd.Series(types).value_counts()
            print("\nPattern types:")
            for t, c in type_counts.items():
                print(f"  {t}: {c}")

def main():
    print("=== Second Layer Anomaly Detection ===")
    
    detector = SecondLayerDetector()
    detector.load_data('stl_anomaly_results.csv')
    detector.analyze_patterns()
    detector.create_visualizations()
    detector.save_results()
    detector.print_summary()
    
    print("=== Complete ===")

if __name__ == "__main__":
    main()
