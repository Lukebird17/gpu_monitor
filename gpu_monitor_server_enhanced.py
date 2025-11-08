#!/usr/bin/env python3
"""
GPU监控服务端 - 增强版 - Geek风格 + 图表监控
运行方式: python gpu_monitor_server_enhanced.py --port 5000
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

# 存储历史数据用于图表显示（最近100个数据点）
from collections import deque, defaultdict
history_data = defaultdict(lambda: {
    'timestamps': deque(maxlen=100),
    'total_memory_used': deque(maxlen=100),
    'total_memory_total': deque(maxlen=100),
    'gpu_memory': defaultdict(lambda: deque(maxlen=100))
})

# 历史数据存储（用于图表）
# 格式: {server_name: deque([{timestamp, memory_percent, gpu_data}, ...])}
history_data = defaultdict(lambda: deque(maxlen=100))  # 保留最近100个数据点
server_start_time = time.time()

# 全局统计历史数据（所有服务器的总显存占用）
global_history = deque(maxlen=100)

# 增强版HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPU监控系统 - 实时监控面板</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --dark-bg: #1a1a2e;
            --card-bg: #ffffff;
            --text-primary: #333333;
            --text-secondary: #666666;
            --border-color: #e5e7eb;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        
        /* 顶部标题栏 */
        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px 30px;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
            animation: slideDown 0.5s ease;
        }

        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .header-left {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .header-title {
            font-size: 2em;
            color: var(--text-primary);
            font-weight: 700;
        }
        
        .header-title i {
            color: var(--primary-color);
            margin-right: 10px;
        }
        
        .header-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .last-update {
            color: var(--text-secondary);
            font-size: 0.95em;
        }
        
        .last-update i {
            color: var(--primary-color);
            margin-right: 5px;
        }
        
        .auto-refresh {
            background: var(--success-color);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .auto-refresh i {
            animation: spin 2s linear infinite;
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        /* 统计面板 */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            gap: 15px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .stat-icon {
            width: 60px;
            height: 60px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8em;
        }
        
        .stat-icon.servers {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .stat-icon.gpus {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        
        .stat-icon.online {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }
        
        .stat-icon.offline {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            color: white;
        }
        
        .stat-content {
            flex: 1;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        
        .stat-value {
            color: var(--text-primary);
            font-size: 1.8em;
            font-weight: 700;
        }
        
        /* 搜索和筛选 */
        .controls {
            background: white;
            border-radius: 12px;
            padding: 15px 20px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            display: flex;
            gap: 15px;
            align-items: center;
        }
        
        .search-box {
            flex: 1;
            position: relative;
        }
        
        .search-box input {
            width: 100%;
            padding: 10px 15px 10px 40px;
            border: 2px solid var(--border-color);
            border-radius: 8px;
            font-size: 0.95em;
            transition: border-color 0.3s;
        }
        
        .search-box input:focus {
            outline: none;
            border-color: var(--primary-color);
        }
        
        .search-box i {
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
        }
        
        .filter-buttons {
            display: flex;
            gap: 10px;
        }
        
        .filter-btn {
            padding: 10px 20px;
            border: 2px solid var(--border-color);
            background: white;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s;
            font-weight: 600;
        }
        
        .filter-btn:hover {
            border-color: var(--primary-color);
            color: var(--primary-color);
        }
        
        .filter-btn.active {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }
        
        /* 服务器卡片 */
        .server-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            animation: fadeIn 0.5s ease;
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .server-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid var(--primary-color);
        }
        
        .server-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .server-name {
            font-size: 1.6em;
            color: var(--text-primary);
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .server-name i {
            color: var(--primary-color);
        }
        
        .server-badges {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .badge {
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85em;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .badge-online {
            background: var(--success-color);
            color: white;
        }
        
        .badge-offline {
            background: var(--danger-color);
            color: white;
        }
        
        .badge-gpu-count {
            background: #e0e7ff;
            color: var(--primary-color);
        }
        
        .server-meta {
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .meta-item {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-secondary);
            font-size: 0.9em;
        }
        
        .meta-item i {
            color: var(--primary-color);
        }
        
        .meta-item strong {
            color: var(--text-primary);
        }
        
        /* GPU卡片网格 */
        .gpu-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 20px;
        }
        
        .gpu-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            padding: 20px;
            border-left: 5px solid var(--primary-color);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .gpu-card:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .gpu-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .gpu-title {
            font-size: 1.15em;
            color: var(--text-primary);
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .gpu-title i {
            color: var(--primary-color);
        }
        
        .gpu-status {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 0.85em;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: 600;
        }
        
        .gpu-status.idle {
            background: #d1fae5;
            color: #065f46;
        }
        
        .gpu-status.busy {
            background: #fed7aa;
            color: #92400e;
        }
        
        .gpu-status.full {
            background: #fecaca;
            color: #991b1b;
        }
        
        .gpu-model {
            color: var(--text-secondary);
            font-size: 0.9em;
            margin-bottom: 15px;
        }
        
        /* 指标网格 */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 15px;
        }
        
        .metric {
            background: white;
            padding: 12px;
            border-radius: 8px;
        }
        
        .metric-label {
            display: flex;
            align-items: center;
            gap: 6px;
            color: var(--text-secondary);
            font-size: 0.85em;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        .metric-label i {
            font-size: 0.9em;
        }
        
        .metric-value {
            font-size: 1.3em;
            font-weight: 700;
            color: var(--text-primary);
        }
        
        .metric-bar {
            margin-top: 8px;
        }
        
        /* 进度条 */
        .progress-bar {
            background: #e5e7eb;
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            position: relative;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.5s ease;
            position: relative;
        }
        
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            right: 0;
            background: linear-gradient(
                90deg,
                rgba(255,255,255,0) 0%,
                rgba(255,255,255,0.3) 50%,
                rgba(255,255,255,0) 100%
            );
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
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
        
        .progress-label {
            display: flex;
            justify-content: space-between;
            margin-top: 4px;
            font-size: 0.8em;
            color: var(--text-secondary);
        }
        
        /* 进程列表 */
        .process-section {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 2px dashed var(--border-color);
        }
        
        .process-header {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-secondary);
            font-weight: 700;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        
        .process-header i {
            color: var(--primary-color);
        }
        
        .process-list {
            max-height: 200px;
            overflow-y: auto;
        }
        
        .process-item {
            background: white;
            padding: 10px 12px;
            margin: 6px 0;
            border-radius: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 3px solid var(--primary-color);
            font-size: 0.85em;
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
            color: var(--text-secondary);
            font-size: 0.9em;
        }
        
        .process-memory {
            color: var(--primary-color);
            font-weight: 700;
            white-space: nowrap;
        }
        
        /* 空状态 */
        .no-data {
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .no-data i {
            font-size: 4em;
            color: var(--text-secondary);
            margin-bottom: 20px;
        }
        
        .no-data h3 {
            color: var(--text-primary);
            margin-bottom: 10px;
            font-size: 1.5em;
        }
        
        .no-data p {
            color: var(--text-secondary);
        }
        
        /* 离线状态 */
        .offline-notice {
            text-align: center;
            padding: 40px 20px;
            color: var(--text-secondary);
            background: #f9fafb;
            border-radius: 10px;
        }
        
        .offline-notice i {
            font-size: 3em;
            color: var(--danger-color);
            margin-bottom: 15px;
        }
        
        /* 响应式设计 */
        @media (max-width: 1200px) {
            .gpu-grid {
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            }
        }
        
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 15px;
            }
            
            .header-left, .header-right {
                width: 100%;
                justify-content: space-between;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .controls {
                flex-direction: column;
            }
            
            .gpu-grid {
                grid-template-columns: 1fr;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* 滚动条样式 */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--primary-color);
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--secondary-color);
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <div class="header-left">
                <div class="header-title">
                    <i class="fas fa-server"></i>
                    GPU监控系统
                </div>
            </div>
            <div class="header-right">
                <div class="last-update">
                    <i class="far fa-clock"></i>
                    {{ current_time }}
                </div>
                <div class="auto-refresh">
                    <i class="fas fa-sync-alt"></i>
                    自动刷新
                </div>
            </div>
        </div>
        
        <!-- 统计面板 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon servers">
                    <i class="fas fa-server"></i>
                </div>
                <div class="stat-content">
                    <div class="stat-label">总服务器数</div>
                    <div class="stat-value">{{ total_servers }}</div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon gpus">
                    <i class="fas fa-microchip"></i>
                </div>
                <div class="stat-content">
                    <div class="stat-label">GPU总数</div>
                    <div class="stat-value">{{ total_gpus }}</div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon online">
                    <i class="fas fa-check-circle"></i>
                </div>
                <div class="stat-content">
                    <div class="stat-label">在线服务器</div>
                    <div class="stat-value">{{ online_servers }}</div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon offline">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div class="stat-content">
                    <div class="stat-label">离线服务器</div>
                    <div class="stat-value">{{ offline_servers }}</div>
                </div>
            </div>
        </div>
        
        <!-- 搜索和筛选 -->
        <div class="controls">
            <div class="search-box">
                <i class="fas fa-search"></i>
                <input type="text" id="searchInput" placeholder="搜索服务器名称...">
            </div>
            <div class="filter-buttons">
                <button class="filter-btn active" onclick="filterServers('all')">
                    <i class="fas fa-list"></i> 全部
                </button>
                <button class="filter-btn" onclick="filterServers('online')">
                    <i class="fas fa-check-circle"></i> 在线
                </button>
                <button class="filter-btn" onclick="filterServers('offline')">
                    <i class="fas fa-times-circle"></i> 离线
                </button>
            </div>
        </div>
        
        <!-- 服务器列表 -->
        {% if servers %}
            {% for server_name, server_data in servers.items() %}
            <div class="server-card" data-status="{{ 'online' if server_data.online else 'offline' }}" data-name="{{ server_name }}">
                <div class="server-header">
                    <div class="server-info">
                        <div class="server-name">
                            <i class="fas fa-desktop"></i>
                            {{ server_name }}
                        </div>
                    </div>
                    <div class="server-badges">
                        <div class="badge {{ 'badge-online' if server_data.online else 'badge-offline' }}">
                            <i class="fas fa-circle"></i>
                            {{ '在线' if server_data.online else '离线' }}
                        </div>
                        {% if server_data.online %}
                        <div class="badge badge-gpu-count">
                            <i class="fas fa-microchip"></i>
                            {{ server_data.gpus|length }} GPU
                        </div>
                        {% endif %}
                    </div>
                </div>
                
                {% if server_data.online %}
                    <div class="server-meta">
                        <div class="meta-item">
                            <i class="far fa-clock"></i>
                            最后更新: <strong>{{ server_data.timestamp }}</strong>
                        </div>
                    </div>
                    
                    <div class="gpu-grid">
                        {% for gpu in server_data.gpus %}
                        <div class="gpu-card">
                            <div class="gpu-header">
                                <div class="gpu-title">
                                    <i class="fas fa-microchip"></i>
                                    GPU {{ gpu.index }}
                                </div>
                                {% set util = gpu.utilization|int %}
                                <div class="gpu-status {{ 'idle' if util < 20 else ('busy' if util < 80 else 'full') }}">
                                    <i class="fas fa-circle"></i>
                                    {{ '空闲' if util < 20 else ('使用中' if util < 80 else '满载') }}
                                </div>
                            </div>
                            
                            <div class="gpu-model">{{ gpu.name }}</div>
                            
                            <div class="metrics-grid">
                                <!-- 温度 -->
                                <div class="metric">
                                    <div class="metric-label">
                                        <i class="fas fa-thermometer-half"></i>
                                        温度
                                    </div>
                                    <div class="metric-value">{{ gpu.temperature }}°C</div>
                                </div>
                                
                                <!-- 功耗 -->
                                <div class="metric">
                                    <div class="metric-label">
                                        <i class="fas fa-bolt"></i>
                                        功耗
                                    </div>
                                    <div class="metric-value">{{ gpu.power_draw }}</div>
                                </div>
                                
                                <!-- GPU使用率 -->
                                <div class="metric" style="grid-column: 1 / -1;">
                                    <div class="metric-label">
                                        <i class="fas fa-chart-line"></i>
                                        GPU使用率
                                    </div>
                                    <div class="metric-bar">
                                        <div class="progress-bar">
                                            {% set util_val = gpu.utilization|int %}
                                            <div class="progress-fill {{ 'progress-low' if util_val < 50 else ('progress-medium' if util_val < 80 else 'progress-high') }}" 
                                                 style="width: {{ gpu.utilization }}%">
                                            </div>
                                        </div>
                                        <div class="progress-label">
                                            <span>{{ gpu.utilization }}%</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- 显存使用 -->
                                <div class="metric" style="grid-column: 1 / -1;">
                                    <div class="metric-label">
                                        <i class="fas fa-memory"></i>
                                        显存使用
                                    </div>
                                    <div class="metric-bar">
                                        <div class="progress-bar">
                                            {% set mem_val = gpu.memory_percent|int %}
                                            <div class="progress-fill {{ 'progress-low' if mem_val < 50 else ('progress-medium' if mem_val < 80 else 'progress-high') }}" 
                                                 style="width: {{ gpu.memory_percent }}%">
                                            </div>
                                        </div>
                                        <div class="progress-label">
                                            <span>{{ gpu.memory_used }} / {{ gpu.memory_total }}</span>
                                            <span>{{ gpu.memory_percent }}%</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            {% if gpu.processes %}
                            <div class="process-section">
                                <div class="process-header">
                                    <i class="fas fa-tasks"></i>
                                    运行中的进程 ({{ gpu.processes|length }})
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
                {% else %}
                    <div class="offline-notice">
                        <i class="fas fa-exclamation-circle"></i>
                        <p>服务器超过60秒未更新数据</p>
                    </div>
                {% endif %}
            </div>
            {% endfor %}
        {% else %}
            <div class="no-data">
                <i class="fas fa-inbox"></i>
                <h3>暂无服务器数据</h3>
                <p>请确保客户端正在运行并连接到此服务端</p>
            </div>
        {% endif %}
    </div>
    
    <script>
        // 自动刷新
        setInterval(function() {
            location.reload();
        }, 5000);
        
        // 搜索功能
        document.getElementById('searchInput').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const serverCards = document.querySelectorAll('.server-card');
            
            serverCards.forEach(card => {
                const serverName = card.getAttribute('data-name').toLowerCase();
                if (serverName.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
        
        // 筛选功能
        function filterServers(filter) {
            const serverCards = document.querySelectorAll('.server-card');
            const filterBtns = document.querySelectorAll('.filter-btn');
            
            // 更新按钮状态
            filterBtns.forEach(btn => btn.classList.remove('active'));
            event.target.closest('.filter-btn').classList.add('active');
            
            // 筛选服务器
            serverCards.forEach(card => {
                const status = card.getAttribute('data-status');
                
                if (filter === 'all') {
                    card.style.display = 'block';
                } else if (filter === status) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
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
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
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
    
    return render_template_string(
        HTML_TEMPLATE,
        servers=servers,
        current_time=current_time,
        total_servers=len(servers),
        total_gpus=total_gpus,
        online_servers=online_count,
        offline_servers=offline_count
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
    parser = argparse.ArgumentParser(description='GPU监控服务端 - 增强版')
    parser.add_argument('--port', type=int, default=5000, help='服务端口 (默认: 5000)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    args = parser.parse_args()
    
    # 启动清理线程
    cleaner = threading.Thread(target=clean_old_data, daemon=True)
    cleaner.start()
    
    print(f"===========================================")
    print(f"GPU监控服务端启动成功! (增强版)")
    print(f"访问地址: http://localhost:{args.port}")
    print(f"如果使用端口转发，请将客户端配置为您的公网地址")
    print(f"===========================================")
    
    app.run(host=args.host, port=args.port, debug=False)

if __name__ == '__main__':
    main()

