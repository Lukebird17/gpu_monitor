# GPU监控系统使用说明

这是一个用于实时监控多台服务器GPU使用情况的系统，包含一个Web服务端和多个客户端。

## 系统架构

- **服务端** (`gpu_monitor_server.py`): 提供Web界面和API接口，展示所有服务器的GPU状态
- **客户端** (`gpu_monitor_client.py`): 在各个服务器上运行，收集GPU信息并发送到服务端

## 功能特点

✨ **实时监控**: 每5秒自动刷新，实时显示GPU状态  
📊 **详细信息**: 显示GPU使用率、显存、温度、功耗等  
🔄 **进程监控**: 显示每个GPU上运行的进程  
🎨 **美观界面**: 现代化的Web界面，支持多服务器展示  
⚡ **自动恢复**: 客户端自动重连，服务端自动标记离线服务器  

## 安装依赖

### 服务端依赖

```bash
pip install flask
```

### 客户端依赖

```bash
pip install requests
```

**注意**: 客户端需要安装NVIDIA驱动和`nvidia-smi`工具

## 使用方法

### 1. 启动服务端（在一台服务器上）

```bash
# 基本用法（监听5000端口）
python gpu_monitor_server.py

# 自定义端口
python gpu_monitor_server.py --port 8080

# 指定监听地址
python gpu_monitor_server.py --host 0.0.0.0 --port 5000
```

启动后，访问 `http://your-server-ip:5000` 即可查看监控页面

### 2. 在每台GPU服务器上启动客户端

```bash
# 基本用法（自动使用主机名作为服务器名称）
python gpu_monitor_client.py --server http://192.168.1.100:5000

# 自定义服务器名称
python gpu_monitor_client.py --server http://192.168.1.100:5000 --name "深度学习服务器1"

# 自定义更新间隔（秒）
python gpu_monitor_client.py --server http://192.168.1.100:5000 --name "GPU-Server-1" --interval 10
```

### 3. 后台运行客户端

使用`nohup`或`screen`在后台运行客户端：

**方法1: 使用nohup**
```bash
nohup python gpu_monitor_client.py --server http://192.168.1.100:5000 --name "服务器1" > gpu_client.log 2>&1 &
```

**方法2: 使用screen**
```bash
screen -S gpu_monitor
python gpu_monitor_client.py --server http://192.168.1.100:5000 --name "服务器1"
# 按 Ctrl+A 然后 D 退出screen
```

**方法3: 使用systemd服务（推荐用于生产环境）**

创建服务文件 `/etc/systemd/system/gpu-monitor-client.service`:

```ini
[Unit]
Description=GPU Monitor Client
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username
ExecStart=/usr/bin/python3 /home/your-username/gpu_monitor_client.py --server http://192.168.1.100:5000 --name "服务器1"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

然后启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl start gpu-monitor-client
sudo systemctl enable gpu-monitor-client  # 开机自启动
sudo systemctl status gpu-monitor-client  # 查看状态
```

## 端口转发配置

如果你的服务端在内网，需要通过SSH端口转发访问：

### 本地端口转发
```bash
ssh -L 5000:localhost:5000 user@your-server-ip
```
然后在本地浏览器访问 `http://localhost:5000`

### 配置防火墙（如果需要外网访问）
```bash
# Ubuntu/Debian
sudo ufw allow 5000/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

## API接口

系统提供以下API接口：

### 1. 获取所有服务器数据（JSON格式）
```
GET http://your-server:5000/api/data
```

### 2. 更新GPU数据（客户端使用）
```
POST http://your-server:5000/api/update
Content-Type: application/json

{
  "server_name": "服务器1",
  "timestamp": "2024-01-01 12:00:00",
  "gpus": [...]
}
```

## 监控指标说明

| 指标 | 说明 |
|------|------|
| GPU使用率 | GPU核心的计算使用率百分比 |
| 显存使用 | 已使用显存 / 总显存 |
| 温度 | GPU当前温度（°C）|
| 功耗 | 当前功耗 / 功耗限制 |
| 运行进程 | 在GPU上运行的进程列表及其显存占用 |

## 故障排查

### 问题1: 客户端无法连接服务端
- 检查服务端是否正常运行
- 检查防火墙设置
- 确认服务器地址和端口正确
- 使用 `curl http://your-server:5000/api/data` 测试连接

### 问题2: 客户端显示"未找到nvidia-smi命令"
- 确认已安装NVIDIA驱动
- 运行 `nvidia-smi` 测试是否可用
- 检查PATH环境变量

### 问题3: 服务器显示"离线"
- 检查客户端是否正在运行
- 查看客户端日志输出
- 确认网络连接正常
- 服务器超过60秒未收到数据会标记为离线

### 问题4: Web页面不刷新
- 检查浏览器控制台是否有错误
- 尝试手动刷新页面（F5）
- 清除浏览器缓存

## 性能说明

- **服务端**: 轻量级Flask应用，资源占用很小
- **客户端**: 每次查询仅调用nvidia-smi，CPU和内存占用可忽略不计
- **网络流量**: 每次更新约1-5KB（取决于GPU和进程数量）
- **更新频率**: 默认5秒，可根据需要调整

## 自定义配置

### 修改数据过期时间
编辑 `gpu_monitor_server.py`，修改：
```python
DATA_TIMEOUT = 60  # 改为你想要的秒数
```

### 修改页面自动刷新间隔
编辑 `gpu_monitor_server.py` 中的HTML模板，修改：
```javascript
setInterval(function() {
    location.reload();
}, 5000);  // 改为你想要的毫秒数
```

## 安全建议

1. **生产环境建议**:
   - 使用Nginx反向代理
   - 启用HTTPS
   - 添加身份认证
   - 限制访问IP

2. **示例Nginx配置**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # 可选：添加基本认证
        auth_basic "GPU Monitor";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

## 许可证

此脚本可自由使用和修改。

## 问题反馈

如有问题或建议，请联系管理员。

---

**最后更新**: 2024

