from flask import Flask, request, jsonify
import time
from datetime import datetime, timezone
import random
app = Flask(__name__)

@app.route('/v1/metrics/<service>/<name>')
def get_metrics(service, name):
    # 获取查询参数
    version = request.args.get('version', 'v1.0.0')
    start = request.args.get('start')
    end = request.args.get('end')
    granule = request.args.get('granule', '5m')
    
    # 生成时间序列数据
    def generate_time_series():
        # 解析时间参数
        if start and end:
            start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end.replace('Z', '+00:00'))
        else:
            # 默认时间范围
            end_time = datetime.now(timezone.utc)
            start_time = datetime.fromtimestamp(end_time.timestamp() - 3600, timezone.utc)
        
        # 根据granule生成时间间隔
        if granule == '1m':
            interval = 60
        elif granule == '5m':
            interval = 300
        elif granule == '1h':
            interval = 3600
        else:
            interval = 300  # 默认5分钟
        
        # 生成时间点
        values = []
        current_time = start_time.timestamp()
        end_timestamp = end_time.timestamp()
        
        while current_time <= end_timestamp:
            # 生成随机值
            value = str(round(random.uniform(0.1, 1.0), 3))
            values.append([current_time, value])
            current_time += interval
        
        return values
    
    # 构造响应数据
    response_data = {
        "status": "success",
        "data": {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": name,
                        "service": service,
                        "version": "v1.0.1",
                        "instance": "localhost:8080"
                    },
                    "values": generate_time_series()
                },
                {
                    "metric": {
                        "__name__": name,
                        "service": service,
                        "version": version,
                        "instance": "localhost:8081"
                    },
                    "values": generate_time_series()
                }
            ]
        }
    }
    
    return jsonify(response_data)

@app.route("/v1/servers")
def get_servers():
    return_data = {
        "items": [
            {
                "name": "stg", 
                "deployState": "InDeploying", 
                "health": "Normal",  # 健康状态：Normal/Warning/Error
                "deps": ["stg", "meta", "mq"]
            },
            {
                "name": "meta", 
                "deployState": "InDeploying", 
                "health": "Normal",
                "deps": ["stg", "meta", "mq"]
            }
        ]
    }
    return jsonify(return_data)

if __name__ == '__main__':
    print("Mock server starting on http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)