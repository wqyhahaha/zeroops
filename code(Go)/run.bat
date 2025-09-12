@echo off
chcp 65001 >nul
echo ========================================
echo 🏥 Go语言运行体检中心
echo ========================================
echo.

REM 检查Go是否安装
go version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Go语言未安装或未添加到PATH
    echo 请先安装Go语言环境，参考 INSTALL.md
    pause
    exit /b 1
)

echo ✅ Go语言环境检查通过
echo.

REM 下载依赖
echo 📦 下载依赖...
go mod tidy
if %errorlevel% neq 0 (
    echo ❌ 依赖下载失败
    pause
    exit /b 1
)

echo ✅ 依赖下载完成
echo.

echo 请选择要运行的程序:
echo 1. 启动Mock服务器
echo 2. 运行健康检查启动脚本
echo 3. 运行测试
echo 4. 运行主程序
echo 5. 退出
echo.

set /p choice=请输入选择 (1-5): 

if "%choice%"=="1" (
    echo 🚀 启动Mock服务器...
    go run server.go
) else if "%choice%"=="2" (
    echo 🏥 运行健康检查启动脚本...
    go run run_health_center.go health_check_center.go
) else if "%choice%"=="3" (
    echo 🧪 运行测试...
    go run test_health_center.go health_check_center.go
) else if "%choice%"=="4" (
    echo 🏥 运行主程序...
    go run main.go health_check_center.go
) else if "%choice%"=="5" (
    echo 👋 再见！
    exit /b 0
) else (
    echo ❌ 无效选择
)

echo.
pause
