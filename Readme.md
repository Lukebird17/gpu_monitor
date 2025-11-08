# GPU监控系统 - 配置说明

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         你的浏览器                           │
│                  访问 http://服务端IP:5000                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    服务端 (Server)                           │
│        运行在：一台可以被其他机器访问的服务器上               │
│        作用：                                                │
│          1. 提供Web监控界面                                  │
│          2. 接收所有客户端发送的GPU数据                       │
│          3. 汇总显示所有服务器的GPU状态                       │
└─────────────────────────────────────────────────────────────┘
                              ↑
                              │ HTTP POST
              ┌───────────────┼───────────────┐
              ↓               ↓               ↓
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │  客户端 #1   │  │  客户端 #2   │  │  客户端 #3   │
    │ GPU服务器1   │  │ GPU服务器2   │  │ GPU服务器3   │
    │              │  │              │  │              │
    │ 作用：       │  │ 作用：       │  │ 作用：       │
    │ 1.读取本地   │  │ 1.读取本地   │  │ 1.读取本地   │
    │   GPU信息    │  │   GPU信息    │  │   GPU信息    │
    │ 2.发送到     │  │ 2.发送到     │  │ 2.发送到     │
    │   服务端     │  │   服务端     │  │   服务端     │
    └──────────────┘  └──────────────┘  └──────────────┘
```

## 📍 部署位置

### 服务端 (gpu_monitor_server.py)
**运行在哪里**: 
- 选择**一台**服务器运行即可
- 这台服务器需要能被所有GPU服务器访问到
- 可以是其中一台GPU服务器，也可以是单独的监控服务器

**推荐选择**:
- ✅ 有公网IP或固定内网IP的服务器
- ✅ 网络稳定、不经常重启的服务器
- ✅ 可以是你常用的主服务器或登录节点

### 客户端 (gpu_monitor_client.py)
**运行在哪里**:
- 在**每一台**需要监控的GPU服务器上都要运行
- 包括运行服务端的那台机器（如果它也有GPU需要监控）

---

## ⚙️ 服务端配置参数

### 命令格式
```bash
python3 gpu_monitor_server.py [参数]
```

### 必需参数
**无** - 所有参数都是可选的，有默认值

### 可选参数

| 参数 | 默认值 | 说明 | 示例 |
|------|--------|------|------|
| `--port` | 5000 | Web服务监听的端口号 | `--port 8080` |
| `--host` | 0.0.0.0 | 监听地址，0.0.0.0表示所有网络接口 | `--host 0.0.0.0` |

### 配置示例

**例1: 使用默认配置（最简单）**
```bash
python3 gpu_monitor_server.py
# 监听 0.0.0.0:5000
# 访问: http://服务器IP:5000
```

**例2: 自定义端口**
```bash
python3 gpu_monitor_server.py --port 8080
# 监听 0.0.0.0:8080
# 访问: http://服务器IP:8080
```

**例3: 只允许本地访问（用于SSH端口转发）**
```bash
python3 gpu_monitor_server.py --host 127.0.0.1 --port 5000
# 监听 127.0.0.1:5000
# 只能从本机访问，或通过SSH隧道访问
```

### 后台运行示例
```bash
nohup python3 gpu_monitor_server.py --port 5000 > gpu_server.log 2>&1 &
echo $! > gpu_server.pid
```

---

## ⚙️ 客户端配置参数

### 命令格式
```bash
python3 gpu_monitor_client.py [参数]
```

### 必需参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--server` | **必需！** 服务端的完整地址 | `--server http://192.168.1.100:5000` |

### 可选参数

| 参数 | 默认值 | 说明 | 示例 |
|------|--------|------|------|
| `--name` | 主机名 | 在监控页面显示的服务器名称 | `--name "深度学习服务器1"` |
| `--interval` | 5 | 更新间隔（秒） | `--interval 10` |

### 配置示例

**例1: 最简配置（使用主机名）**
```bash
python3 gpu_monitor_client.py --server http://192.168.1.100:5000
# 服务器名称自动使用主机名
# 每5秒更新一次
```

