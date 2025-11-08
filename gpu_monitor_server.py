#!/usr/bin/env python3
"""
GPU监控服务端 - 收集并展示所有服务器的GPU状态
运行方式: python gpu_monitor_server.py --port 5000
"""

from flask import Flask, render_template_string, jsonify, request
from datetime import datetime
import argparse
import threading
import time

app = Flask(__name__)

# 存储所有服务器的GPU信息
# 格式: {server_name: {timestamp: ..., gpus: [...], system_info: {...}}}
gpu_data = {}
# 数据过期时间（秒）
DATA_TIMEOUT = 60

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPU监控系统 - 实时监控</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .last-update {
            color: white;
            text-align: center;
            margin-bottom: 20px;
            font-size: 1.1em;
        }
        
        .server-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            animation: fadeIn 0.5s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .server-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }
        
        .server-name {
            font-size: 1.8em;
            color: #333;
            font-weight: bold;
        }
        
        .server-status {
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .status-online {
            background: #10b981;
            color: white;
        }
        
        .status-offline {
            background: #ef4444;
            color: white;
        }
        
        .gpu-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .gpu-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
            border-radius: 10px;
            padding: 20px;
            border-left: 5px solid #667eea;
        }
        
        .gpu-title {
            font-size: 1.2em;
            color: #333;
            margin-bottom: 15px;
            font-weight: bold;
        }
        
        .gpu-info {
            margin-bottom: 10px;
        }
        
        .info-label {
            display: inline-block;
            width: 120px;
            color: #666;
            font-weight: 600;
        }
        
        .info-value {
            color: #333;
            font-weight: 500;
        }
        
        .progress-bar {
            background: #e0e0e0;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin-top: 5px;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .progress-low {
            background: linear-gradient(90deg, #10b981 0%, #059669 100%);
        }
        
        .progress-medium {
            background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
        }
        
        .progress-high {
            background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
        }
        
        .no-data {
            text-align: center;
            color: white;
            font-size: 1.5em;
            margin-top: 50px;
        }
        
        .process-list {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 2px dashed #ccc;
        }
        
        .process-title {
            font-weight: bold;
            color: #666;
            margin-bottom: 10px;
        }
        
        .process-item {
            background: white;
            padding: 8px;
            margin: 5px 0;
            border-radius: 5px;
            font-size: 0.9em;
            display: flex;
            justify-content: space-between;
        }
        
        .process-name {
            color: #333;
            font-weight: 500;
        }
        
        .process-memory {
            color: #667eea;
            font-weight: bold;
        }
    </style>
    <script>
        // 每5秒刷新一次数据
        setInterval(function() {
            location.reload();
        }, 5000);
    </script>
</head>
<body>
    <div class="container">
        <h1>🖥️ GPU监控系统</h1>
        <div class="last-update">最后更新: {{ current_time }}</div>
        
        {% if servers %}
            {% for server_name, server_data in servers.items() %}
            <div class="server-card">
                <div class="server-header">
                    <div class="server-name">{{ server_name }}</div>
                    <div class="server-status {{ 'status-online' if server_data.online else 'status-offline' }}">
                        {{ '在线' if server_data.online else '离线' }}
                    </div>
                </div>
                
                {% if server_data.online %}
                    <div class="gpu-info" style="margin-bottom: 15px;">
                        <span class="info-label">更新时间:</span>
                        <span class="info-value">{{ server_data.timestamp }}</span>
                    </div>
                    
                    <div class="gpu-grid">
                        {% for gpu in server_data.gpus %}
                        <div class="gpu-card">
                            <div class="gpu-title">GPU {{ gpu.index }}: {{ gpu.name }}</div>
                            
                            <div class="gpu-info">
                                <span class="info-label">温度:</span>
                                <span class="info-value">{{ gpu.temperature }}°C</span>
                            </div>
                            
                            <div class="gpu-info">
                                <span class="info-label">GPU使用率:</span>
                                <span class="info-value">{{ gpu.utilization }}%</span>
                                <div class="progress-bar">
                                    <div class="progress-fill {{ 'progress-low' if gpu.utilization|int < 50 else ('progress-medium' if gpu.utilization|int < 80 else 'progress-high') }}" 
                                         style="width: {{ gpu.utilization }}%">
                                        {{ gpu.utilization }}%
                                    </div>
                                </div>
                            </div>
                            
                            <div class="gpu-info">
                                <span class="info-label">显存使用:</span>
                                <span class="info-value">{{ gpu.memory_used }} / {{ gpu.memory_total }}</span>
                                <div class="progress-bar">
                                    <div class="progress-fill {{ 'progress-low' if gpu.memory_percent|int < 50 else ('progress-medium' if gpu.memory_percent|int < 80 else 'progress-high') }}" 
                                         style="width: {{ gpu.memory_percent }}%">
                                        {{ gpu.memory_percent }}%
                                    </div>
                                </div>
                            </div>
                            
                            <div class="gpu-info">
                                <span class="info-label">功耗:</span>
                                <span class="info-value">{{ gpu.power_draw }} / {{ gpu.power_limit }}</span>
                            </div>
                            
                            {% if gpu.processes %}
                            <div class="process-list">
                                <div class="process-title">运行中的进程 ({{ gpu.processes|length }}):</div>
                                {% for proc in gpu.processes %}
                                <div class="process-item">
                                    <span class="process-name">{{ proc.name }} (PID: {{ proc.pid }})</span>
                                    <span class="process-memory">{{ proc.memory }}</span>
                                </div>
                                {% endfor %}
                            </div>
                            {% endif %}
                        </div>
                        {% endfor %}
                    </div>
                {% else %}
                    <div style="text-align: center; color: #666; padding: 20px;">
                        服务器超过60秒未更新数据
                    </div>
                {% endif %}
            </div>
            {% endfor %}
        {% else %}
            <div class="no-data">暂无服务器数据，请确保客户端正在运行</div>
        {% endif %}
    </div>
</body>
</html>
"""

def clean_old_data():
    """定期清理过期的服务器数据"""
    while True:
        current_time = time.time()
        offline_servers = []
        for server_name, data in gpu_data.items():
            if current_time - data.get('last_update', 0) > DATA_TIMEOUT:
                offline_servers.append(server_name)
        
        time.sleep(10)

@app.route('/')
def index():
    """主页面 - 显示所有服务器的GPU信息"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 准备数据
    servers = {}
    current_timestamp = time.time()
    
    for server_name, data in gpu_data.items():
        is_online = (current_timestamp - data.get('last_update', 0)) < DATA_TIMEOUT
        servers[server_name] = {
            'online': is_online,
            'timestamp': data.get('timestamp', 'N/A'),
            'gpus': data.get('gpus', [])
        }
    
    return render_template_string(HTML_TEMPLATE, 
                                 servers=servers,
                                 current_time=current_time)

@app.route('/api/update', methods=['POST'])
def update_gpu_data():
    """接收客户端发送的GPU数据"""
    try:
        data = request.get_json()
        server_name = data.get('server_name', 'unknown')
        
        gpu_data[server_name] = {
            'timestamp': data.get('timestamp'),
            'gpus': data.get('gpus', []),
            'last_update': time.time()
        }
        
        return jsonify({'status': 'success', 'message': 'Data updated'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/data')
def get_data():
    """API接口 - 返回JSON格式的数据"""
    current_timestamp = time.time()
    servers = {}
    
    for server_name, data in gpu_data.items():
        is_online = (current_timestamp - data.get('last_update', 0)) < DATA_TIMEOUT
        servers[server_name] = {
            'online': is_online,
            'timestamp': data.get('timestamp', 'N/A'),
            'gpus': data.get('gpus', [])
        }
    
    return jsonify(servers)

def main():
    parser = argparse.ArgumentParser(description='GPU监控服务端')
    parser.add_argument('--port', type=int, default=5000, help='服务端口 (默认: 5000)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    args = parser.parse_args()
    
    # 启动清理线程
    cleaner = threading.Thread(target=clean_old_data, daemon=True)
    cleaner.start()
    
    print(f"===========================================")
    print(f"GPU监控服务端启动成功!")
    print(f"访问地址: http://localhost:{args.port}")
    print(f"如果使用端口转发，请将客户端配置为您的公网地址")
    print(f"===========================================")
    
    app.run(host=args.host, port=args.port, debug=False)

if __name__ == '__main__':
    main()

