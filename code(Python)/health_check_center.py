import requests
import json
from datetime import datetime, timezone, timedelta
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HealthCheckCenter:
    """运行体检中心 - 定时检测系统运行指标"""
    
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.metrics_to_check = [
            'latency',
            'traffic', 
            'errorRatio',
            'saturation'
        ]
        
    def get_all_services(self):
        """获取所有服务列表"""
        try:
            response = requests.get(f"{self.base_url}/v1/servers")
            response.raise_for_status()
            data = response.json()
            
            services = [item['name'] for item in data['items']]
            logger.info(f"发现服务: {services}")
            return services
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取服务列表失败: {e}")
            return []
    
    def fetch_metric_data(self, service, metric, time_range_hours=1):
        """获取指定服务的指标数据"""
        try:
            # 计算时间范围
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=time_range_hours)
            
            # 格式化时间
            start_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            end_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # 构建请求URL
            url = f"{self.base_url}/v1/metrics/{service}/{metric}"
            params = {
                'version': 'v1.0.1',
                'start': start_str,
                'end': end_str,
                'granule': '5m'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'success':
                logger.warning(f"服务 {service} 指标 {metric} 返回错误状态")
                return None
                
            logger.info(f"成功获取 {service}/{metric} 数据")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取 {service}/{metric} 数据失败: {e}")
            return None
    
    def anomaly_detection(self, metric_data):
        """异常检测 - 暂时写死返回异常"""
        # TODO: 这里后续会集成LangGraph + AI检测
        logger.info("执行异常检测...")
        
        # 暂时写死返回异常，用于测试告警流程
        return True  # 总是返回异常
    
    def trigger_alert(self, service, metric, metric_data):
        """触发告警 - 调用其他同学的告警模块"""
        logger.warning(f"🚨 告警触发: 服务 {service} 的 {metric} 指标异常")
        
        # 构造告警数据
        alert_data = {
            'service': service,
            'metric': metric,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': metric_data,
            'severity': 'warning'
        }
        
        # 这里调用其他同学的告警模块
        # TODO: 替换为真实的告警模块调用
        self._mock_alert_handler(alert_data)
    
    def _mock_alert_handler(self, alert_data):
        """模拟告警处理函数"""
        print(f"📢 告警处理: {alert_data['service']}/{alert_data['metric']} 在 {alert_data['timestamp']} 发生异常")
        # 这里可以添加告警发送逻辑（邮件、短信、钉钉等）
    
    def health_check_workflow(self):
        """运行体检中心主流程"""
        logger.info("🏥 开始运行体检中心检测...")
        
        # 1. 服务发现
        services = self.get_all_services()
        if not services:
            logger.error("未发现任何服务，退出检测")
            return
        
        # 2. 遍历服务和指标进行检测
        total_checks = 0
        anomaly_count = 0
        
        for service in services:
            logger.info(f"🔍 检测服务: {service}")
            
            for metric in self.metrics_to_check:
                total_checks += 1
                logger.info(f"  📊 检测指标: {metric}")
                
                # 3. 获取指标数据
                metric_data = self.fetch_metric_data(service, metric)
                if metric_data is None:
                    continue
                
                # 4. 异常检测
                is_anomaly = self.anomaly_detection(metric_data)
                
                # 5. 告警处理
                if is_anomaly:
                    anomaly_count += 1
                    self.trigger_alert(service, metric, metric_data)
        
        # 6. 输出检测总结
        logger.info(f"✅ 检测完成: 共检测 {total_checks} 个指标，发现 {anomaly_count} 个异常")
        
        return {
            'total_checks': total_checks,
            'anomaly_count': anomaly_count,
            'services': services
        }
    
    def run_continuous_check(self, interval_minutes=5):
        """持续运行体检中心（定时检测）"""
        logger.info(f"🔄 启动持续检测模式，间隔 {interval_minutes} 分钟")
        
        try:
            while True:
                start_time = time.time()
                
                # 执行检测
                result = self.health_check_workflow()
                
                # 计算下次检测时间
                elapsed_time = time.time() - start_time
                sleep_time = max(0, interval_minutes * 60 - elapsed_time)
                
                if sleep_time > 0:
                    logger.info(f"⏰ 等待 {sleep_time:.1f} 秒后进行下次检测...")
                    time.sleep(sleep_time)
                else:
                    logger.warning("⚠️ 检测耗时过长，立即开始下次检测")
                    
        except KeyboardInterrupt:
            logger.info("🛑 检测已停止")

def main():
    """主函数"""
    # 创建体检中心实例
    health_center = HealthCheckCenter()
    
    # 运行单次检测
    print("=" * 50)
    print("🏥 运行体检中心 - 单次检测")
    print("=" * 50)
    result = health_center.health_check_workflow()
    
    print("\n" + "=" * 50)
    print("📊 检测结果汇总:")
    print(f"  总检测数: {result['total_checks']}")
    print(f"  异常数量: {result['anomaly_count']}")
    print(f"  检测服务: {', '.join(result['services'])}")
    print("=" * 50)
    
    # 如果需要持续检测，取消下面的注释
    # health_center.run_continuous_check(interval_minutes=5)

if __name__ == "__main__":
    main()

