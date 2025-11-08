#!/bin/bash
# GPU监控系统一键安装脚本（无需sudo权限）

echo "============================================"
echo "    GPU监控系统 - 安装脚本（无sudo版本）"
echo "============================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python
echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误: 未找到python3${NC}"
    echo "请联系管理员安装Python 3.6或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✅ 找到Python: $PYTHON_VERSION${NC}"

# 检查pip
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo -e "${RED}❌ 错误: 未找到pip3${NC}"
    echo "请联系管理员安装pip，或尝试运行: python3 -m ensurepip --user"
    exit 1
fi

echo ""
echo "请选择安装类型:"
echo "1) 安装服务端（Web监控服务器）"
echo "2) 安装客户端（GPU数据收集器）"
echo "3) 同时安装服务端和客户端"
echo ""
read -p "请输入选项 (1-3): " install_type

case $install_type in
    1)
        INSTALL_SERVER=true
        INSTALL_CLIENT=false
        ;;
    2)
        INSTALL_SERVER=false
        INSTALL_CLIENT=true
        ;;
    3)
        INSTALL_SERVER=true
        INSTALL_CLIENT=true
        ;;
    *)
        echo -e "${RED}❌ 无效选项${NC}"
        exit 1
        ;;
esac

echo ""
echo "============================================"
echo "开始安装依赖包..."
echo "============================================"

if [ "$INSTALL_SERVER" = true ]; then
    echo "安装服务端依赖: Flask..."
    pip3 install --user flask || python3 -m pip install --user flask || {
        echo -e "${RED}❌ Flask安装失败${NC}"
        echo "请尝试手动安装: pip3 install --user flask"
        exit 1
    }
    echo -e "${GREEN}✅ Flask安装完成${NC}"
fi

if [ "$INSTALL_CLIENT" = true ]; then
    echo "安装客户端依赖: requests..."
    pip3 install --user requests || python3 -m pip install --user requests || {
        echo -e "${RED}❌ requests安装失败${NC}"
        echo "请尝试手动安装: pip3 install --user requests"
        exit 1
    }
    echo -e "${GREEN}✅ requests安装完成${NC}"
    
    # 检查nvidia-smi
    echo ""
    echo "检查NVIDIA驱动..."
    if command -v nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✅ nvidia-smi可用${NC}"
        nvidia-smi --query-gpu=name --format=csv,noheader | while read gpu_name; do
            echo "   - 检测到GPU: $gpu_name"
        done
    else
        echo -e "${YELLOW}⚠️  警告: 未找到nvidia-smi命令${NC}"
        echo "客户端需要NVIDIA驱动才能运行"
        echo "请先安装NVIDIA驱动: https://www.nvidia.com/Download/index.aspx"
    fi
fi

echo ""
echo "============================================"
echo "创建后台运行脚本（无需sudo权限）"
echo "============================================"

CURRENT_DIR=$(pwd)

if [ "$INSTALL_SERVER" = true ]; then
    read -p "是否创建服务端后台运行脚本? (y/n): " create_server_script
    if [ "$create_server_script" = "y" ]; then
        read -p "请输入服务端监听端口 (默认5000): " server_port
        server_port=${server_port:-5000}
        
        cat > run_server_background.sh <<EOF
#!/bin/bash
# GPU Monitor Server - 后台运行脚本
cd $CURRENT_DIR
nohup python3 gpu_monitor_server.py --host 0.0.0.0 --port $server_port > gpu_server.log 2>&1 &
echo \$! > gpu_server.pid
echo "✅ 服务端已在后台启动"
echo "PID: \$(cat gpu_server.pid)"
echo "日志文件: gpu_server.log"
echo "停止服务: kill \\\$(cat gpu_server.pid)"
EOF
        chmod +x run_server_background.sh
        echo -e "${GREEN}✅ 创建完成: run_server_background.sh${NC}"
        
        read -p "是否现在启动服务端? (y/n): " start_now
        if [ "$start_now" = "y" ]; then
            ./run_server_background.sh
            sleep 2
            echo ""
            echo "服务端状态:"
            if ps -p $(cat gpu_server.pid 2>/dev/null) > /dev/null 2>&1; then
                echo -e "${GREEN}✅ 运行中 (PID: $(cat gpu_server.pid))${NC}"
            else
                echo -e "${RED}❌ 启动失败，请查看日志: tail gpu_server.log${NC}"
            fi
        fi
    fi
fi

if [ "$INSTALL_CLIENT" = true ]; then
    read -p "是否创建客户端后台运行脚本? (y/n): " create_client_script
    if [ "$create_client_script" = "y" ]; then
        read -p "请输入服务端地址 (例如: http://192.168.1.100:5000): " server_url
        read -p "请输入此服务器的名称 (默认使用主机名): " server_name
        server_name=${server_name:-$(hostname)}
        
        cat > run_client_background.sh <<EOF
#!/bin/bash
# GPU Monitor Client - 后台运行脚本
cd $CURRENT_DIR
nohup python3 gpu_monitor_client.py --server $server_url --name "$server_name" --interval 5 > gpu_client.log 2>&1 &
echo \$! > gpu_client.pid
echo "✅ 客户端已在后台启动"
echo "服务器名称: $server_name"
echo "目标服务端: $server_url"
echo "PID: \$(cat gpu_client.pid)"
echo "日志文件: gpu_client.log"
echo "停止服务: kill \\\$(cat gpu_client.pid)"
EOF
        chmod +x run_client_background.sh
        echo -e "${GREEN}✅ 创建完成: run_client_background.sh${NC}"
        
        read -p "是否现在启动客户端? (y/n): " start_now
        if [ "$start_now" = "y" ]; then
            ./run_client_background.sh
            sleep 2
            echo ""
            echo "客户端状态:"
            if ps -p $(cat gpu_client.pid 2>/dev/null) > /dev/null 2>&1; then
                echo -e "${GREEN}✅ 运行中 (PID: $(cat gpu_client.pid))${NC}"
            else
                echo -e "${RED}❌ 启动失败，请查看日志: tail gpu_client.log${NC}"
            fi
        fi
    fi
fi

echo ""
echo "============================================"
echo -e "${GREEN}✅ 安装完成！${NC}"
echo "============================================"
echo ""

if [ "$INSTALL_SERVER" = true ]; then
    echo "服务端使用方法:"
    echo "  前台启动: python3 gpu_monitor_server.py --port 5000"
    echo "  后台启动: ./run_server_background.sh (如果已创建)"
    echo "  交互式启动: ./start_gpu_monitor.sh"
    echo "  查看日志: tail -f gpu_server.log"
    echo "  停止服务: kill \$(cat gpu_server.pid)"
    echo ""
fi

if [ "$INSTALL_CLIENT" = true ]; then
    echo "客户端使用方法:"
    echo "  前台启动: python3 gpu_monitor_client.py --server http://SERVER_IP:5000 --name \"名称\""
    echo "  后台启动: ./run_client_background.sh (如果已创建)"
    echo "  交互式启动: ./start_gpu_monitor.sh"
    echo "  查看日志: tail -f gpu_client.log"
    echo "  停止服务: kill \$(cat gpu_client.pid)"
    echo ""
fi

echo "常用命令:"
echo "  查看运行进程: ps aux | grep gpu_monitor"
echo "  停止所有监控: pkill -f gpu_monitor"
echo ""
echo "详细文档请查看: GPU_MONITOR_README.md"
echo ""

