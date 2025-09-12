package main

import (
	"fmt"
	"os"
	"strings"
)

func main() {
	// 创建体检中心实例
	healthCenter := NewHealthCheckCenter("")

	// 运行单次检测
	fmt.Println(strings.Repeat("=", 50))
	fmt.Println("🏥 运行体检中心 - 单次检测")
	fmt.Println(strings.Repeat("=", 50))

	result, err := healthCenter.HealthCheckWorkflow()
	if err != nil {
		fmt.Printf("❌ 检测失败: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("\n" + "="*50)
	fmt.Println("📊 检测结果汇总:")
	fmt.Printf("  总检测数: %d\n", result.TotalChecks)
	fmt.Printf("  异常数量: %d\n", result.AnomalyCount)
	fmt.Printf("  检测服务: %s\n", strings.Join(result.Services, ", "))
	fmt.Println(strings.Repeat("=", 50))

	// 如果需要持续检测，取消下面的注释
	// fmt.Println("\n🔄 启动持续检测模式...")
	// fmt.Println("按 Ctrl+C 停止检测")
	//
	// // 设置信号处理
	// sigChan := make(chan os.Signal, 1)
	// signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	//
	// // 启动持续检测的goroutine
	// go func() {
	// 	healthCenter.RunContinuousCheck(5) // 每5分钟检测一次
	// }()
	//
	// // 等待中断信号
	// <-sigChan
	// fmt.Println("\n🛑 检测已停止")
}
