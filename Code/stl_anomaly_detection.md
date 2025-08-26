# STL 异常检测模块使用说明

## 概述
`Code/stl_anomaly_detection.py` 基于 STL 分解对单指标时序进行点异常检测，并生成可视化与结构化结果。

## 输入
- 文件：`Data/yzh_mirror_data.csv`
  - 格式：分号分隔；包含列 `"Series";Time;Value`
  - Time：ISO 时间（含时区）
  - Value：数值型
- 参数（可选）：
  - `seasonal_period`：季节性周期（默认 144，表示 10 分钟采样的 24 小时周期）
  - `method`：异常分数计算方法（默认 `zscore`，可选 `iqr`、`modified_zscore`）

## 输出
- 结构化结果：`Data/stl_anomaly_results.csv`
  - 列：`Time,Value,trend,seasonal,residual,anomaly_score,anomaly_level`
  - `anomaly_level ∈ {normal, mild, moderate, severe}`
- 可视化（当前目录保存）：
  - `stl_analysis_results_stl_decomposition.png`
  - `stl_analysis_results_anomaly_scores.png`
  - `stl_analysis_results_anomaly_points.png`
  - `stl_analysis_results_residual_analysis.png`
- 终端摘要：输出总点数、各等级异常统计与阈值


