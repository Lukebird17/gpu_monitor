#!/bin/bash
# GPU监控系统快速启动脚本

echo "============================================"
echo "       GPU监控系统 - 快速启动脚本"
echo "============================================"
echo ""

# 检测Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3，请先安装Python 3"
    exit 1
fi

echo "请选择启动模式:"
echo "1) 启动服务端（Web监控界面）"
echo "2) 启动客户端（GPU数据收集）"
echo "3) 测试nvidia-smi"
echo "4) 退出"
echo ""
read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "启动服务端..."
        echo "============================================"
        
        # 检查Flask
        if ! python3 -c "import flask" 2>/dev/null; then
            echo "⚠️  警告: 未安装Flask"
            read -p "是否现在安装? (y/n): " install_flask
            if [ "$install_flask" = "y" ]; then
                pip3 install --user flask || python3 -m pip install --user flask
            else
                echo "❌ 取消启动"
                exit 1
            fi
        fi
        
        read -p "请输入端口号 (默认5000): " port
        port=${port:-5000}
        
        echo ""
        echo "正在启动服务端，端口: $port"
        echo "访问地址: http://localhost:$port"
        echo "按 Ctrl+C 停止服务"
        echo ""
        
        python3 gpu_monitor_server.py --port $port
        ;;
    
    2)
        echo ""
        echo "启动客户端..."
        echo "============================================"
        
        # 检查requests
        if ! python3 -c "import requests" 2>/dev/null; then
            echo "⚠️  警告: 未安装requests库"
            read -p "是否现在安装? (y/n): " install_requests
            if [ "$install_requests" = "y" ]; then
                pip3 install --user requests || python3 -m pip install --user requests
            else
                echo "❌ 取消启动"
                exit 1
            fi
        fi
        
        # 检查nvidia-smi
        if ! command -v nvidia-smi &> /dev/null; then
            echo "❌ 错误: 未找到nvidia-smi命令"
            echo "请确保已安装NVIDIA驱动"
            exit 1
        fi
        
        read -p "请输入服务端地址 (例如: http://192.168.1.100:5000): " server_url
        
        if [ -z "$server_url" ]; then
            echo "❌ 错误: 服务端地址不能为空"
            exit 1
        fi
        
        read -p "请输入服务器名称 (默认使用主机名): " server_name
        
        read -p "请输入更新间隔/秒 (默认5): " interval
        interval=${interval:-5}
        
        echo ""
        echo "正在启动客户端..."
        
        if [ -z "$server_name" ]; then
            python3 gpu_monitor_client.py --server "$server_url" --interval $interval
        else
            python3 gpu_monitor_client.py --server "$server_url" --name "$server_name" --interval $interval
        fi
        ;;
    
    3)
        echo ""
        echo "测试nvidia-smi..."
        echo "============================================"
        
        if ! command -v nvidia-smi &> /dev/null; then
            echo "❌ 错误: 未找到nvidia-smi命令"
            echo "请确保已安装NVIDIA驱动"
            exit 1
        fi
        
        nvidia-smi
        echo ""
        echo "✅ nvidia-smi运行正常"
        ;;
    
    4)
        echo "退出"
        exit 0
        ;;
    
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

