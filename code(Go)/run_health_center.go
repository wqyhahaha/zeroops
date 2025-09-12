package main

import (
	"bufio"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"
)

// startMockServer 启动mock服务器
func startMockServer() bool {
	fmt.Println("🚀 启动Mock服务器...")

	// 检查服务器是否已经在运行
	client := &http.Client{Timeout: 2 * time.Second}
	resp, err := client.Get("http://localhost:8080/v1/servers")
	if err == nil && resp.StatusCode == 200 {
		fmt.Println("✅ Mock服务器已在运行")
		resp.Body.Close()
		return true
	}

	// 启动新的服务器进程
	fmt.Println("📡 启动新的Mock服务器进程...")
	cmd := exec.Command("go", "run", "server.go")

	// 设置输出
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	// 启动进程
	if err := cmd.Start(); err != nil {
		fmt.Printf("❌ 启动服务器进程失败: %v\n", err)
		return false
	}

	// 等待服务器启动
	fmt.Println("⏳ 等待服务器启动...")
	for i := 0; i < 10; i++ {
		time.Sleep(1 * time.Second)

		resp, err := client.Get("http://localhost:8080/v1/servers")
		if err == nil && resp.StatusCode == 200 {
			fmt.Println("✅ Mock服务器启动成功")
			resp.Body.Close()
			return true
		}
		if resp != nil {
			resp.Body.Close()
		}
	}

	fmt.Println("❌ Mock服务器启动失败")
	return false
}

// getInput 获取用户输入
func getInput(prompt string) string {
	fmt.Print(prompt)
	reader := bufio.NewReader(os.Stdin)
	input, _ := reader.ReadString('\n')
	return strings.TrimSpace(input)
}

// getIntInput 获取整数输入
func getIntInput(prompt string) (int, error) {
	input := getInput(prompt)
	return strconv.Atoi(input)
}

// runSingleCheck 运行单次检测
func runSingleCheck(healthCenter *HealthCheckCenter) {
	fmt.Println("\n🔍 执行单次检测...")

	result, err := healthCenter.HealthCheckWorkflow()
	if err != nil {
		fmt.Printf("❌ 检测失败: %v\n", err)
		return
	}

	fmt.Printf("\n📊 检测完成: %d 个指标, %d 个异常\n",
		result.TotalChecks, result.AnomalyCount)
}

// runContinuousCheck 运行持续检测
func runContinuousCheck(healthCenter *HealthCheckCenter, intervalMinutes int) {
	fmt.Printf("\n🔄 启动持续检测模式 (每%d分钟)...\n", intervalMinutes)
	fmt.Println("按 Ctrl+C 停止检测")

	// 设置信号处理
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// 启动持续检测的goroutine
	go func() {
		healthCenter.RunContinuousCheck(intervalMinutes)
	}()

	// 等待中断信号
	<-sigChan
	fmt.Println("\n🛑 检测已停止")
}

func main() {
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("🏥 运行体检中心 - 启动脚本")
	fmt.Println(strings.Repeat("=", 60))

	// 启动mock服务器
	if !startMockServer() {
		fmt.Println("❌ 无法启动Mock服务器，退出")
		return
	}

	// 创建体检中心实例
	healthCenter := NewHealthCheckCenter("")

	fmt.Println("\n选择运行模式:")
	fmt.Println("1. 单次检测")
	fmt.Println("2. 持续检测 (每5分钟)")
	fmt.Println("3. 自定义间隔持续检测")

	choice := getInput("\n请选择 (1-3): ")

	switch choice {
	case "1":
		runSingleCheck(healthCenter)

	case "2":
		runContinuousCheck(healthCenter, 5)

	case "3":
		interval, err := getIntInput("请输入检测间隔(分钟): ")
		if err != nil {
			fmt.Println("❌ 无效的间隔时间")
			return
		}
		runContinuousCheck(healthCenter, interval)

	default:
		fmt.Println("❌ 无效选择")
	}
}
