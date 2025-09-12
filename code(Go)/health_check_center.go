package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/sirupsen/logrus"
)

// HealthCheckCenter 运行体检中心 - 定时检测系统运行指标
type HealthCheckCenter struct {
	BaseURL        string
	MetricsToCheck []string
	HTTPClient     *http.Client
	Logger         *logrus.Logger
}

// Service 服务信息
type Service struct {
	Name        string   `json:"name"`
	DeployState string   `json:"deployState"`
	Health      string   `json:"health"`
	Deps        []string `json:"deps"`
}

// ServerResponse 服务器列表响应
type ServerResponse struct {
	Items []Service `json:"items"`
}

// MetricData 指标数据
type MetricData struct {
	Status string `json:"status"`
	Data   struct {
		ResultType string `json:"resultType"`
		Result     []struct {
			Metric struct {
				Name     string `json:"__name__"`
				Service  string `json:"service"`
				Version  string `json:"version"`
				Instance string `json:"instance"`
			} `json:"metric"`
			Values [][]interface{} `json:"values"`
		} `json:"result"`
	} `json:"data"`
}

// AlertData 告警数据
type AlertData struct {
	Service   string      `json:"service"`
	Metric    string      `json:"metric"`
	Timestamp string      `json:"timestamp"`
	Data      *MetricData `json:"data"`
	Severity  string      `json:"severity"`
}

// CheckResult 检测结果
type CheckResult struct {
	TotalChecks  int      `json:"total_checks"`
	AnomalyCount int      `json:"anomaly_count"`
	Services     []string `json:"services"`
}

// NewHealthCheckCenter 创建新的健康检查中心实例
func NewHealthCheckCenter(baseURL string) *HealthCheckCenter {
	if baseURL == "" {
		baseURL = "http://localhost:8080"
	}

	logger := logrus.New()
	logger.SetFormatter(&logrus.TextFormatter{
		FullTimestamp: true,
	})

	return &HealthCheckCenter{
		BaseURL:    baseURL,
		HTTPClient: &http.Client{Timeout: 30 * time.Second},
		Logger:     logger,
		MetricsToCheck: []string{
			"latency",
			"traffic",
			"errorRatio",
			"saturation",
		},
	}
}

