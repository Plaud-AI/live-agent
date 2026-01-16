# Live-Agent Dokploy 一键部署指南

本指南帮助你在 AWS EC2 上使用 Dokploy 一键部署 Live-Agent 项目。

## 📋 前置要求

### AWS EC2 配置

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| CPU | 2 vCPU | 4 vCPU |
| 内存 | 4 GB | 8 GB |
| 存储 | 40 GB SSD | 80 GB SSD |

### 安全组端口开放

| 端口 | 用途 |
|------|------|
| 22 | SSH |
| 80 | HTTP |
| 443 | HTTPS |
| 3000 | Dokploy 面板 |
| 8000 | WebSocket 服务 |
| 8002 | 智控台 |
| 8003 | 视觉分析接口 |

---

## 🚀 方式一：一键部署脚本（推荐）

SSH 连接到 EC2 后，执行以下命令：

```bash
# 下载并执行一键部署脚本
curl -sSL https://raw.githubusercontent.com/your-repo/live-agent/main/deploy/dokploy-deploy.sh | sudo bash
```

或者手动执行：

```bash
# 1. 下载脚本
wget https://raw.githubusercontent.com/your-repo/live-agent/main/deploy/dokploy-deploy.sh

# 2. 添加执行权限
chmod +x dokploy-deploy.sh

# 3. 执行脚本
sudo ./dokploy-deploy.sh
```

脚本会自动完成：
- ✅ 安装 Docker
- ✅ 安装 Dokploy
- ✅ 创建目录结构
- ✅ 下载语音识别模型
- ✅ 生成配置文件
- ✅ 启动所有服务

---

## 🛠 方式二：手动部署

### Step 1: 安装 Docker

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker
```

### Step 2: 安装 Dokploy

```bash
curl -sSL https://dokploy.com/install.sh | sh
```

安装完成后访问 `http://你的IP:3000` 创建管理员账号。

### Step 3: 创建目录和下载模型

```bash
# 创建目录
mkdir -p /opt/live-agent/{data,models/SenseVoiceSmall,mysql/data,uploadfile,logs}

# 下载语音识别模型 (约 900MB)
curl -fL https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt \
  -o /opt/live-agent/models/SenseVoiceSmall/model.pt
```

### Step 4: 在 Dokploy 中部署

1. 登录 Dokploy 面板
2. 创建新项目 → 选择 **Compose**
3. 将 `dokploy-compose.yml` 的内容粘贴到编辑器
4. 添加环境变量：
   ```
   MYSQL_ROOT_PASSWORD=你的安全密码
   ```
5. 配置 Volumes 映射：
   - `model-data` → `/opt/live-agent/models/SenseVoiceSmall`
   - `server-data` → `/opt/live-agent/data`
6. 点击 **Deploy**

---

## ⚙️ 部署后配置

### 1. 注册超级管理员

访问智控台 `http://你的IP:8002`，注册第一个账号（自动成为超级管理员）。

### 2. 配置 Server Secret

1. 登录智控台 → **参数管理**
2. 找到 `server.secret`，复制其**参数值**
3. 编辑配置文件：

```bash
nano /opt/live-agent/data/.config.yaml
```

修改内容：

```yaml
server:
  ip: 0.0.0.0
  port: 8000
  http_port: 8003
  vision_explain: http://你的公网IP:8003/mcp/vision/explain

manager-api:
  url: http://xiaozhi-esp32-server-web:8002/xiaozhi
  secret: 粘贴刚才复制的server.secret

prompt_template: agent-base-prompt.txt
```

4. 重启 Server：

```bash
docker restart xiaozhi-esp32-server
```

### 3. 配置 LLM API 密钥

1. 登录智控台 → **模型配置** → **大语言模型**
2. 选择你要使用的 LLM（如智谱AI）
3. 填入 API 密钥并保存

### 4. 配置参数（重要）

在智控台 **参数管理** 中更新：

| 参数编码 | 参数值 |
|---------|--------|
| `server.websocket` | `ws://你的公网IP:8000/xiaozhi/v1/` |
| `server.ota` | `http://你的公网IP:8002/xiaozhi/ota/` |

---

## 📊 服务地址汇总

| 服务 | 地址 |
|------|------|
| 智控台 | `http://你的IP:8002` |
| WebSocket | `ws://你的IP:8000/xiaozhi/v1/` |
| OTA 接口 | `http://你的IP:8002/xiaozhi/ota/` |
| 视觉分析 | `http://你的IP:8003/mcp/vision/explain` |
| Dokploy | `http://你的IP:3000` |

---

## 🔧 常用命令

```bash
# 查看所有容器状态
docker ps

# 查看 Server 日志
docker logs -f xiaozhi-esp32-server

# 查看智控台日志
docker logs -f xiaozhi-esp32-server-web

# 重启所有服务
cd /opt/live-agent && docker compose restart

# 停止所有服务
cd /opt/live-agent && docker compose down

# 启动所有服务
cd /opt/live-agent && docker compose up -d

# 更新镜像
cd /opt/live-agent && docker compose pull && docker compose up -d
```

---

## ❓ 常见问题

### Q: 智控台无法访问？

1. 检查 EC2 安全组是否开放 8002 端口
2. 检查容器是否运行：`docker ps`
3. 查看日志：`docker logs xiaozhi-esp32-server-web`

### Q: WebSocket 连接失败？

1. 检查 8000 端口是否开放
2. 确认 `server.secret` 配置正确
3. 重启 Server：`docker restart xiaozhi-esp32-server`

### Q: 语音识别不工作？

1. 确认模型文件已下载：`ls -la /opt/live-agent/models/SenseVoiceSmall/`
2. 模型文件大小应约 900MB
3. 检查 Server 日志是否有模型加载错误

---

## 📁 目录结构

```
/opt/live-agent/
├── data/                    # Server 配置和数据
│   └── .config.yaml         # 主配置文件
├── models/                  # AI 模型
│   └── SenseVoiceSmall/
│       └── model.pt         # 语音识别模型
├── mysql/data/              # MySQL 数据
├── uploadfile/              # 上传文件存储
├── logs/                    # 日志文件
├── docker-compose.yml       # Docker 配置
├── .env                     # 环境变量
└── deployment-info.txt      # 部署信息
```

---

## 📚 参考链接

- [Dokploy 官方文档](https://docs.dokploy.com)
- [Dokploy GitHub](https://github.com/dokploy/dokploy)
- [项目部署文档](../docs/Deployment_all.md)

