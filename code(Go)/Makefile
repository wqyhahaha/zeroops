# Makefile for Health Check Center

.PHONY: help build run test clean deps server mock-server

# 默认目标
help:
	@echo "可用的命令:"
	@echo "  deps        - 下载依赖"
	@echo "  build       - 构建所有程序"
	@echo "  server      - 启动Mock服务器"
	@echo "  run         - 运行启动脚本"
	@echo "  test        - 运行测试"
	@echo "  main        - 运行主程序"
	@echo "  clean       - 清理构建文件"
	@echo ""
	@echo "示例:"
	@echo "  make deps   # 下载依赖"
	@echo "  make server # 启动Mock服务器"
	@echo "  make run    # 运行健康检查"

# 下载依赖
deps:
	@echo "📦 下载依赖..."
	go mod tidy
	go mod download

# 构建所有程序
build: deps
	@echo "🔨 构建程序..."
	go build -o bin/health-center main.go health_check_center.go
	go build -o bin/server server.go
	go build -o bin/run-script run_health_center.go health_check_center.go
	go build -o bin/test test_health_center.go health_check_center.go

# 启动Mock服务器
server:
	@echo "🚀 启动Mock服务器..."
	go run server.go

# 运行启动脚本
run:
	@echo "🏥 运行健康检查启动脚本..."
	go run run_health_center.go health_check_center.go

# 运行主程序
main:
	@echo "🏥 运行健康检查主程序..."
	go run main.go health_check_center.go

# 运行测试
test:
	@echo "🧪 运行测试..."
	go run test_health_center.go health_check_center.go

# 清理构建文件
clean:
	@echo "🧹 清理构建文件..."
	rm -rf bin/
	go clean

# 检查代码格式
fmt:
	@echo "📝 格式化代码..."
	go fmt ./...

# 运行代码检查
vet:
	@echo "🔍 代码检查..."
	go vet ./...

# 运行所有检查
check: fmt vet test
	@echo "✅ 所有检查通过"

# 安装依赖并运行完整测试
all: deps check
	@echo "✅ 所有任务完成"
