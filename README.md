# aiops
# 基于STL分解的异常值检测系统

这是一个基于STL（Seasonal and Trend decomposition using Loess）分解的异常值检测系统，使用百分位数方法识别时间序列数据中的异常值。

## 功能特点

- **STL分解**: 将时间序列分解为趋势、季节性和残差成分
- **百分位数检测**: 使用0.5%和99.5%百分位数作为异常值阈值
- **通用性**: 支持任意符合格式的CSV文件
- **JSON输出**: 以标准JSON格式输出异常信息
- **自动单位识别**: 根据指标名称自动识别单位

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 方法1: 直接运行主程序

```bash
python anomaly_detection.py
```

这将处理 `cpu_usage_percentage_filtered.csv` 文件并生成 `anomaly_results.json`。

### 方法2: 使用通用脚本

```bash
# 基本用法
python run_anomaly_detection.py your_data.csv

# 指定输出文件
python run_anomaly_detection.py your_data.csv -o results.json

# 自定义百分位数
python run_anomaly_detection.py your_data.csv --lower-percentile 1.0 --upper-percentile 99.0

# 显示详细信息
python run_anomaly_detection.py your_data.csv -v
```

### 方法3: 在代码中使用

```python
from anomaly_detection import AnomalyDetector

# 创建检测器
detector = AnomalyDetector(lower_percentile=0.5, upper_percentile=99.5)

# 处理文件
results = detector.process_file('your_data.csv')

# 输出结果
print(f"检测到 {results['total_anomalies']} 个异常值")
```

## 输入数据格式

CSV文件必须包含以下列：
- `name`: 指标名称
- `host`: 主机地址
- `time`: 时间戳（ISO格式）
- `value`: 数值

示例：
```csv
name,host,time,value
storage_service_cpu_usage_percentage,localhost:1080,2025-08-14T13:11:01+00:00,27.14198563
```

## 输出格式

系统输出JSON格式的异常信息，包含以下字段：

```json
{
  "total_anomalies": 10,
  "anomalies": [
    {
      "label": "PromQL",
      "host": "localhost:1080",
      "startTime": "2025-08-14T13:11:01+00:00",
      "endTime": "2025-08-14T13:11:01+00:00",
      "异常描述": "(storage_service_cpu_usage_percentage,百分比,偏高)",
      "original_value": 27.14198563,
      "residual": 2.5,
      "threshold": 1.8,
      "anomaly_type": "偏高"
    }
  ],
  "detection_params": {
    "lower_percentile": 0.5,
    "upper_percentile": 99.5,
    "method": "STL分解 + 百分位数检测"
  }
}
```

## 算法说明

1. **STL分解**: 将时间序列分解为趋势、季节性和残差成分
2. **残差分析**: 对残差成分进行异常检测
3. **百分位数阈值**: 使用0.5%和99.5%百分位数作为异常值边界
4. **异常判断**: 残差超出阈值范围的数据点被标记为异常

## 支持的指标类型

系统会自动识别以下指标类型并分配相应单位：
- CPU使用率: 百分比
- 内存使用: 字节
- 磁盘使用: 字节
- 网络流量: 字节/秒
- 响应时间: 毫秒
- 其他: 单位

## 注意事项

- 确保输入数据按时间顺序排列
- 数据量过少可能影响STL分解效果
- 可以根据实际需求调整百分位数阈值
- 系统会自动处理STL分解失败的情况，使用移动平均作为备选方案

