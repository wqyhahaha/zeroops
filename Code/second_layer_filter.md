# 第二层异常过滤模块使用说明

## 概述
`Code/second_layer_filter.py` 对第一层输出进行规则化聚合，筛出“真正需要关注”的异常事件，并生成摘要与结构化结果。

## 输入
- 文件：`Data/stl_anomaly_results.csv`
  - 列：`Time,Value,trend,seasonal,residual,anomaly_score,anomaly_level`
  - `anomaly_level ∈ {normal, mild, moderate, severe}`
- 配置（类内默认，可按需修改）：
  - `min_score_for_mild=2.0`：mild 点的分数下限
  - `max_gap_minutes=30`：事件合并的点间隔
  - 严重判定：`max_score≥3.0` 或 `density≥0.1 & count≥5`
  - 中等判定：`2.0≤max_score<3.0` 或 `density≥0.05 & count≥3`
  - `spike_threshold=4.0`：1-2点窗口的尖峰最低分
  - `dedup_window_minutes=60`、`max_daily_events=5`

## 输出
- 事件列表：`Data/second_layer_events.csv`
  - 列：`start_time,end_time,anomaly_count,anomaly_density,max_score,mean_score,severity_level`
- 告警消息：`Data/alert_messages.json`
  - 每条包含：`title,date,time_window,stats,sample_points,hint,severity_level,max_score`
- 每日统计：`Data/daily_summary.json`

