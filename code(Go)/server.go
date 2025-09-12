package main

import (
	"fmt"
	"math/rand"
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
)

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

// MetricResponse 指标数据响应
type MetricResponse struct {
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

// generateTimeSeries 生成时间序列数据
func generateTimeSeries(startTime, endTime time.Time, granule string) [][]interface{} {
	var interval time.Duration

	switch granule {
	case "1m":
		interval = time.Minute
	case "5m":
		interval = 5 * time.Minute
	case "1h":
		interval = time.Hour
	default:
		interval = 5 * time.Minute // 默认5分钟
	}

	var values [][]interface{}
	currentTime := startTime

	for currentTime.Before(endTime) || currentTime.Equal(endTime) {
		// 生成随机值 (0.1 到 1.0)
		value := 0.1 + rand.Float64()*0.9
		values = append(values, []interface{}{float64(currentTime.Unix()), fmt.Sprintf("%.3f", value)})
		currentTime = currentTime.Add(interval)
	}

	return values
}

// parseTime 解析时间字符串
func parseTime(timeStr string) (time.Time, error) {
	// 移除Z后缀并添加时区信息
	if strings.HasSuffix(timeStr, "Z") {
		timeStr = strings.TrimSuffix(timeStr, "Z") + "+00:00"
	}

	// 尝试解析ISO 8601格式
	layouts := []string{
		"2006-01-02T15:04:05-07:00",
		"2006-01-02T15:04:05Z07:00",
		"2006-01-02T15:04:05",
	}

	for _, layout := range layouts {
		if t, err := time.Parse(layout, timeStr); err == nil {
			return t, nil
		}
	}

	return time.Time{}, fmt.Errorf("无法解析时间格式: %s", timeStr)
}

// getMetrics 获取指标数据
func getMetrics(c *gin.Context) {
	service := c.Param("service")
	metricName := c.Param("name")

	// 获取查询参数
	version := c.DefaultQuery("version", "v1.0.0")
	startStr := c.Query("start")
	endStr := c.Query("end")
	granule := c.DefaultQuery("granule", "5m")

	// 解析时间参数
	var startTime, endTime time.Time
	var err error

	if startStr != "" && endStr != "" {
		startTime, err = parseTime(startStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("无效的开始时间: %v", err)})
			return
		}

		endTime, err = parseTime(endStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("无效的结束时间: %v", err)})
			return
		}
	} else {
		// 默认时间范围（过去1小时）
		endTime = time.Now().UTC()
		startTime = endTime.Add(-time.Hour)
	}

	// 生成时间序列数据
	values := generateTimeSeries(startTime, endTime, granule)

	// 构造响应数据
	response := MetricResponse{
		Status: "success",
	}

	response.Data.ResultType = "matrix"
	response.Data.Result = []struct {
		Metric struct {
			Name     string `json:"__name__"`
			Service  string `json:"service"`
			Version  string `json:"version"`
			Instance string `json:"instance"`
		} `json:"metric"`
		Values [][]interface{} `json:"values"`
	}{
		{
			Metric: struct {
				Name     string `json:"__name__"`
				Service  string `json:"service"`
				Version  string `json:"version"`
				Instance string `json:"instance"`
			}{
				Name:     metricName,
				Service:  service,
				Version:  "v1.0.1",
				Instance: "localhost:8080",
			},
			Values: values,
		},
		{
			Metric: struct {
				Name     string `json:"__name__"`
				Service  string `json:"service"`
				Version  string `json:"version"`
				Instance string `json:"instance"`
			}{
				Name:     metricName,
				Service:  service,
				Version:  version,
				Instance: "localhost:8081",
			},
			Values: values,
		},
	}

	c.JSON(http.StatusOK, response)
}

// getServers 获取服务器列表
func getServers(c *gin.Context) {
	response := ServerResponse{
		Items: []Service{
			{
				Name:        "stg",
				DeployState: "InDeploying",
				Health:      "Normal", // 健康状态：Normal/Warning/Error
				Deps:        []string{"stg", "meta", "mq"},
			},
			{
				Name:        "meta",
				DeployState: "InDeploying",
				Health:      "Normal",
				Deps:        []string{"stg", "meta", "mq"},
			},
		},
	}

	c.JSON(http.StatusOK, response)
}

// healthCheck 健康检查端点
func healthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "healthy",
		"time":   time.Now().UTC().Format(time.RFC3339),
	})
}

func main() {
	// 设置随机种子
	rand.Seed(time.Now().UnixNano())

	// 创建Gin路由器
	r := gin.Default()

	// 添加中间件
	r.Use(gin.Logger())
	r.Use(gin.Recovery())

	// 添加CORS中间件
	r.Use(func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Origin, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	})

	// 路由配置
	r.GET("/v1/metrics/:service/:name", getMetrics)
	r.GET("/v1/servers", getServers)
	r.GET("/health", healthCheck)

	// 根路径
	r.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"message": "Mock Server for Health Check Center",
			"version": "1.0.0",
			"endpoints": gin.H{
				"metrics": "/v1/metrics/:service/:name",
				"servers": "/v1/servers",
				"health":  "/health",
			},
		})
	})

	// 启动服务器
	fmt.Println("Mock server starting on http://localhost:8080")
	fmt.Println("Available endpoints:")
	fmt.Println("  GET /v1/servers - 获取服务器列表")
	fmt.Println("  GET /v1/metrics/:service/:name - 获取指标数据")
	fmt.Println("  GET /health - 健康检查")
	fmt.Println("  GET / - 服务信息")

	if err := r.Run(":8080"); err != nil {
		fmt.Printf("启动服务器失败: %v\n", err)
	}
}
