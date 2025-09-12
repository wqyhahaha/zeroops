# 运行体检中心 - Go语言版本

这是一个用Go语言重写的运行体检中心系统，用于定时检测系统运行指标。

## 功能特性

- 🔍 自动服务发现
- 📊 多维度指标监控 (延迟、流量、错误率、饱和度)
- 🚨 智能异常检测与告警
- ⏰ 支持单次检测和持续检测模式
- 🌐 RESTful API接口
- 📝 详细的日志记录

## 项目结构

```
├── go.mod                    # Go模块依赖文件
├── main.go                   # 主程序入口
├── health_check_center.go    # 健康检查中心核心逻辑
├── server.go                 # Mock服务器
├── run_health_center.go      # 启动脚本
├── test_health_center.go     # 测试脚本
└── README.md                 # 说明文档
```

## 快速开始

### 1. 环境要求

- Go 1.16 或更高版本
- 网络连接（用于下载依赖）

### 2. 安装依赖

```bash
go mod tidy
```

### 3. 启动Mock服务器

```bash
go run server.go
```

服务器将在 `http://localhost:8080` 启动，提供以下API端点：

- `GET /v1/servers` - 获取服务器列表
- `GET /v1/metrics/:service/:name` - 获取指标数据
- `GET /health` - 健康检查
- `GET /` - 服务信息

### 4. 运行健康检查

#### 方式一：使用启动脚本（推荐）

```bash
go run run_health_center.go
```

然后选择运行模式：
1. 单次检测
2. 持续检测 (每5分钟)
3. 自定义间隔持续检测

#### 方式二：直接运行主程序

```bash
go run main.go
```

#### 方式三：运行测试

```bash
go run test_health_center.go
```

## API接口说明

### 获取服务器列表

```bash
curl http://localhost:8080/v1/servers
```

响应示例：
```json
{
  "items": [
    {
      "name": "stg",
      "deployState": "InDeploying",
      "health": "Normal",
      "deps": ["stg", "meta", "mq"]
    },
    {
      "name": "meta",
      "deployState": "InDeploying", 
      "health": "Normal",
      "deps": ["stg", "meta", "mq"]
    }
  ]
}
```

### 获取指标数据

```bash
curl "http://localhost:8080/v1/metrics/stg/latency?version=v1.0.1&start=2024-01-01T00:00:00Z&end=2024-01-01T01:00:00Z&granule=5m"
```

## 配置说明

### 环境变量

- `BASE_URL`: 服务器地址（默认：http://localhost:8080）
- `LOG_LEVEL`: 日志级别（默认：info）

### 检测指标

系统默认检测以下指标：
- `latency` - 延迟
- `traffic` - 流量  
- `errorRatio` - 错误率
- `saturation` - 饱和度

## 扩展开发

### 添加新的检测指标

在 `health_check_center.go` 中修改 `MetricsToCheck` 字段：

```go
MetricsToCheck: []string{
    "latency",
    "traffic", 
    "errorRatio",
    "saturation",
    "your_new_metric", // 添加新指标
},
```

### 自定义异常检测算法

修改 `AnomalyDetection` 方法，集成您的检测算法：

```go
func (h *HealthCheckCenter) AnomalyDetection(metricData *MetricData) bool {
    // TODO: 集成LangGraph + AI检测
    // 这里可以添加您的异常检测逻辑
    
    // 示例：基于阈值的检测
    // if metricValue > threshold {
    //     return true
    // }
    
    return false
}
```

### 集成告警系统

修改 `TriggerAlert` 方法，集成您的告警系统：

```go
func (h *HealthCheckCenter) TriggerAlert(service, metric string, metricData *MetricData) {
    // 调用您的告警API
    // 发送邮件、短信、钉钉通知等
    
    alertData := AlertData{
        Service:   service,
        Metric:    metric,
        Timestamp: time.Now().UTC().Format(time.RFC3339),
        Data:      metricData,
        Severity:  "warning",
    }
    
    // 发送告警
    // sendAlert(alertData)
}
```

## 日志说明

系统使用 `logrus` 进行日志记录，支持以下级别：
- `DEBUG` - 调试信息
- `INFO` - 一般信息  
- `WARN` - 警告信息
- `ERROR` - 错误信息

## 故障排除

### 常见问题

1. **服务器启动失败**
   - 检查端口8080是否被占用
   - 确认Go版本是否符合要求

2. **无法连接到Mock服务器**
   - 确认服务器已启动
   - 检查网络连接

3. **依赖下载失败**
   - 检查网络连接
   - 尝试设置Go代理：`go env -w GOPROXY=https://goproxy.cn,direct`

### 调试模式

设置环境变量启用详细日志：

```bash
export LOG_LEVEL=debug
go run main.go
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License
