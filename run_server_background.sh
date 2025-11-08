#!/bin/bash
# GPU Monitor Server - 后台运行脚本
cd /home/honglianglu/ssd/gpu_monitor
nohup python3 gpu_monitor_server.py --host 0.0.0.0 --port 1160 > gpu_server.log 2>&1 &
echo $! > gpu_server.pid
echo "✅ 服务端已在后台启动"
echo "PID: $(cat gpu_server.pid)"
echo "日志文件: gpu_server.log"
echo "停止服务: kill \$(cat gpu_server.pid)"
