package main

import (
	"fmt"
	"net/http"
	"os"
	"runtime"
	"strings"
	"time"
)

// checkMockServer 检查mock服务器是否运行
func checkMockServer() bool {
	client := &http.Client{Timeout: 5 * time.Second}

	resp, err := client.Get("http://localhost:8080/v1/servers")
	if err != nil {
		fmt.Printf("❌ 无法连接到Mock服务器: %v\n", err)
		fmt.Println("请先运行: go run server.go")
		return false
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		fmt.Printf("❌ Mock服务器响应异常: %d\n", resp.StatusCode)
		return false
	}

	fmt.Println("✅ Mock服务器运行正常")
	return true
}

// testHealthCenter 测试体检中心功能
func testHealthCenter() bool {
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("🧪 测试运行体检中心")
	fmt.Println(strings.Repeat("=", 60))

	// 检查服务器
	if !checkMockServer() {
		return false
	}

	// 创建体检中心实例
	healthCenter := NewHealthCheckCenter("")

	// 测试服务发现
	fmt.Println("\n1️⃣ 测试服务发现...")
	services, err := healthCenter.GetAllServices()
	if err != nil {
		fmt.Printf("   ❌ 服务发现失败: %v\n", err)
		return false
	}
	fmt.Printf("   发现服务: %v\n", services)

	// 测试指标数据获取
	fmt.Println("\n2️⃣ 测试指标数据获取...")
	if len(services) > 0 {
		service := services[0]
		metric := "latency"

		data, err := healthCenter.FetchMetricData(service, metric, 1)
		if err != nil {
			fmt.Printf("   ❌ 获取 %s/%s 数据失败: %v\n", service, metric, err)
			return false
		}

		fmt.Printf("   ✅ 成功获取 %s/%s 数据\n", service, metric)
		if len(data.Data.Result) > 0 && len(data.Data.Result[0].Values) > 0 {
			fmt.Printf("   数据示例: %v...\n", data.Data.Result[0].Values[:2])
		}
	}

	// 测试完整工作流程
	fmt.Println("\n3️⃣ 测试完整工作流程...")
	result, err := healthCenter.HealthCheckWorkflow()
	if err != nil {
		fmt.Printf("   ❌ 工作流程失败: %v\n", err)
		return false
	}

	fmt.Println("\n📊 测试结果:")
	fmt.Printf("   总检测数: %d\n", result.TotalChecks)
	fmt.Printf("   异常数量: %d\n", result.AnomalyCount)
	fmt.Printf("   检测服务: %s\n", strings.Join(result.Services, ", "))

	return true
}

// checkGoVersion 检查Go版本
func checkGoVersion() bool {
	version := runtime.Version()
	fmt.Printf("🔍 Go版本: %s\n", version)

	// 检查是否是Go 1.16或更高版本
	if version < "go1.16" {
		fmt.Println("❌ 需要Go 1.16或更高版本")
		return false
	}

	return true
}

func main() {
	fmt.Println("🚀 开始测试运行体检中心...")

	// 检查Go版本
	if !checkGoVersion() {
		return
	}

	// 运行测试
	success := testHealthCenter()

	if success {
		fmt.Println("\n✅ 所有测试通过！")
		fmt.Println("\n💡 使用说明:")
		fmt.Println("   - 运行单次检测: go run health_check_center.go")
		fmt.Println("   - 运行持续检测: 修改main()函数中的注释")
		fmt.Println("   - 启动Mock服务器: go run server.go")
		fmt.Println("   - 运行启动脚本: go run run_health_center.go")
	} else {
		fmt.Println("\n❌ 测试失败，请检查配置")
		os.Exit(1)
	}
}
