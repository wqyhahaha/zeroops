# Go语言运行体检中心 - 安装指南

## 系统要求

- Windows 10/11 (当前系统)
- 管理员权限（用于安装Go）

## 安装Go语言环境

### 1. 下载Go安装包

访问 [Go官网下载页面](https://golang.org/dl/) 或使用以下链接：

- **Windows 64位**: https://golang.org/dl/go1.21.5.windows-amd64.msi
- **Windows 32位**: https://golang.org/dl/go1.21.5.windows-386.msi

### 2. 安装Go

1. 下载对应版本的MSI安装包
2. 双击运行安装程序
3. 按照向导完成安装（建议使用默认安装路径：`C:\Program Files\Go`）
4. 安装完成后，Go会自动添加到系统PATH环境变量中

### 3. 验证安装

打开新的PowerShell窗口，运行以下命令验证安装：

```powershell
go version
```

如果显示Go版本信息（如 `go version go1.21.5 windows/amd64`），说明安装成功。

### 4. 配置Go环境（可选）

如果需要配置Go代理（提高依赖下载速度），运行：

```powershell
go env -w GOPROXY=https://goproxy.cn,direct
go env -w GOSUMDB=sum.golang.google.cn
```

## 安装项目依赖

安装Go后，在项目目录下运行：

```powershell
# 初始化Go模块并下载依赖
go mod tidy

# 验证依赖下载成功
go mod download
```

## 运行项目

### 1. 启动Mock服务器

```powershell
go run server.go
```

服务器将在 `http://localhost:8080` 启动。

### 2. 运行健康检查（新开一个PowerShell窗口）

```powershell
go run run_health_center.go health_check_center.go
```

### 3. 运行测试

```powershell
go run test_health_center.go health_check_center.go
```

## 使用Makefile（需要安装make工具）

如果您的系统安装了make工具，可以使用以下命令：

```powershell
# 下载依赖
make deps

# 启动服务器
make server

# 运行健康检查
make run

# 运行测试
make test
```

## 故障排除

### 问题1：`go: 无法将"go"项识别为 cmdlet`

**解决方案**：
1. 确认Go已正确安装
2. 重新打开PowerShell窗口
3. 检查PATH环境变量是否包含Go安装目录
4. 手动添加到PATH：`$env:PATH += ";C:\Program Files\Go\bin"`

### 问题2：网络连接问题

**解决方案**：
```powershell
# 设置Go代理
go env -w GOPROXY=https://goproxy.cn,direct
go env -w GOSUMDB=sum.golang.google.cn
```

### 问题3：端口被占用

**解决方案**：
```powershell
# 查看端口占用
netstat -ano | findstr :8080

# 终止占用进程（替换PID为实际进程ID）
taskkill /PID <PID> /F
```

## 开发环境推荐

### 推荐的IDE/编辑器

1. **Visual Studio Code** + Go扩展
   - 下载：https://code.visualstudio.com/
   - Go扩展：在VS Code中搜索并安装"Go"

2. **GoLand**（JetBrains）
   - 下载：https://www.jetbrains.com/go/

3. **Vim/Neovim** + vim-go插件

### 有用的Go命令

```powershell
# 格式化代码
go fmt ./...

# 代码检查
go vet ./...

# 运行测试
go test ./...

# 构建可执行文件
go build -o health-center.exe main.go health_check_center.go

# 交叉编译（编译为Linux版本）
set GOOS=linux
set GOARCH=amd64
go build -o health-center-linux main.go health_check_center.go
```

## 下一步

安装完成后，您可以：

1. 阅读 [README.md](README.md) 了解项目功能
2. 运行 `go run test_health_center.go health_check_center.go` 测试系统
3. 查看源代码了解实现细节
4. 根据需求扩展功能

## 技术支持

如果遇到问题，请检查：

1. Go版本是否为1.16或更高
2. 网络连接是否正常
3. 防火墙是否阻止了程序运行
4. 端口8080是否被其他程序占用
