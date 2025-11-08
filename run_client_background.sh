#!/bin/bash
# GPU Monitor Client - 后台运行脚本
cd /home/honglianglu/ssd/gpu_monitor
nohup python3 gpu_monitor_client.py --server http://192.168.100.201:1160 --name "aries" --interval 5 > gpu_client.log 2>&1 &
echo $! > gpu_client.pid
echo "✅ 客户端已在后台启动"
echo "服务器名称: aries"
echo "目标服务端: http://192.168.100.201:1160"
echo "PID: $(cat gpu_client.pid)"
echo "日志文件: gpu_client.log"
echo "停止服务: kill \$(cat gpu_client.pid)"
