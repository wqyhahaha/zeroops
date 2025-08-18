#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用异常检测运行脚本
支持处理任意符合格式的CSV文件
"""

import sys
import os
import argparse
from anomaly_detection import AnomalyDetector

def main():
    parser = argparse.ArgumentParser(description='基于STL分解的异常值检测')
    parser.add_argument('input_file', help='输入的CSV文件路径')
    parser.add_argument('--output', '-o', default='anomaly_results.json', 
                       help='输出JSON文件路径 (默认: anomaly_results.json)')
    parser.add_argument('--lower-percentile', type=float, default=0.5,
                       help='下界百分位数 (默认: 0.5)')
    parser.add_argument('--upper-percentile', type=float, default=99.5,
                       help='上界百分位数 (默认: 99.5)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细信息')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input_file):
        print(f"错误: 文件 '{args.input_file}' 不存在")
        sys.exit(1)
    
    try:
        # 创建异常检测器
        detector = AnomalyDetector(
            lower_percentile=args.lower_percentile,
            upper_percentile=args.upper_percentile
        )
        
        if args.verbose:
            print(f"正在处理文件: {args.input_file}")
            print(f"检测参数: 下界{args.lower_percentile}%, 上界{args.upper_percentile}%")
        
        # 执行异常检测
        results = detector.process_file(args.input_file)
        
        # 保存结果
        with open(args.output, 'w', encoding='utf-8') as f:
            import json
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 输出统计信息
        print(f"检测完成!")
        print(f"总异常数: {results['total_anomalies']}")
        print(f"结果已保存到: {args.output}")
        
        if args.verbose and results['total_anomalies'] > 0:
            print("\n异常值详情:")
            for i, anomaly in enumerate(results['anomalies'][:5], 1):  # 只显示前5个
                print(f"  {i}. {anomaly['startTime']} - {anomaly['异常描述']}")
            if len(results['anomalies']) > 5:
                print(f"  ... 还有 {len(results['anomalies']) - 5} 个异常值")
        
    except Exception as e:
        print(f"处理失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