**例2: 自定义服务器名称**
```bash
python3 gpu_monitor_client.py \
  --server http://192.168.1.100:5000 \
  --name "GPU服务器-实验室A"
# 在监控页面会显示为 "GPU服务器-实验室A"
```

**例3: 完整配置**
```bash
python3 gpu_monitor_client.py \
  --server http://192.168.1.100:5000 \
  --name "V100-Server-01" \
  --interval 10
# 每10秒更新一次数据
```

**例4: 服务端在本机**
```bash
python3 gpu_monitor_client.py --server http://localhost:5000 --name "本机GPU"
# 服务端和客户端在同一台机器
```

### 后台运行示例
```bash
nohup python3 gpu_monitor_client.py \
  --server http://192.168.1.100:5000 \
  --name "GPU-Server-$(hostname)" \
  --interval 5 \
  > gpu_client.log 2>&1 &
echo $! > gpu_client.pid
```

---

## 🎯 实际部署场景

### 场景1: 单台服务器（自己监控自己）

```bash
# 在同一台机器上

# 1. 启动服务端（终端1或后台）
python3 gpu_monitor_server.py --port 5000

# 2. 启动客户端（终端2或后台）
python3 gpu_monitor_client.py \
  --server http://localhost:5000 \
  --name "我的GPU服务器"

# 3. 浏览器访问
# http://localhost:5000
```

### 场景2: 实验室多台GPU服务器

**环境假设**:
- 服务端机器: `gpu-master.lab.com` (IP: 192.168.1.100)
- GPU服务器1: `gpu-node1.lab.com` (IP: 192.168.1.101)
- GPU服务器2: `gpu-node2.lab.com` (IP: 192.168.1.102)
- GPU服务器3: `gpu-node3.lab.com` (IP: 192.168.1.103)

**在 gpu-master (192.168.1.100) 上**:
```bash
# 启动服务端
nohup python3 gpu_monitor_server.py --port 5000 > gpu_server.log 2>&1 &
echo $! > gpu_server.pid

# 如果master也有GPU要监控，也启动客户端
nohup python3 gpu_monitor_client.py \
  --server http://localhost:5000 \
  --name "Master节点" \
  > gpu_client.log 2>&1 &
echo $! > gpu_client.pid
```

**在 gpu-node1 (192.168.1.101) 上**:
```bash
nohup python3 gpu_monitor_client.py \
  --server http://192.168.1.100:5000 \
  --name "Node-1 (4xV100)" \
  > gpu_client.log 2>&1 &
echo $! > gpu_client.pid
```

**在 gpu-node2 (192.168.1.102) 上**:
```bash
nohup python3 gpu_monitor_client.py \
  --server http://192.168.1.100:5000 \
  --name "Node-2 (8xA100)" \
  > gpu_client.log 2>&1 &
echo $! > gpu_client.pid
```

**在 gpu-node3 (192.168.1.103) 上**:
```bash
nohup python3 gpu_monitor_client.py \
  --server http://192.168.1.100:5000 \
  --name "Node-3 (测试机)" \
  > gpu_client.log 2>&1 &
echo $! > gpu_client.pid
```

**访问监控页面**:
```
http://192.168.1.100:5000
```

### 场景3: 跨服务器集群

如果你有多个不同的集群或数据中心：

**选项A: 每个集群一个服务端**
```
集群A: http://cluster-a.com:5000
集群B: http://cluster-b.com:5000
```

**选项B: 统一服务端（推荐）**
```
所有客户端都连接到: http://central-monitor.com:5000
通过服务器名称区分: "集群A-GPU1", "集群B-GPU2"
```

---

## 🔍 如何确定服务端地址

### 方法1: 查看IP地址
```bash
# 在服务端机器上运行
ip addr show | grep "inet " | grep -v 127.0.0.1
# 或者
hostname -I
```

### 方法2: 测试连通性
```bash
# 在客户端机器上测试能否访问服务端
ping 192.168.1.100
curl http://192.168.1.100:5000
```

### 方法3: 如果有域名
```bash
# 直接使用域名
--server http://gpu-master.lab.com:5000
```

---

## ✅ 配置检查清单

