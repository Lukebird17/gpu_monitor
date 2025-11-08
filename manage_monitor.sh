#!/bin/bash
# GPU监控系统管理脚本（无需sudo权限）

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

show_status() {
    echo "============================================"
    echo "       GPU监控系统运行状态"
    echo "============================================"
    echo ""
    
    # 检查服务端
    if [ -f "gpu_server.pid" ]; then
        SERVER_PID=$(cat gpu_server.pid)
        if ps -p $SERVER_PID > /dev/null 2>&1; then
            echo -e "服务端: ${GREEN}✅ 运行中${NC} (PID: $SERVER_PID)"
            echo "  日志: gpu_server.log"
        else
            echo -e "服务端: ${RED}❌ 已停止${NC} (PID文件存在但进程不存在)"
        fi
    else
        echo -e "服务端: ${YELLOW}⚪ 未运行${NC}"
    fi
    
    echo ""
    
    # 检查客户端
    if [ -f "gpu_client.pid" ]; then
        CLIENT_PID=$(cat gpu_client.pid)
        if ps -p $CLIENT_PID > /dev/null 2>&1; then
            echo -e "客户端: ${GREEN}✅ 运行中${NC} (PID: $CLIENT_PID)"
            echo "  日志: gpu_client.log"
        else
            echo -e "客户端: ${RED}❌ 已停止${NC} (PID文件存在但进程不存在)"
        fi
    else
        echo -e "客户端: ${YELLOW}⚪ 未运行${NC}"
    fi
    
    echo ""
    echo "所有GPU监控进程:"
    ps aux | grep -E "gpu_monitor_(server|client)" | grep -v grep || echo "  无"
}

stop_server() {
    echo "停止服务端..."
    if [ -f "gpu_server.pid" ]; then
        SERVER_PID=$(cat gpu_server.pid)
        if ps -p $SERVER_PID > /dev/null 2>&1; then
            kill $SERVER_PID
            sleep 1
            if ps -p $SERVER_PID > /dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  进程未响应，强制终止...${NC}"
                kill -9 $SERVER_PID 2>/dev/null
            fi
            echo -e "${GREEN}✅ 服务端已停止${NC}"
        else
            echo -e "${YELLOW}服务端进程不存在${NC}"
        fi
        rm -f gpu_server.pid
    else
        echo -e "${YELLOW}未找到服务端PID文件${NC}"
    fi
}

stop_client() {
    echo "停止客户端..."
    if [ -f "gpu_client.pid" ]; then
        CLIENT_PID=$(cat gpu_client.pid)
        if ps -p $CLIENT_PID > /dev/null 2>&1; then
            kill $CLIENT_PID
            sleep 1
            if ps -p $CLIENT_PID > /dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  进程未响应，强制终止...${NC}"
                kill -9 $CLIENT_PID 2>/dev/null
            fi
            echo -e "${GREEN}✅ 客户端已停止${NC}"
        else
            echo -e "${YELLOW}客户端进程不存在${NC}"
        fi
        rm -f gpu_client.pid
    else
        echo -e "${YELLOW}未找到客户端PID文件${NC}"
    fi
}

stop_all() {
    echo "停止所有监控进程..."
    stop_server
    stop_client
    
    # 清理可能遗留的进程
    pkill -f "gpu_monitor_server.py" 2>/dev/null
    pkill -f "gpu_monitor_client.py" 2>/dev/null
    
    echo -e "${GREEN}✅ 所有监控进程已停止${NC}"
}

view_server_log() {
    if [ -f "gpu_server.log" ]; then
        echo "服务端日志 (按Ctrl+C退出):"
        echo "============================================"
        tail -f gpu_server.log
    else
        echo -e "${RED}❌ 未找到服务端日志文件${NC}"
    fi
}

view_client_log() {
    if [ -f "gpu_client.log" ]; then
        echo "客户端日志 (按Ctrl+C退出):"
        echo "============================================"
        tail -f gpu_client.log
    else
        echo -e "${RED}❌ 未找到客户端日志文件${NC}"
    fi
}

restart_server() {
    echo "重启服务端..."
    stop_server
    sleep 1
    if [ -f "run_server_background.sh" ]; then
        ./run_server_background.sh
    else
        echo -e "${RED}❌ 未找到 run_server_background.sh${NC}"
        echo "请先运行 ./install_gpu_monitor.sh 创建启动脚本"
    fi
}

restart_client() {
    echo "重启客户端..."
    stop_client
    sleep 1
    if [ -f "run_client_background.sh" ]; then
        ./run_client_background.sh
    else
        echo -e "${RED}❌ 未找到 run_client_background.sh${NC}"
        echo "请先运行 ./install_gpu_monitor.sh 创建启动脚本"
    fi
}

# 主菜单
echo "============================================"
echo "       GPU监控系统 - 管理工具"
echo "============================================"
echo ""
echo "1) 查看运行状态"
echo "2) 停止服务端"
echo "3) 停止客户端"
echo "4) 停止所有服务"
echo "5) 重启服务端"
echo "6) 重启客户端"
echo "7) 查看服务端日志"
echo "8) 查看客户端日志"
echo "9) 退出"
echo ""
read -p "请选择操作 (1-9): " choice

case $choice in
    1)
        show_status
        ;;
    2)
        stop_server
        ;;
    3)
        stop_client
        ;;
    4)
        stop_all
        ;;
    5)
        restart_server
        ;;
    6)
        restart_client
        ;;
    7)
        view_server_log
        ;;
    8)
        view_client_log
        ;;
    9)
        echo "退出"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ 无效选项${NC}"
        exit 1
        ;;
esac

