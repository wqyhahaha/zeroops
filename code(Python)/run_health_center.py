#!/usr/bin/env python3
"""
运行体检中心启动脚本
"""

import subprocess
import time
import requests
import sys
import os
from health_check_center import HealthCheckCenter

def start_mock_server():
    """启动mock服务器"""
    print("🚀 启动Mock服务器...")
    try:
        # 检查服务器是否已经在运行
        response = requests.get('http://localhost:8080/v1/servers', timeout=2)
        print("✅ Mock服务器已在运行")
        return True
    except:
        # 启动新的服务器进程
        print("📡 启动新的Mock服务器进程...")
        process = subprocess.Popen([sys.executable, 'server.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # 等待服务器启动
        for i in range(10):
            time.sleep(1)
            try:
                response = requests.get('http://localhost:8080/v1/servers', timeout=2)
                if response.status_code == 200:
                    print("✅ Mock服务器启动成功")
                    return True
            except:
                continue
        
        print("❌ Mock服务器启动失败")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🏥 运行体检中心 - 启动脚本")
    print("=" * 60)
    
    # 启动mock服务器
    if not start_mock_server():
        print("❌ 无法启动Mock服务器，退出")
        return
    
    # 创建体检中心实例
    health_center = HealthCheckCenter()
    
    print("\n选择运行模式:")
    print("1. 单次检测")
    print("2. 持续检测 (每5分钟)")
    print("3. 自定义间隔持续检测")
    
    try:
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == "1":
            print("\n🔍 执行单次检测...")
            result = health_center.health_check_workflow()
            print(f"\n📊 检测完成: {result['total_checks']} 个指标, {result['anomaly_count']} 个异常")
            
        elif choice == "2":
            print("\n🔄 启动持续检测模式 (每5分钟)...")
            print("按 Ctrl+C 停止检测")
            health_center.run_continuous_check(interval_minutes=5)
            
        elif choice == "3":
            try:
                interval = int(input("请输入检测间隔(分钟): "))
                print(f"\n🔄 启动持续检测模式 (每{interval}分钟)...")
                print("按 Ctrl+C 停止检测")
                health_center.run_continuous_check(interval_minutes=interval)
            except ValueError:
                print("❌ 无效的间隔时间")
                
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n🛑 检测已停止")
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")

if __name__ == "__main__":
    main()