### 服务端检查
- [ ] 选择了一台稳定的服务器
- [ ] 确定了端口号（默认5000）
- [ ] 启动了服务端进程
- [ ] 可以在本机访问 `http://localhost:端口`
- [ ] 防火墙允许该端口（如果需要）

### 客户端检查
- [ ] 知道服务端的IP地址和端口
- [ ] 能ping通服务端
- [ ] 能访问服务端API: `curl http://服务端IP:端口/api/data`
- [ ] nvidia-smi命令可用
- [ ] 设置了容易识别的服务器名称
- [ ] 启动了客户端进程

### 测试验证
```bash
# 1. 在服务端机器上
curl http://localhost:5000
# 应该看到HTML页面

curl http://localhost:5000/api/data
# 应该返回JSON数据

# 2. 在客户端机器上
curl http://服务端IP:5000
# 应该能访问

# 3. 启动客户端后，查看日志
tail -f gpu_client.log
# 应该看到 "✅ 数据发送成功"

# 4. 浏览器访问
# http://服务端IP:5000
# 应该看到客户端的服务器名称和GPU信息
```

---

## 💡 常见配置问题

### Q1: 服务端地址应该填什么？
**A**: 填写服务端机器的IP地址或域名，加上端口号

正确示例：
```bash
--server http://192.168.1.100:5000
--server http://gpu-master.lab.com:5000
--server http://localhost:5000  # 如果在同一台机器
```

错误示例：
```bash
--server 192.168.1.100  # ❌ 缺少 http:// 和端口
--server http://192.168.1.100/  # ❌ 末尾不要加 /
--server localhost:5000  # ❌ 缺少 http://
```

### Q2: 服务器名称应该怎么取？
**A**: 取一个你能识别的名字，建议包含：
- 机器位置/编号
- GPU型号
- 用途

示例：
```bash
--name "实验室A-GPU1 (4xV100)"
--name "深度学习服务器-主节点"
--name "测试机-2080Ti"
--name "$(hostname)-$(whoami)"  # 自动使用主机名和用户名
```

### Q3: 服务端需要在每台机器上都运行吗？
**A**: ❌ **不需要！** 只需要在一台机器上运行服务端
- 服务端：只运行**1个**
- 客户端：每台GPU服务器运行**1个**

### Q4: 端口号可以随便改吗？
**A**: 可以，但要注意：
- 服务端和客户端的端口要匹配
- 避免使用已被占用的端口
- 常用端口：5000, 8000, 8080, 8888

### Q5: 如何添加新的GPU服务器？
**A**: 只需在新服务器上：
```bash
# 1. 复制客户端文件
# 2. 安装依赖
pip3 install --user requests

# 3. 启动客户端
nohup python3 gpu_monitor_client.py \
  --server http://服务端IP:5000 \
  --name "新服务器名称" \
  > gpu_client.log 2>&1 &
```

不需要重启服务端！新客户端会自动出现在监控页面。

---

## 📝 配置文件示例

如果你想用配置文件而不是命令行参数，可以创建：

**run_server_background.sh**:
```bash
#!/bin/bash
cd /home/honglianglu/ssd/gpu_monitor
nohup python3 gpu_monitor_server.py \
  --host 0.0.0.0 \
  --port 5000 \
  > gpu_server.log 2>&1 &
echo $! > gpu_server.pid
echo "服务端已启动，PID: $(cat gpu_server.pid)"
echo "访问地址: http://$(hostname -I | awk '{print $1}'):5000"
```

**run_client_background.sh**:
```bash
#!/bin/bash
cd /home/honglianglu/ssd/gpu_monitor

# 配置参数
SERVER_URL="http://192.168.1.100:5000"
SERVER_NAME="GPU-$(hostname)"
UPDATE_INTERVAL=5

nohup python3 gpu_monitor_client.py \
  --server "$SERVER_URL" \
  --name "$SERVER_NAME" \
  --interval $UPDATE_INTERVAL \
  > gpu_client.log 2>&1 &
echo $! > gpu_client.pid
echo "客户端已启动，PID: $(cat gpu_client.pid)"
echo "服务器名称: $SERVER_NAME"
echo "连接到: $SERVER_URL"
```

---

需要更多帮助？查看 `快速使用指南.md` 或 `GPU_MONITOR_README.md`

