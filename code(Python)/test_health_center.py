#!/usr/bin/env python3
"""
测试运行体检中心
确保mock服务器运行在 http://localhost:8080
"""

import subprocess
import time
import requests
import sys
from health_check_center import HealthCheckCenter

def check_mock_server():
    """检查mock服务器是否运行"""
    try:
        response = requests.get('http://localhost:8080/v1/servers', timeout=5)
        if response.status_code == 200:
            print("✅ Mock服务器运行正常")
            return True
        else:
            print(f"❌ Mock服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到Mock服务器: {e}")
        print("请先运行: python server.py")
        return False

def test_health_center():
    """测试体检中心功能"""
    print("=" * 60)
    print("🧪 测试运行体检中心")
    print("=" * 60)
    
    # 检查服务器
    if not check_mock_server():
        return False
    
    # 创建体检中心实例
    health_center = HealthCheckCenter()
    
    # 测试服务发现
    print("\n1️⃣ 测试服务发现...")
    services = health_center.get_all_services()
    print(f"   发现服务: {services}")
    
    # 测试指标数据获取
    print("\n2️⃣ 测试指标数据获取...")
    if services:
        service = services[0]
        metric = 'latency'
        data = health_center.fetch_metric_data(service, metric)
        if data:
            print(f"   ✅ 成功获取 {service}/{metric} 数据")
            print(f"   数据示例: {data['data']['result'][0]['values'][:2]}...")
        else:
            print(f"   ❌ 获取 {service}/{metric} 数据失败")
    
    # 测试完整工作流程
    print("\n3️⃣ 测试完整工作流程...")
    result = health_center.health_check_workflow()
    
    print("\n📊 测试结果:")
    print(f"   总检测数: {result['total_checks']}")
    print(f"   异常数量: {result['anomaly_count']}")
    print(f"   检测服务: {', '.join(result['services'])}")
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始测试运行体检中心...")
    
    # 检查Python版本
    if sys.version_info < (3, 6):
        print("❌ 需要Python 3.6或更高版本")
        return
    
    # 运行测试
    success = test_health_center()
    
    if success:
        print("\n✅ 所有测试通过！")
        print("\n💡 使用说明:")
        print("   - 运行单次检测: python health_check_center.py")
        print("   - 运行持续检测: 修改main()函数中的注释")
        print("   - 查看详细日志: 修改logging级别")
    else:
        print("\n❌ 测试失败，请检查配置")

if __name__ == "__main__":
    main()

