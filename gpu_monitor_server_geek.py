#!/usr/bin/env python3
"""
GPU监控服务端 - 数据库控制台风格
运行方式: python gpu_monitor_server_geek.py --port 5000
"""

from flask import Flask, render_template_string, jsonify, request
from datetime import datetime
import argparse
import threading
import time
from collections import deque, defaultdict

app = Flask(__name__)

# 存储所有服务器的GPU信息
gpu_data = {}
# 数据过期时间（秒）
DATA_TIMEOUT = 60

# 存储历史数据用于图表显示
history_data = defaultdict(lambda: {
    'timestamps': deque(maxlen=100),
    'total_memory_percent': deque(maxlen=100),
    'gpu_memory': defaultdict(lambda: deque(maxlen=100))
})

server_start_time = time.time()

# 数据库控制台风格HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPU Monitor - Database Console</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&family=Inter:wght@400;600;700&display=swap');
        
        :root {
            --primary: #3b82f6;
            --secondary: #8b5cf6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #06b6d4;
            --dark-bg: #0f172a;
            --darker-bg: #020617;
            --card-bg: #1e293b;
            --card-border: #334155;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: var(--dark-bg);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* 顶部标题栏 */
        .header {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 20px 30px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .title-section h1 {
            font-size: 1.75em;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .title-section h1 i {
            color: var(--primary);
        }
        
        .header-info {
            display: flex;
            gap: 20px;
            align-items: center;
            font-family: 'Roboto Mono', monospace;
            font-size: 0.9em;
            color: var(--text-secondary);
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* 统计卡片 */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 20px;
            transition: all 0.2s;
        }
        
        .stat-card:hover {
            border-color: var(--primary);
            transform: translateY(-2px);
        }
        
        .stat-label {
            font-size: 0.85em;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        
        .stat-value {
            font-size: 2.25em;
            font-weight: 700;
            color: var(--text-primary);
            font-family: 'Roboto Mono', monospace;
        }
        
        /* 图表区域 */
        .chart-section {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
        }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--card-border);
        }
        
        .chart-title {
            font-size: 1.1em;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .chart-title i {
            color: var(--primary);
        }
        
        .server-selector {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        .server-selector label {
            font-size: 0.9em;
            color: var(--text-secondary);
        }
        
        .server-selector select {
            background: var(--darker-bg);
            color: var(--text-primary);
            border: 1px solid var(--card-border);
            border-radius: 6px;
            padding: 8px 16px;
            font-family: 'Roboto Mono', monospace;
            font-size: 0.9em;
            cursor: pointer;
            min-width: 200px;
        }
        
        .server-selector select:hover {
            border-color: var(--primary);
        }
        
        .server-selector select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        .chart-container {
            position: relative;
            height: 280px;
        }
        
        /* GPU详情 */
        .server-section {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
        }
        
        .server-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--card-border);
        }
        
        .server-name {
            font-size: 1.5em;
            font-weight: 700;
            color: var(--text-primary);
            font-family: 'Roboto Mono', monospace;
        }
        
        .server-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 16px;
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid var(--primary);
            border-radius: 20px;
            color: var(--primary);
            font-size: 0.9em;
            font-weight: 600;
        }
        
        /* GPU卡片网格 */
        .gpu-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
            gap: 20px;
        }
        
        .gpu-card {
            background: var(--darker-bg);
            border: 1px solid var(--card-border);
            border-radius: 6px;
            padding: 20px;
            transition: all 0.2s;
        }
        
        .gpu-card:hover {
            border-color: var(--primary);
        }
        
        .gpu-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .gpu-title {
            font-size: 1.1em;
            font-weight: 600;
            color: var(--text-primary);
            font-family: 'Roboto Mono', monospace;
        }
        
        .gpu-status {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .gpu-status.idle {
            background: rgba(16, 185, 129, 0.15);
            color: var(--success);
        }
        
        .gpu-status.busy {
            background: rgba(245, 158, 11, 0.15);
            color: var(--warning);
        }
        
        .gpu-status.full {
            background: rgba(239, 68, 68, 0.15);
            color: var(--danger);
        }
        
        .gpu-model {
            color: var(--text-secondary);
            font-size: 0.9em;
            margin-bottom: 15px;
        }
        
        /* 指标行 */
        .metrics-row {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 15px;
        }
        
        .metric {
            background: var(--card-bg);
            padding: 12px;
            border-radius: 6px;
            border-left: 3px solid var(--primary);
        }
        
        .metric-label {
            font-size: 0.8em;
            color: var(--text-muted);
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metric-value {
            font-size: 1.4em;
            font-weight: 700;
            color: var(--text-primary);
            font-family: 'Roboto Mono', monospace;
        }
        
        /* 进度条 */
        .progress-section {
            margin-bottom: 15px;
        }
        
        .progress-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
            font-size: 0.85em;
        }
        
        .progress-label {
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .progress-value {
            color: var(--text-primary);
            font-weight: 600;
            font-family: 'Roboto Mono', monospace;
        }
        
        .progress-bar {
            height: 8px;
            background: var(--card-bg);
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }
        
        .progress-fill {
            height: 100%;
            transition: width 0.5s ease;
            border-radius: 4px;
        }
        
        .progress-low { background: var(--success); }
        .progress-medium { background: var(--warning); }
        .progress-high { background: var(--danger); }
        
        /* 进程列表 */
        .process-section {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid var(--card-border);
        }
        
        .process-header {
            font-size: 0.9em;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .process-list {
            max-height: 200px;
            overflow-y: auto;
        }
        
        .process-list::-webkit-scrollbar {
            width: 6px;
        }
        
        .process-list::-webkit-scrollbar-track {
            background: var(--card-bg);
        }
        
        .process-list::-webkit-scrollbar-thumb {
            background: var(--card-border);
            border-radius: 3px;
        }
        
        .process-item {
            background: var(--card-bg);
            padding: 10px 12px;
            margin: 6px 0;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85em;
            border-left: 2px solid transparent;
            transition: all 0.2s;
        }
        
        .process-item:hover {
            border-left-color: var(--primary);
            background: rgba(59, 130, 246, 0.05);
        }
        
        .process-info {
            flex: 1;
        }
        
        .process-name {
            color: var(--text-primary);
            font-weight: 600;
            margin-bottom: 2px;
        }
        
        .process-pid {
            color: var(--text-muted);
            font-size: 0.9em;
            font-family: 'Roboto Mono', monospace;
        }
        
        .process-memory {
            color: var(--primary);
            font-weight: 700;
            font-family: 'Roboto Mono', monospace;
        }
        
        /* 空数据 */
        .no-data {
            text-align: center;
            padding: 60px 20px;
            background: var(--card-bg);
            border: 1px dashed var(--card-border);
            border-radius: 8px;
        }
        
        .no-data i {
            font-size: 3em;
            color: var(--text-muted);
            margin-bottom: 15px;
        }
        
        .no-data h3 {
            color: var(--text-primary);
            font-size: 1.3em;
            margin-bottom: 8px;
        }
        
        .no-data p {
            color: var(--text-secondary);
        }
        
        /* 响应式 */
        @media (max-width: 1200px) {
            .gpu-grid {
                grid-template-columns: 1fr;
            }
        }
        
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 15px;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .metrics-row {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <div class="title-section">
                <h1>
                    <i class="fas fa-database"></i>
                    GPU Monitor Console
                </h1>
            </div>
            <div class="header-info">
                <div class="status-indicator">
                    <span class="status-dot"></span>
                    <span>ONLINE</span>
                </div>
                <div>
                    <i class="far fa-clock"></i>
                    {{ current_time }}
                </div>
                <div>
                    UPTIME: {{ uptime }}
                </div>
            </div>
        </div>
        
        <!-- 统计卡片 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Servers</div>
                <div class="stat-value">{{ total_servers }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total GPUs</div>
                <div class="stat-value">{{ total_gpus }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Online</div>
                <div class="stat-value" style="color: var(--success)">{{ online_servers }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Offline</div>
                <div class="stat-value" style="color: var(--danger)">{{ offline_servers }}</div>
            </div>
        </div>
        
        <!-- 总显存占用图表 -->
        <div class="chart-section">
            <div class="chart-header">
                <div class="chart-title">
                    <i class="fas fa-chart-line"></i>
                    Total Memory Usage Over Time
                </div>
            </div>
            <div class="chart-container">
                <canvas id="totalMemoryChart"></canvas>
            </div>
        </div>
        
        <!-- 单服务器GPU显存图表 -->
        <div class="chart-section">
            <div class="chart-header">
                <div class="chart-title">
                    <i class="fas fa-chart-area"></i>
                    Server GPU Memory Timeline
                </div>
                <div class="server-selector">
                    <label for="serverSelect">Server:</label>
                    <select id="serverSelect" onchange="updateServerChart()">
                        {% if servers %}
                            {% for server_name in servers.keys() %}
                            <option value="{{ server_name }}" {% if loop.first %}selected{% endif %}>{{ server_name }}</option>
                            {% endfor %}
                        {% else %}
                            <option value="">No servers available</option>
                        {% endif %}
                    </select>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="serverMemoryChart"></canvas>
            </div>
        </div>
        
        <!-- GPU详细信息 -->
        {% if servers %}
            {% for server_name, server_data in servers.items() %}
            {% if server_data.online %}
            <div class="server-section">
                <div class="server-header">
                    <div class="server-name">{{ server_name }}</div>
                    <div class="server-badge">
                        <i class="fas fa-microchip"></i>
                        {{ server_data.gpus|length }} GPUs
                    </div>
                </div>
                
                <div class="gpu-grid">
                    {% for gpu in server_data.gpus %}
                    <div class="gpu-card">
                        <div class="gpu-header">
                            <div class="gpu-title">GPU {{ gpu.index }}</div>
                            {% set util = gpu.utilization|int %}
                            <div class="gpu-status {{ 'idle' if util < 20 else ('busy' if util < 80 else 'full') }}">
                                {{ 'Idle' if util < 20 else ('Active' if util < 80 else 'Full') }}
                            </div>
                        </div>
                        
                        <div class="gpu-model">{{ gpu.name }}</div>
                        
                        <div class="metrics-row">
                            <div class="metric">
                                <div class="metric-label">Temperature</div>
                                <div class="metric-value">{{ gpu.temperature }}°C</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">Power</div>
                                <div class="metric-value">{{ gpu.power_draw }}</div>
                            </div>
                        </div>
                        
                        <div class="progress-section">
                            <div class="progress-header">
                                <span class="progress-label">GPU Utilization</span>
                                <span class="progress-value">{{ gpu.utilization }}%</span>
                            </div>
                            <div class="progress-bar">
                                {% set util_val = gpu.utilization|int %}
                                <div class="progress-fill {{ 'progress-low' if util_val < 50 else ('progress-medium' if util_val < 80 else 'progress-high') }}" 
                                     style="width: {{ gpu.utilization }}%"></div>
                            </div>
                        </div>
                        
                        <div class="progress-section">
                            <div class="progress-header">
                                <span class="progress-label">Memory Usage</span>
                                <span class="progress-value">{{ gpu.memory_used }} / {{ gpu.memory_total }}</span>
                            </div>
                            <div class="progress-bar">
                                {% set mem_val = gpu.memory_percent|int %}
                                <div class="progress-fill {{ 'progress-low' if mem_val < 50 else ('progress-medium' if mem_val < 80 else 'progress-high') }}" 
                                     style="width: {{ gpu.memory_percent }}%"></div>
                            </div>
                        </div>
                        
                        {% if gpu.processes %}
                        <div class="process-section">
                            <div class="process-header">
                                <i class="fas fa-tasks"></i>
                                Running Processes ({{ gpu.processes|length }})
                            </div>
                            <div class="process-list">
                                {% for proc in gpu.processes %}
                                <div class="process-item">
                                    <div class="process-info">
                                        <div class="process-name">{{ proc.name }}</div>
                                        <div class="process-pid">PID: {{ proc.pid }}</div>
                                    </div>
                                    <div class="process-memory">{{ proc.memory }}</div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            {% endfor %}
        {% else %}
            <div class="no-data">
                <i class="fas fa-server"></i>
                <h3>No Server Data</h3>
                <p>Waiting for client connections...</p>
            </div>
        {% endif %}
    </div>
    
    <script>
        // 历史数据
        const historyData = {{ history_json|safe }};
        
        // Chart.js 配置
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.borderColor = '#334155';
        Chart.defaults.font.family = 'Roboto Mono';
        
        // 总显存占用图表
        const totalMemoryCtx = document.getElementById('totalMemoryChart').getContext('2d');
        const totalMemoryChart = new Chart(totalMemoryCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#e2e8f0',
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 15,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#e2e8f0',
                        bodyColor: '#94a3b8',
                        borderColor: '#334155',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: '#334155',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        grid: {
                            color: '#334155',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                size: 11
                            },
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
        
        // 服务器GPU显存图表
        const serverMemoryCtx = document.getElementById('serverMemoryChart').getContext('2d');
        const serverMemoryChart = new Chart(serverMemoryCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#e2e8f0',
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 15,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#e2e8f0',
                        bodyColor: '#94a3b8',
                        borderColor: '#334155',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: '#334155',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        grid: {
                            color: '#334155',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                size: 11
                            },
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
        
        // 颜色调色板
        const colors = [
            '#3b82f6', // blue
            '#8b5cf6', // purple
            '#10b981', // green
            '#f59e0b', // yellow
            '#ef4444', // red
            '#06b6d4', // cyan
            '#ec4899', // pink
            '#f97316'  // orange
        ];
        
        // 初始化图表
        function initCharts() {
            // 总显存图表
            const totalDatasets = [];
            let colorIndex = 0;
            
            for (const [serverName, data] of Object.entries(historyData)) {
                if (data.timestamps.length > 0) {
                    totalDatasets.push({
                        label: serverName,
                        data: data.total_memory_percent,
                        borderColor: colors[colorIndex % colors.length],
                        backgroundColor: colors[colorIndex % colors.length] + '20',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 4
                    });
                    colorIndex++;
                }
            }
            
            if (totalDatasets.length > 0) {
                const firstServer = Object.values(historyData).find(d => d.timestamps.length > 0);
                totalMemoryChart.data.labels = firstServer.timestamps;
                totalMemoryChart.data.datasets = totalDatasets;
                totalMemoryChart.update();
            }
            
            // 自动加载第一个服务器的数据
            const firstServerName = document.getElementById('serverSelect').value;
            if (firstServerName) {
                updateServerChart();
            }
        }
        
        // 更新服务器图表
        function updateServerChart() {
            const serverName = document.getElementById('serverSelect').value;
            if (!serverName || !historyData[serverName]) {
                serverMemoryChart.data.labels = [];
                serverMemoryChart.data.datasets = [];
                serverMemoryChart.update();
                return;
            }
            
            const data = historyData[serverName];
            const datasets = [];
            let colorIndex = 0;
            
            for (const [gpuId, gpuData] of Object.entries(data.gpu_memory)) {
                datasets.push({
                    label: `GPU ${gpuId}`,
                    data: gpuData,
                    borderColor: colors[colorIndex % colors.length],
                    backgroundColor: colors[colorIndex % colors.length] + '20',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                });
                colorIndex++;
            }
            
            serverMemoryChart.data.labels = data.timestamps;
            serverMemoryChart.data.datasets = datasets;
            serverMemoryChart.update();
        }
        
        // 初始化
        initCharts();
        
        // 自动刷新
        setInterval(function() {
            location.reload();
        }, 5000);
    </script>
</body>
</html>
"""

def clean_old_data():
    """定期清理过期的服务器数据"""
    while True:
        time.sleep(10)

@app.route('/')
def index():
    """主页面 - 显示所有服务器的GPU信息"""
    current_time = datetime.now().strftime('%H:%M:%S')
    
    # 计算运行时间
    uptime_seconds = int(time.time() - server_start_time)
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    uptime = f"{uptime_hours:02d}:{uptime_minutes:02d}"
    
    # 准备数据
    servers = {}
    current_timestamp = time.time()
    total_gpus = 0
    online_count = 0
    offline_count = 0
    
    for server_name, data in gpu_data.items():
        is_online = (current_timestamp - data.get('last_update', 0)) < DATA_TIMEOUT
        
        if is_online:
            online_count += 1
            total_gpus += len(data.get('gpus', []))
        else:
            offline_count += 1
        
        servers[server_name] = {
            'online': is_online,
            'timestamp': data.get('timestamp', 'N/A'),
            'gpus': data.get('gpus', [])
        }
    
    # 准备历史数据用于图表
    import json
    history_json = {}
    for server_name, hist in history_data.items():
        history_json[server_name] = {
            'timestamps': list(hist['timestamps']),
            'total_memory_percent': list(hist['total_memory_percent']),
            'gpu_memory': {k: list(v) for k, v in hist['gpu_memory'].items()}
        }
    
    return render_template_string(
        HTML_TEMPLATE,
        servers=servers,
        current_time=current_time,
        total_servers=len(servers),
        total_gpus=total_gpus,
        online_servers=online_count,
        offline_servers=offline_count,
        uptime=uptime,
        history_json=json.dumps(history_json)
    )

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
        
        # 更新历史数据
        gpus = data.get('gpus', [])
        if gpus:
            # 计算总显存使用百分比
            total_used = sum(float(gpu.get('memory_used', '0').split()[0]) for gpu in gpus)
            total_capacity = sum(float(gpu.get('memory_total', '0').split()[0]) for gpu in gpus)
            total_percent = (total_used / total_capacity * 100) if total_capacity > 0 else 0
            
            # 添加到历史记录
            hist = history_data[server_name]
            current_time_str = datetime.now().strftime('%H:%M:%S')
            hist['timestamps'].append(current_time_str)
            hist['total_memory_percent'].append(round(total_percent, 1))
            
            # 记录每个GPU的显存使用
            for gpu in gpus:
                gpu_id = str(gpu.get('index', 0))
                mem_percent = float(gpu.get('memory_percent', 0))
                hist['gpu_memory'][gpu_id].append(round(mem_percent, 1))
        
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

@app.route('/api/history')
def get_history():
    """返回历史数据"""
    history_json = {}
    for server_name, hist in history_data.items():
        history_json[server_name] = {
            'timestamps': list(hist['timestamps']),
            'total_memory_percent': list(hist['total_memory_percent']),
            'gpu_memory': {k: list(v) for k, v in hist['gpu_memory'].items()}
        }
    return jsonify(history_json)

def main():
    parser = argparse.ArgumentParser(description='GPU监控服务端 - 数据库控制台风格')
    parser.add_argument('--port', type=int, default=5000, help='服务端口 (默认: 5000)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    args = parser.parse_args()
    
    # 启动清理线程
    cleaner = threading.Thread(target=clean_old_data, daemon=True)
    cleaner.start()
    
    print(f"╔════════════════════════════════════════╗")
    print(f"║   GPU Monitor - Database Console      ║")
    print(f"╠════════════════════════════════════════╣")
    print(f"║  Status: ONLINE                        ║")
    print(f"║  Port: {args.port:<32} ║")
    print(f"║  URL: http://localhost:{args.port:<18} ║")
    print(f"╚════════════════════════════════════════╝")
    
    app.run(host=args.host, port=args.port, debug=False)

if __name__ == '__main__':
    main()
