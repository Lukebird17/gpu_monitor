#!/usr/bin/env python3
"""
GPU监控服务端 - Geek版 - 超酷的赛博朋克风格 + 实时图表
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

# Geek风格HTML模板
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
            font-family: 'Share Tech Mono', monospace;
            background: var(--dark-bg);
            color: var(--cyber-blue);
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }
        
        /* 赛博朋克背景动画 */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                repeating-linear-gradient(
                    0deg,
                    transparent,
                    transparent 2px,
                    rgba(0, 243, 255, 0.03) 2px,
                    rgba(0, 243, 255, 0.03) 4px
                );
            pointer-events: none;
            z-index: 1;
        }
        
        /* 扫描线效果 */
        body::after {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, 
                transparent, 
                var(--cyber-blue), 
                transparent);
            animation: scan 3s linear infinite;
            z-index: 2;
            opacity: 0.5;
        }
        
        @keyframes scan {
            0% { top: 0%; }
            100% { top: 100%; }
        }
        
        .container {
            max-width: 1800px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 10;
        }
        
        /* 顶部标题栏 */
        .header {
            background: var(--card-bg);
            border: 2px solid var(--cyber-blue);
            border-radius: 0;
            padding: 20px 30px;
            margin-bottom: 20px;
            box-shadow: 
                0 0 20px rgba(0, 243, 255, 0.3),
                inset 0 0 20px rgba(0, 243, 255, 0.05);
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(0, 243, 255, 0.1),
                transparent
            );
            animation: shimmer 3s infinite;
        }
        
        @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
            z-index: 1;
        }
        
        .title-section {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .logo {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.5em;
            font-weight: 900;
            background: linear-gradient(135deg, var(--cyber-blue), var(--cyber-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px rgba(0, 243, 255, 0.5);
            letter-spacing: 2px;
        }
        
        .system-status {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 15px;
            background: rgba(0, 243, 255, 0.1);
            border: 1px solid var(--cyber-blue);
            font-size: 0.9em;
            text-transform: uppercase;
        }
        
        .status-item .indicator {
            width: 8px;
            height: 8px;
            background: var(--cyber-green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; box-shadow: 0 0 10px var(--cyber-green); }
            50% { opacity: 0.5; box-shadow: 0 0 5px var(--cyber-green); }
        }
        
        /* 统计面板 */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--cyber-blue);
            padding: 20px;
            position: relative;
            clip-path: polygon(0 0, calc(100% - 15px) 0, 100% 15px, 100% 100%, 0 100%);
            transition: all 0.3s;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 15px;
            height: 15px;
            background: var(--cyber-blue);
            clip-path: polygon(0 0, 100% 0, 100% 100%);
        }
        
        .stat-card:hover {
            border-color: var(--cyber-pink);
            box-shadow: 0 0 20px rgba(255, 0, 110, 0.5);
            transform: translateY(-3px);
        }
        
        .stat-label {
            font-size: 0.75em;
            color: var(--cyber-blue);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.5em;
            font-weight: 700;
            color: var(--cyber-green);
            text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
        }
        
        /* 图表区域 */
        .chart-section {
            background: var(--card-bg);
            border: 2px solid var(--cyber-pink);
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 0 30px rgba(255, 0, 110, 0.2);
        }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(0, 243, 255, 0.3);
        }
        
        .chart-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.3em;
            color: var(--cyber-pink);
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        .server-selector {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .server-selector label {
            font-size: 0.9em;
            color: var(--cyber-blue);
            text-transform: uppercase;
        }
        
        .server-selector select {
            background: var(--darker-bg);
            color: var(--cyber-green);
            border: 1px solid var(--cyber-blue);
            padding: 8px 15px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.9em;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .server-selector select:hover {
            border-color: var(--cyber-pink);
            box-shadow: 0 0 10px rgba(255, 0, 110, 0.3);
        }
        
        .server-selector select:focus {
            outline: none;
            border-color: var(--cyber-purple);
            box-shadow: 0 0 15px rgba(139, 0, 255, 0.5);
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin-bottom: 20px;
        }
        
        /* 服务器详情卡片 */
        .server-details {
            background: var(--card-bg);
            border: 2px solid var(--cyber-purple);
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 0 30px rgba(139, 0, 255, 0.2);
        }
        
        .server-details-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(0, 243, 255, 0.3);
        }
        
        .server-name {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.8em;
            color: var(--cyber-green);
            text-transform: uppercase;
            letter-spacing: 3px;
            text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
        }
        
        .server-badge {
            padding: 8px 20px;
            background: rgba(0, 255, 136, 0.2);
            border: 1px solid var(--cyber-green);
            color: var(--cyber-green);
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 2px;
        }
        
        /* GPU网格 */
        .gpu-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
            gap: 20px;
        }
        
        .gpu-card {
            background: rgba(10, 14, 39, 0.5);
            border: 1px solid var(--cyber-blue);
            padding: 20px;
            position: relative;
            transition: all 0.3s;
        }
        
        .gpu-card::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, 
                var(--cyber-blue), 
                var(--cyber-pink), 
                var(--cyber-purple));
        }
        
        .gpu-card:hover {
            border-color: var(--cyber-pink);
            box-shadow: 0 0 20px rgba(255, 0, 110, 0.3);
            transform: translateY(-3px);
        }
        
        .gpu-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .gpu-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.2em;
            color: var(--cyber-yellow);
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        .gpu-status {
            padding: 5px 12px;
            border: 1px solid;
            font-size: 0.8em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .gpu-status.idle { 
            border-color: var(--cyber-green); 
            color: var(--cyber-green);
            background: rgba(0, 255, 136, 0.1);
        }
        .gpu-status.busy { 
            border-color: var(--cyber-yellow); 
            color: var(--cyber-yellow);
            background: rgba(255, 207, 0, 0.1);
        }
        .gpu-status.full { 
            border-color: var(--cyber-pink); 
            color: var(--cyber-pink);
            background: rgba(255, 0, 110, 0.1);
        }
        
        .gpu-model {
            color: rgba(0, 243, 255, 0.7);
            font-size: 0.85em;
            margin-bottom: 15px;
            text-transform: uppercase;
        }
        
        /* 指标显示 */
        .metric-row {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .metric {
            background: rgba(0, 0, 0, 0.3);
            padding: 12px;
            border-left: 3px solid var(--cyber-blue);
        }
        
        .metric-label {
            font-size: 0.75em;
            color: rgba(0, 243, 255, 0.7);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        
        .metric-value {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.5em;
            color: var(--cyber-green);
        }
        
        /* 进度条 */
        .progress-container {
            margin-top: 15px;
        }
        
        .progress-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 0.85em;
        }
        
        .progress-bar {
            height: 8px;
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(0, 243, 255, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            position: relative;
            transition: width 0.5s ease;
        }
        
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(
                90deg,
                transparent 0%,
                rgba(255, 255, 255, 0.3) 50%,
                transparent 100%
            );
            animation: progressShine 2s infinite;
        }
        
        @keyframes progressShine {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .progress-low { 
            background: linear-gradient(90deg, #00ff88, #00cc6a); 
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }
        .progress-medium { 
            background: linear-gradient(90deg, #ffcf00, #ff9500); 
            box-shadow: 0 0 10px rgba(255, 207, 0, 0.5);
        }
        .progress-high { 
            background: linear-gradient(90deg, #ff006e, #ff4d00); 
            box-shadow: 0 0 10px rgba(255, 0, 110, 0.5);
        }
        
        /* 进程列表 */
        .process-section {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(0, 243, 255, 0.2);
        }
        
        .process-header {
            font-family: 'Orbitron', sans-serif;
            color: var(--cyber-pink);
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }
        
        .process-list {
            max-height: 200px;
            overflow-y: auto;
        }
        
        .process-list::-webkit-scrollbar {
            width: 8px;
        }
        
        .process-list::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.3);
        }
        
        .process-list::-webkit-scrollbar-thumb {
            background: var(--cyber-blue);
            border: 1px solid var(--cyber-pink);
        }
        
        .process-item {
            background: rgba(0, 0, 0, 0.3);
            border-left: 2px solid var(--cyber-purple);
            padding: 10px;
            margin: 5px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85em;
            transition: all 0.3s;
        }
        
        .process-item:hover {
            border-left-color: var(--cyber-pink);
            background: rgba(255, 0, 110, 0.1);
            transform: translateX(5px);
        }
        
        .process-name {
            color: var(--cyber-green);
            font-weight: 700;
        }
        
        .process-pid {
            color: rgba(0, 243, 255, 0.6);
            font-size: 0.9em;
        }
        
        .process-memory {
            color: var(--cyber-yellow);
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
        }
        
        /* 空数据状态 */
        .no-data {
            text-align: center;
            padding: 60px;
            background: var(--card-bg);
            border: 2px dashed rgba(0, 243, 255, 0.3);
        }
        
        .no-data i {
            font-size: 4em;
            color: rgba(0, 243, 255, 0.3);
            margin-bottom: 20px;
        }
        
        .no-data h3 {
            font-family: 'Orbitron', sans-serif;
            color: var(--cyber-pink);
            font-size: 1.5em;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        
        /* 响应式 */
        @media (max-width: 1200px) {
            .gpu-grid {
                grid-template-columns: 1fr;
            }
        }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .header-content {
                flex-direction: column;
                gap: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <div class="header-content">
                <div class="title-section">
                    <div class="logo">GPU_MONITOR</div>
                </div>
                <div class="system-status">
                    <div class="status-item">
                        <span class="indicator"></span>
                        <span>SYSTEM ONLINE</span>
                    </div>
                    <div class="status-item">
                        <i class="far fa-clock"></i>
                        <span>{{ current_time }}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 统计面板 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">&gt; SERVERS</div>
                <div class="stat-value">{{ total_servers }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">&gt; TOTAL_GPUs</div>
                <div class="stat-value">{{ total_gpus }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">&gt; ONLINE</div>
                <div class="stat-value">{{ online_servers }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">&gt; UPTIME</div>
                <div class="stat-value">{{ uptime }}</div>
            </div>
        </div>
        
        <!-- 总显存占用图表 -->
        <div class="chart-section">
            <div class="chart-header">
                <div class="chart-title">&gt;&gt; TOTAL MEMORY USAGE TIMELINE</div>
            </div>
            <div class="chart-container">
                <canvas id="totalMemoryChart"></canvas>
            </div>
        </div>
        
        <!-- 单服务器GPU显存图表 -->
        <div class="chart-section">
            <div class="chart-header">
                <div class="chart-title">&gt;&gt; SERVER GPU MEMORY TIMELINE</div>
                <div class="server-selector">
                    <label for="serverSelect">SELECT_SERVER:</label>
                    <select id="serverSelect" onchange="updateServerChart()">
                        <option value="">-- SELECT --</option>
                        {% for server_name in servers.keys() %}
                        <option value="{{ server_name }}">{{ server_name }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="serverMemoryChart"></canvas>
            </div>
        </div>
        
        <!-- GPU详细信息 -->
        <div id="gpuDetails">
            {% if servers %}
                {% for server_name, server_data in servers.items() %}
                {% if server_data.online %}
                <div class="server-details" data-server="{{ server_name }}">
                    <div class="server-details-header">
                        <div class="server-name">// {{ server_name }}</div>
                        <div class="server-badge">{{ server_data.gpus|length }} GPU_UNITS</div>
                    </div>
                    
                    <div class="gpu-grid">
                        {% for gpu in server_data.gpus %}
                        <div class="gpu-card">
                            <div class="gpu-header">
                                <div class="gpu-title">GPU_{{ gpu.index }}</div>
                                {% set util = gpu.utilization|int %}
                                <div class="gpu-status {{ 'idle' if util < 20 else ('busy' if util < 80 else 'full') }}">
                                    {{ 'IDLE' if util < 20 else ('ACTIVE' if util < 80 else 'FULL') }}
                                </div>
                            </div>
                            
                            <div class="gpu-model">{{ gpu.name }}</div>
                            
                            <div class="metric-row">
                                <div class="metric">
                                    <div class="metric-label">&gt; TEMP</div>
                                    <div class="metric-value">{{ gpu.temperature }}°C</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-label">&gt; POWER</div>
                                    <div class="metric-value">{{ gpu.power_draw }}</div>
                                </div>
                            </div>
                            
                            <div class="progress-container">
                                <div class="progress-header">
                                    <span>&gt; GPU_UTIL</span>
                                    <span>{{ gpu.utilization }}%</span>
                                </div>
                                <div class="progress-bar">
                                    {% set util_val = gpu.utilization|int %}
                                    <div class="progress-fill {{ 'progress-low' if util_val < 50 else ('progress-medium' if util_val < 80 else 'progress-high') }}" 
                                         style="width: {{ gpu.utilization }}%"></div>
                                </div>
                            </div>
                            
                            <div class="progress-container">
                                <div class="progress-header">
                                    <span>&gt; VRAM</span>
                                    <span>{{ gpu.memory_used }} / {{ gpu.memory_total }}</span>
                                </div>
                                <div class="progress-bar">
                                    {% set mem_val = gpu.memory_percent|int %}
                                    <div class="progress-fill {{ 'progress-low' if mem_val < 50 else ('progress-medium' if mem_val < 80 else 'progress-high') }}" 
                                         style="width: {{ gpu.memory_percent }}%"></div>
                                </div>
                            </div>
                            
                            {% if gpu.processes %}
                            <div class="process-section">
                                <div class="process-header">&gt; ACTIVE_PROCESSES [{{ gpu.processes|length }}]</div>
                                <div class="process-list">
                                    {% for proc in gpu.processes %}
                                    <div class="process-item">
                                        <div>
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
                    <i class="fas fa-database"></i>
                    <h3>NO_DATA_DETECTED</h3>
                    <p>Waiting for client connection...</p>
                </div>
            {% endif %}
        </div>
    </div>
    
    <script>
        // 历史数据
        const historyData = {{ history_json|safe }};
        
        // Chart.js 默认配置
        Chart.defaults.color = '#00f3ff';
        Chart.defaults.borderColor = 'rgba(0, 243, 255, 0.1)';
        Chart.defaults.font.family = 'Share Tech Mono';
        
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
                            color: '#00f3ff',
                            font: {
                                family: 'Orbitron',
                                size: 11
                            },
                            boxWidth: 15,
                            boxHeight: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(10, 14, 39, 0.9)',
                        titleColor: '#00f3ff',
                        bodyColor: '#00ff88',
                        borderColor: '#ff006e',
                        borderWidth: 1,
                        titleFont: {
                            family: 'Orbitron'
                        },
                        bodyFont: {
                            family: 'Share Tech Mono'
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(0, 243, 255, 0.1)'
                        },
                        ticks: {
                            color: '#00f3ff',
                            font: {
                                size: 10
                            }
                        }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        grid: {
                            color: 'rgba(0, 243, 255, 0.1)'
                        },
                        ticks: {
                            color: '#00f3ff',
                            font: {
                                size: 10
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
                            color: '#00f3ff',
                            font: {
                                family: 'Orbitron',
                                size: 11
                            },
                            boxWidth: 15,
                            boxHeight: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(10, 14, 39, 0.9)',
                        titleColor: '#00f3ff',
                        bodyColor: '#00ff88',
                        borderColor: '#8b00ff',
                        borderWidth: 1,
                        titleFont: {
                            family: 'Orbitron'
                        },
                        bodyFont: {
                            family: 'Share Tech Mono'
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(0, 243, 255, 0.1)'
                        },
                        ticks: {
                            color: '#00f3ff',
                            font: {
                                size: 10
                            }
                        }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        grid: {
                            color: 'rgba(0, 243, 255, 0.1)'
                        },
                        ticks: {
                            color: '#00f3ff',
                            font: {
                                size: 10
                            },
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
        
        // 彩虹色调色板
        const colors = [
            '#00f3ff', // cyan
            '#ff006e', // pink
            '#8b00ff', // purple
            '#00ff88', // green
            '#ffcf00', // yellow
            '#ff4d00', // orange
            '#00ccff', // light blue
            '#ff00ff'  // magenta
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
                        tension: 0.4,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 5
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
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 5
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
    parser = argparse.ArgumentParser(description='GPU监控服务端 - Geek版')
    parser.add_argument('--port', type=int, default=5000, help='服务端口 (默认: 5000)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    args = parser.parse_args()
    
    # 启动清理线程
    cleaner = threading.Thread(target=clean_old_data, daemon=True)
    cleaner.start()
    
    print(f"═══════════════════════════════════════════")
    print(f"   GPU MONITOR // GEEK EDITION")
    print(f"═══════════════════════════════════════════")
    print(f"  STATUS: ONLINE")
    print(f"  ADDRESS: http://localhost:{args.port}")
    print(f"═══════════════════════════════════════════")
    
    app.run(host=args.host, port=args.port, debug=False)

if __name__ == '__main__':
    main()

