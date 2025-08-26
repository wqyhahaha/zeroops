#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二层异常过滤规则实现
从第一层STL异常检测结果中筛选出真正的异常事件，减少误报
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import json

class SecondLayerFilter:
    def __init__(self, config: Dict = None):
        """初始化第二层过滤器"""
        self.config = config or self._get_default_config()
        self.anomaly_events = []
        self.daily_summary = {}
        
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            # 粗筛规则
            'min_score_for_mild': 2.0,  # mild异常的最小分数阈值
            
            # 事件合并规则
            'max_gap_minutes': 30,  # 相邻异常点最大间隔（分钟）
            
            # 事件分级规则
            'severe_thresholds': {
                'max_score': 3.0,  # 严重异常的最小分数
                'density': 0.1,    # 异常密度阈值（10%）
                'min_count': 5     # 最小异常点数量
            },
            'moderate_thresholds': {
                'max_score': 2.0,  # 中等异常的最小分数
                'density': 0.05,   # 异常密度阈值（5%）
                'min_count': 3     # 最小异常点数量
            },
            
            # 尖峰去噪规则
            'spike_threshold': 4.0,  # 尖峰保留阈值
            
            # 去重与限流规则
            'dedup_window_minutes': 60,  # 去重时间窗口（分钟）
            'max_daily_events': 5,       # 每日最大事件数
        }
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """加载第一层异常检测结果"""
        print(f"正在加载数据: {file_path}")
        
        df = pd.read_csv(file_path)
        df['Time'] = pd.to_datetime(df['Time'])
        df = df.sort_values('Time').reset_index(drop=True)
        
        print(f"数据加载完成，共 {len(df)} 个数据点")
        print(f"时间范围：{df['Time'].min()} 到 {df['Time'].max()}")
        
        return df
    
    def coarse_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """步骤1: 粗筛异常点"""
        print("执行粗筛过滤...")
        
        # 保留条件：severe和moderate异常，或mild异常但分数>=2.0
        mask = (
            (df['anomaly_level'].isin(['severe', 'moderate'])) |
            ((df['anomaly_level'] == 'mild') & (df['anomaly_score'] >= self.config['min_score_for_mild']))
        )
        
        filtered_df = df[mask].copy()
        
        print(f"粗筛前: {len(df)} 个数据点")
        print(f"粗筛后: {len(filtered_df)} 个数据点")
        print(f"过滤掉: {len(df) - len(filtered_df)} 个数据点")
        
        return filtered_df
    
    def merge_anomaly_events(self, df: pd.DataFrame) -> List[Dict]:
        """步骤2: 合并相邻异常为事件窗口"""
        print("合并异常事件...")
        
        if len(df) == 0:
            return []
        
        events = []
        current_event = {
            'start_time': df.iloc[0]['Time'],
            'end_time': df.iloc[0]['Time'],
            'anomaly_points': [df.iloc[0].to_dict()],
            'max_score': df.iloc[0]['anomaly_score'],
            'mean_score': df.iloc[0]['anomaly_score'],
            'anomaly_count': 1
        }
        
        max_gap = timedelta(minutes=self.config['max_gap_minutes'])
        
        for i in range(1, len(df)):
            current_time = df.iloc[i]['Time']
            last_time = current_event['end_time']
            
            # 检查时间间隔
            if current_time - last_time <= max_gap:
                # 合并到当前事件
                current_event['end_time'] = current_time
                current_event['anomaly_points'].append(df.iloc[i].to_dict())
                current_event['max_score'] = max(current_event['max_score'], df.iloc[i]['anomaly_score'])
                current_event['anomaly_count'] += 1
            else:
                # 结束当前事件，开始新事件
                scores = [point['anomaly_score'] for point in current_event['anomaly_points']]
                current_event['mean_score'] = np.mean(scores)
                current_event['window_length'] = len(current_event['anomaly_points'])
                current_event['anomaly_density'] = current_event['anomaly_count'] / current_event['window_length']
                
                events.append(current_event)
                
                # 开始新事件
                current_event = {
                    'start_time': current_time,
                    'end_time': current_time,
                    'anomaly_points': [df.iloc[i].to_dict()],
                    'max_score': df.iloc[i]['anomaly_score'],
                    'mean_score': df.iloc[i]['anomaly_score'],
                    'anomaly_count': 1
                }
        
        # 处理最后一个事件
        if current_event:
            scores = [point['anomaly_score'] for point in current_event['anomaly_points']]
            current_event['mean_score'] = np.mean(scores)
            current_event['window_length'] = len(current_event['anomaly_points'])
            current_event['anomaly_density'] = current_event['anomaly_count'] / current_event['window_length']
            events.append(current_event)
        
        print(f"合并后得到 {len(events)} 个异常事件")
        return events
    
    def classify_events(self, events: List[Dict]) -> List[Dict]:
        """步骤3: 事件分级与过滤"""
        print("执行事件分级...")
        
        classified_events = []
        
        for event in events:
            # 判断是否为严重事件
            is_severe = (
                event['max_score'] >= self.config['severe_thresholds']['max_score'] or
                (event['anomaly_density'] >= self.config['severe_thresholds']['density'] and 
                 event['anomaly_count'] >= self.config['severe_thresholds']['min_count'])
            )
            
            # 判断是否为中等事件
            is_moderate = (
                (self.config['moderate_thresholds']['max_score'] <= event['max_score'] < 
                 self.config['severe_thresholds']['max_score']) or
                (event['anomaly_density'] >= self.config['moderate_thresholds']['density'] and 
                 event['anomaly_count'] >= self.config['moderate_thresholds']['min_count'])
            )
            
            # 尖峰去噪：对于只有1-2个异常点的事件，需要更高的分数
            if event['anomaly_count'] <= 2:
                if event['max_score'] < self.config['spike_threshold']:
                    continue  # 丢弃低分尖峰
            
            # 确定事件等级
            if is_severe:
                event['severity_level'] = 'severe'
                classified_events.append(event)
            elif is_moderate:
                event['severity_level'] = 'moderate'
                classified_events.append(event)
            else:
                # 丢弃不符合条件的事件
                continue
        
        print(f"分级后保留 {len(classified_events)} 个事件")
        print(f"严重事件: {len([e for e in classified_events if e['severity_level'] == 'severe'])} 个")
        print(f"中等事件: {len([e for e in classified_events if e['severity_level'] == 'moderate'])} 个")
        
        return classified_events
    
    def deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """步骤4: 去重与限流"""
        print("执行去重与限流...")
        
        if not events:
            return []
        
        # 按日期分组
        daily_events = {}
        for event in events:
            date_key = event['start_time'].date()
            if date_key not in daily_events:
                daily_events[date_key] = []
            daily_events[date_key].append(event)
        
        deduplicated_events = []
        
        for date_key, day_events in daily_events.items():
            # 按严重程度和分数排序
            day_events.sort(key=lambda x: (
                x['severity_level'] == 'severe',  # severe优先
                x['max_score']  # 分数高的优先
            ), reverse=True)
            
            # 去重：相似时间段的事件只保留一个
            filtered_day_events = []
            dedup_window = timedelta(minutes=self.config['dedup_window_minutes'])
            
            for event in day_events:
                # 检查是否与已保留的事件时间重叠
                is_duplicate = False
                for kept_event in filtered_day_events:
                    if abs(event['start_time'] - kept_event['start_time']) < dedup_window:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    filtered_day_events.append(event)
            
            # 限制每日事件数量
            filtered_day_events = filtered_day_events[:self.config['max_daily_events']]
            
            deduplicated_events.extend(filtered_day_events)
            
            # 记录每日统计
            self.daily_summary[date_key] = {
                'total_events': len(day_events),
                'kept_events': len(filtered_day_events),
                'severe_count': len([e for e in filtered_day_events if e['severity_level'] == 'severe']),
                'moderate_count': len([e for e in filtered_day_events if e['severity_level'] == 'moderate'])
            }
        
        print(f"去重后保留 {len(deduplicated_events)} 个事件")
        return deduplicated_events
    
    def generate_alert_messages(self, events: List[Dict]) -> List[Dict]:
        """生成告警消息"""
        print("生成告警消息...")
        
        alert_messages = []
        
        for event in events:
            # 生成事件标题
            if event['severity_level'] == 'severe':
                title = f"[严重] 指标异常事件"
            else:
                title = f"[中等] 指标异常事件"
            
            # 生成时间窗口描述
            duration = event['end_time'] - event['start_time']
            if duration.total_seconds() <= 600:  # 10分钟内
                time_desc = f"{event['start_time'].strftime('%H:%M')}"
            else:
                time_desc = f"{event['start_time'].strftime('%H:%M')} - {event['end_time'].strftime('%H:%M')}"
            
            # 生成统计信息
            stats = f"异常点: {event['anomaly_count']}个, 密度: {event['anomaly_density']:.1%}, 最高分: {event['max_score']:.2f}"
            
            # 选择代表性数据点
            sample_points = []
            if event['anomaly_points']:
                # 选择分数最高的点
                max_score_point = max(event['anomaly_points'], key=lambda x: x['anomaly_score'])
                sample_points.append({
                    'time': max_score_point['Time'].strftime('%H:%M'),
                    'value': f"{max_score_point['Value']:.0f}",
                    'score': f"{max_score_point['anomaly_score']:.2f}"
                })
                
                # 如果有多个点，再选择一个
                if len(event['anomaly_points']) > 1:
                    # 选择时间最接近中间的点
                    mid_time = event['start_time'] + (event['end_time'] - event['start_time']) / 2
                    mid_point = min(event['anomaly_points'], 
                                  key=lambda x: abs(x['Time'] - mid_time))
                    sample_points.append({
                        'time': mid_point['Time'].strftime('%H:%M'),
                        'value': f"{mid_point['Value']:.0f}",
                        'score': f"{mid_point['anomaly_score']:.2f}"
                    })
            
            # 生成初步判断
            if event['anomaly_count'] == 1:
                hint = "孤立尖峰异常"
            elif event['anomaly_density'] > 0.5:
                hint = "持续性异常波动"
            else:
                hint = "间歇性异常"
            
            alert_message = {
                'title': title,
                'date': event['start_time'].strftime('%Y-%m-%d'),
                'time_window': time_desc,
                'stats': stats,
                'sample_points': sample_points,
                'hint': hint,
                'severity_level': event['severity_level'],
                'max_score': event['max_score']
            }
            
            alert_messages.append(alert_message)
        
        return alert_messages
    
    def process(self, file_path: str) -> Tuple[List[Dict], List[Dict]]:
        """执行完整的第二层过滤流程"""
        print("=" * 50)
        print("开始第二层异常过滤")
        print("=" * 50)
        
        # 步骤1: 加载数据
        df = self.load_data(file_path)
        
        # 步骤2: 粗筛过滤
        filtered_df = self.coarse_filter(df)
        
        # 步骤3: 合并事件
        events = self.merge_anomaly_events(filtered_df)
        
        # 步骤4: 事件分级
        classified_events = self.classify_events(events)
        
        # 步骤5: 去重限流
        final_events = self.deduplicate_events(classified_events)
        
        # 步骤6: 生成告警消息
        alert_messages = self.generate_alert_messages(final_events)
        
        print("=" * 50)
        print("第二层过滤完成")
        print("=" * 50)
        
        return final_events, alert_messages
    
    def save_results(self, events: List[Dict], alert_messages: List[Dict], output_dir: str = '.'):
        """保存结果到文件"""
        import os
        
        # 保存事件数据
        if events:
            events_df = pd.DataFrame([
                {
                    'start_time': event['start_time'],
                    'end_time': event['end_time'],
                    'anomaly_count': event['anomaly_count'],
                    'anomaly_density': event['anomaly_density'],
                    'max_score': event['max_score'],
                    'mean_score': event['mean_score'],
                    'severity_level': event['severity_level']
                }
                for event in events
            ])
            
            events_file = os.path.join(output_dir, 'second_layer_events.csv')
            events_df.to_csv(events_file, index=False)
            print(f"事件数据已保存到: {events_file}")
        
        # 保存告警消息
        if alert_messages:
            alerts_file = os.path.join(output_dir, 'alert_messages.json')
            with open(alerts_file, 'w', encoding='utf-8') as f:
                json.dump(alert_messages, f, ensure_ascii=False, indent=2)
            print(f"告警消息已保存到: {alerts_file}")
        
        # 保存每日统计
        if self.daily_summary:
            summary_file = os.path.join(output_dir, 'daily_summary.json')
            summary_str = {str(k): v for k, v in self.daily_summary.items()}
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_str, f, ensure_ascii=False, indent=2)
            print(f"每日统计已保存到: {summary_file}")
    
    def print_summary(self, events: List[Dict], alert_messages: List[Dict]):
        """打印处理摘要"""
        print("\n" + "=" * 50)
        print("处理摘要")
        print("=" * 50)
        
        print(f"最终事件数量: {len(events)}")
        if events:
            severe_count = len([e for e in events if e['severity_level'] == 'severe'])
            moderate_count = len([e for e in events if e['severity_level'] == 'moderate'])
            print(f"严重事件: {severe_count} 个")
            print(f"中等事件: {moderate_count} 个")
        
        print(f"告警消息数量: {len(alert_messages)}")
        
        if self.daily_summary:
            print("\n每日统计:")
            for date, stats in sorted(self.daily_summary.items()):
                print(f"  {date}: 总事件{stats['total_events']}个, 保留{stats['kept_events']}个 "
                      f"(严重{stats['severe_count']}个, 中等{stats['moderate_count']}个)")
        
        if alert_messages:
            print("\n告警消息预览:")
            for i, msg in enumerate(alert_messages[:3], 1):
                print(f"  {i}. {msg['title']} - {msg['date']} {msg['time_window']}")
                print(f"     {msg['stats']}")
                print(f"     {msg['hint']}")
            
            if len(alert_messages) > 3:
                print(f"  ... 还有 {len(alert_messages) - 3} 条消息")


def main():
    """主函数"""
    # 创建过滤器
    filter = SecondLayerFilter()
    
    # 处理数据
    events, alert_messages = filter.process('stl_anomaly_results.csv')
    
    # 保存结果
    filter.save_results(events, alert_messages)
    
    # 打印摘要
    filter.print_summary(events, alert_messages)


if __name__ == "__main__":
    main()