// GetAllServices 获取所有服务列表
func (h *HealthCheckCenter) GetAllServices() ([]string, error) {
	url := fmt.Sprintf("%s/v1/servers", h.BaseURL)

	resp, err := h.HTTPClient.Get(url)
	if err != nil {
		h.Logger.WithError(err).Error("获取服务列表失败")
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		h.Logger.WithField("status_code", resp.StatusCode).Error("获取服务列表失败")
		return nil, fmt.Errorf("HTTP %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		h.Logger.WithError(err).Error("读取响应失败")
		return nil, err
	}

	var serverResp ServerResponse
	if err := json.Unmarshal(body, &serverResp); err != nil {
		h.Logger.WithError(err).Error("解析服务列表失败")
		return nil, err
	}

	var services []string
	for _, item := range serverResp.Items {
		services = append(services, item.Name)
	}

	h.Logger.WithField("services", services).Info("发现服务")
	return services, nil
}

// FetchMetricData 获取指定服务的指标数据
func (h *HealthCheckCenter) FetchMetricData(service, metric string, timeRangeHours int) (*MetricData, error) {
	if timeRangeHours == 0 {
		timeRangeHours = 1
	}

	// 计算时间范围
	endTime := time.Now().UTC()
	startTime := endTime.Add(-time.Duration(timeRangeHours) * time.Hour)

	// 格式化时间
	startStr := startTime.Format("2006-01-02T15:04:05Z")
	endStr := endTime.Format("2006-01-02T15:04:05Z")

	// 构建请求URL
	url := fmt.Sprintf("%s/v1/metrics/%s/%s", h.BaseURL, service, metric)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}

	// 添加查询参数
	q := req.URL.Query()
	q.Add("version", "v1.0.1")
	q.Add("start", startStr)
	q.Add("end", endStr)
	q.Add("granule", "5m")
	req.URL.RawQuery = q.Encode()

	resp, err := h.HTTPClient.Do(req)
	if err != nil {
		h.Logger.WithError(err).WithFields(logrus.Fields{
			"service": service,
			"metric":  metric,
		}).Error("获取指标数据失败")
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		h.Logger.WithFields(logrus.Fields{
			"service":     service,
			"metric":      metric,
			"status_code": resp.StatusCode,
		}).Error("获取指标数据失败")
		return nil, fmt.Errorf("HTTP %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var metricData MetricData
	if err := json.Unmarshal(body, &metricData); err != nil {
		h.Logger.WithError(err).WithFields(logrus.Fields{
			"service": service,
			"metric":  metric,
		}).Error("解析指标数据失败")
		return nil, err
	}

	if metricData.Status != "success" {
		h.Logger.WithFields(logrus.Fields{
			"service": service,
			"metric":  metric,
			"status":  metricData.Status,
		}).Warning("指标返回错误状态")
		return nil, fmt.Errorf("指标返回错误状态: %s", metricData.Status)
	}

	h.Logger.WithFields(logrus.Fields{
		"service": service,
		"metric":  metric,
	}).Info("成功获取指标数据")

	return &metricData, nil
}

// AnomalyDetection 异常检测 - 暂时写死返回异常
func (h *HealthCheckCenter) AnomalyDetection(metricData *MetricData) bool {
	// TODO: 这里后续会集成LangGraph + AI检测
	h.Logger.Info("执行异常检测...")

	// 暂时写死返回异常，用于测试告警流程
	return true // 总是返回异常
}

// TriggerAlert 触发告警 - 调用其他同学的告警模块
func (h *HealthCheckCenter) TriggerAlert(service, metric string, metricData *MetricData) {
	h.Logger.WithFields(logrus.Fields{
		"service": service,
		"metric":  metric,
	}).Warning("🚨 告警触发: 服务指标异常")

	// 构造告警数据
	alertData := AlertData{
		Service:   service,
		Metric:    metric,
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Data:      metricData,
		Severity:  "warning",
	}

	// 这里调用其他同学的告警模块
	// TODO: 替换为真实的告警模块调用
	h.mockAlertHandler(alertData)
}

// mockAlertHandler 模拟告警处理函数
func (h *HealthCheckCenter) mockAlertHandler(alertData AlertData) {
	fmt.Printf("📢 告警处理: %s/%s 在 %s 发生异常\n",
		alertData.Service, alertData.Metric, alertData.Timestamp)
	// 这里可以添加告警发送逻辑（邮件、短信、钉钉等）
}

// HealthCheckWorkflow 运行体检中心主流程
func (h *HealthCheckCenter) HealthCheckWorkflow() (*CheckResult, error) {
	h.Logger.Info("🏥 开始运行体检中心检测...")

	// 1. 服务发现
	services, err := h.GetAllServices()
	if err != nil {
		h.Logger.WithError(err).Error("未发现任何服务，退出检测")
		return nil, err
	}

	if len(services) == 0 {
		h.Logger.Error("未发现任何服务，退出检测")
		return nil, fmt.Errorf("未发现任何服务")
	}

	// 2. 遍历服务和指标进行检测
	totalChecks := 0
	anomalyCount := 0

	for _, service := range services {
		h.Logger.WithField("service", service).Info("🔍 检测服务")

		for _, metric := range h.MetricsToCheck {
			totalChecks++
			h.Logger.WithFields(logrus.Fields{
				"service": service,
				"metric":  metric,
			}).Info("📊 检测指标")

			// 3. 获取指标数据
			metricData, err := h.FetchMetricData(service, metric, 1)
			if err != nil {
				h.Logger.WithError(err).WithFields(logrus.Fields{
					"service": service,
					"metric":  metric,
				}).Error("获取指标数据失败")
				continue
			}

			// 4. 异常检测
			isAnomaly := h.AnomalyDetection(metricData)

			// 5. 告警处理
			if isAnomaly {
				anomalyCount++
				h.TriggerAlert(service, metric, metricData)
			}
		}
	}

	// 6. 输出检测总结
	h.Logger.WithFields(logrus.Fields{
		"total_checks":  totalChecks,
		"anomaly_count": anomalyCount,
	}).Info("✅ 检测完成")

	result := &CheckResult{
		TotalChecks:  totalChecks,
		AnomalyCount: anomalyCount,
		Services:     services,
	}

	return result, nil
}

// RunContinuousCheck 持续运行体检中心（定时检测）
func (h *HealthCheckCenter) RunContinuousCheck(intervalMinutes int) {
	if intervalMinutes == 0 {
		intervalMinutes = 5
	}

	h.Logger.WithField("interval_minutes", intervalMinutes).Info("🔄 启动持续检测模式")

	for {
		startTime := time.Now()

		// 执行检测
		result, err := h.HealthCheckWorkflow()
		if err != nil {
			h.Logger.WithError(err).Error("检测失败")
		} else {
			h.Logger.WithFields(logrus.Fields{
				"total_checks":  result.TotalChecks,
				"anomaly_count": result.AnomalyCount,
			}).Info("检测完成")
		}

		// 计算下次检测时间
		elapsedTime := time.Since(startTime)
		sleepTime := time.Duration(intervalMinutes)*time.Minute - elapsedTime

		if sleepTime > 0 {
			h.Logger.WithField("sleep_seconds", sleepTime.Seconds()).Info("⏰ 等待后进行下次检测...")
			time.Sleep(sleepTime)
		} else {
			h.Logger.Warning("⚠️ 检测耗时过长，立即开始下次检测")
		}
	}
}
