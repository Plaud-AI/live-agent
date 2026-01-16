#!/bin/bash
# =============================================================================
# Live-Agent 一键部署脚本 (基于 Dokploy)
# 适用于 AWS EC2 / Ubuntu 22.04+
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Banner
echo -e "${CYAN}"
cat << "EOF"
 _     _             _                         _   
| |   (_)_   _____  / \   __ _  ___ _ __ | |_ 
| |   | \ \ / / _ \/ _ \ / _` |/ _ \ '_ \| __|
| |___| |\ V /  __/ ___ \ (_| |  __/ | | | |_ 
|_____|_| \_/ \___/_/   \_\__, |\___|_| |_|\__|
                         |___/                
    Dokploy 一键部署脚本 v1.0
EOF
echo -e "${NC}"

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    print_error "请使用 root 权限运行此脚本: sudo bash $0"
    exit 1
fi

# 获取公网 IP
PUBLIC_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || hostname -I | awk '{print $1}')
print_info "检测到公网 IP: $PUBLIC_IP"

# 配置变量
INSTALL_DIR="/opt/live-agent"
MYSQL_PASSWORD=${MYSQL_PASSWORD:-$(openssl rand -base64 12)}
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-$(openssl rand -base64 12)}

print_info "安装目录: $INSTALL_DIR"
print_info "MySQL 密码将自动生成并保存"

# =============================================================================
# Step 1: 安装 Docker (如果未安装)
# =============================================================================
install_docker() {
    print_info "检查 Docker 安装状态..."
    
    if command -v docker &> /dev/null; then
        print_success "Docker 已安装: $(docker --version)"
        return 0
    fi

    print_info "正在安装 Docker..."
    
    # 安装依赖
    apt-get update
    apt-get install -y apt-transport-https ca-certificates curl software-properties-common gnupg

    # 添加 Docker GPG 密钥
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # 添加 Docker 仓库
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list

    # 安装 Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # 启动 Docker
    systemctl start docker
    systemctl enable docker

    print_success "Docker 安装完成!"
}

# =============================================================================
# Step 2: 安装 Dokploy
# =============================================================================
install_dokploy() {
    print_info "检查 Dokploy 安装状态..."
    
    if docker ps | grep -q "dokploy"; then
        print_success "Dokploy 已在运行"
        return 0
    fi

    print_info "正在安装 Dokploy..."
    curl -sSL https://dokploy.com/install.sh | sh
    
    print_success "Dokploy 安装完成!"
    print_info "Dokploy 面板地址: http://$PUBLIC_IP:3000"
}

# =============================================================================
# Step 3: 创建项目目录结构
# =============================================================================
setup_directories() {
    print_info "创建项目目录结构..."
    
    mkdir -p $INSTALL_DIR/{data,models/SenseVoiceSmall,mysql/data,uploadfile,logs}
    
    print_success "目录结构创建完成!"
}

# =============================================================================
# Step 4: 下载语音识别模型
# =============================================================================
download_model() {
    MODEL_PATH="$INSTALL_DIR/models/SenseVoiceSmall/model.pt"
    
    if [ -f "$MODEL_PATH" ]; then
        print_success "语音识别模型已存在，跳过下载"
        return 0
    fi

    print_info "正在下载语音识别模型 (约 900MB，请耐心等待)..."
    
    curl -fL --progress-bar \
        https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt \
        -o "$MODEL_PATH"
    
    if [ -f "$MODEL_PATH" ]; then
        print_success "语音识别模型下载完成!"
    else
        print_error "模型下载失败，请手动下载"
        print_info "下载地址: https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt"
        print_info "保存到: $MODEL_PATH"
    fi
}

# =============================================================================
# Step 5: 生成 Docker Compose 文件
# =============================================================================
generate_docker_compose() {
    print_info "生成 Docker Compose 配置文件..."
    
    cat > $INSTALL_DIR/docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  # ==================== MySQL 数据库 ====================
  xiaozhi-esp32-server-db:
    image: mysql:8.0
    container_name: xiaozhi-esp32-server-db
    restart: always
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 45s
      interval: 10s
      retries: 10
    networks:
      - live-agent-network
    expose:
      - 3306
    volumes:
      - ./mysql/data:/var/lib/mysql
    environment:
      - TZ=Asia/Shanghai
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=xiaozhi_esp32_server
      - MYSQL_USER=xiaozhi
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}

  # ==================== Redis 缓存 ====================
  xiaozhi-esp32-server-redis:
    image: redis:7-alpine
    container_name: xiaozhi-esp32-server-redis
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - live-agent-network
    expose:
      - 6379
    volumes:
      - redis-data:/data

  # ==================== Java API + Vue Web ====================
  xiaozhi-esp32-server-web:
    image: ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:web_latest
    container_name: xiaozhi-esp32-server-web
    restart: always
    depends_on:
      xiaozhi-esp32-server-db:
        condition: service_healthy
      xiaozhi-esp32-server-redis:
        condition: service_healthy
    networks:
      - live-agent-network
    ports:
      - "8002:8002"
    environment:
      - TZ=Asia/Shanghai
      - SPRING_DATASOURCE_DRUID_URL=jdbc:mysql://xiaozhi-esp32-server-db:3306/xiaozhi_esp32_server?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai&nullCatalogMeansCurrent=true&connectTimeout=30000&socketTimeout=30000&autoReconnect=true&failOverReadOnly=false&maxReconnects=10
      - SPRING_DATASOURCE_DRUID_USERNAME=root
      - SPRING_DATASOURCE_DRUID_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - SPRING_DATA_REDIS_HOST=xiaozhi-esp32-server-redis
      - SPRING_DATA_REDIS_PASSWORD=
      - SPRING_DATA_REDIS_PORT=6379
    volumes:
      - ./uploadfile:/uploadfile

  # ==================== Python WebSocket Server ====================
  xiaozhi-esp32-server:
    image: ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:server_latest
    container_name: xiaozhi-esp32-server
    restart: always
    depends_on:
      - xiaozhi-esp32-server-db
      - xiaozhi-esp32-server-redis
      - xiaozhi-esp32-server-web
    networks:
      - live-agent-network
    ports:
      - "8000:8000"
      - "8003:8003"
    security_opt:
      - seccomp:unconfined
    environment:
      - TZ=Asia/Shanghai
    volumes:
      - ./data:/opt/xiaozhi-esp32-server/data
      - ./models/SenseVoiceSmall/model.pt:/opt/xiaozhi-esp32-server/models/SenseVoiceSmall/model.pt:ro
      - ./logs:/opt/xiaozhi-esp32-server/logs

networks:
  live-agent-network:
    driver: bridge

volumes:
  redis-data:
COMPOSE_EOF

    print_success "Docker Compose 配置文件已生成!"
}

# =============================================================================
# Step 6: 生成环境变量文件
# =============================================================================
generate_env_file() {
    print_info "生成环境变量文件..."
    
    cat > $INSTALL_DIR/.env << EOF
# Live-Agent 环境配置
# 生成时间: $(date)

# MySQL 配置
MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD
MYSQL_PASSWORD=$MYSQL_PASSWORD
MYSQL_DATABASE=xiaozhi_esp32_server

# 服务器配置
PUBLIC_IP=$PUBLIC_IP
EOF

    chmod 600 $INSTALL_DIR/.env
    print_success "环境变量文件已生成!"
}

# =============================================================================
# Step 7: 生成初始配置文件
# =============================================================================
generate_config() {
    print_info "生成服务配置文件..."
    
    cat > $INSTALL_DIR/data/.config.yaml << EOF
# Live-Agent Server 配置文件
# 注意: 部署完成后，请从智控台获取 server.secret 并更新此文件

server:
  ip: 0.0.0.0
  port: 8000
  http_port: 8003
  vision_explain: http://$PUBLIC_IP:8003/mcp/vision/explain

manager-api:
  url: http://xiaozhi-esp32-server-web:8002/xiaozhi
  secret: 请从智控台参数管理中获取server.secret

prompt_template: agent-base-prompt.txt
EOF

    print_success "服务配置文件已生成!"
}

# =============================================================================
# Step 8: 启动服务
# =============================================================================
start_services() {
    print_info "启动所有服务..."
    
    cd $INSTALL_DIR
    docker compose pull
    docker compose up -d
    
    print_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    if docker ps | grep -q "xiaozhi-esp32-server-web"; then
        print_success "智控台服务已启动!"
    else
        print_warning "智控台服务启动中，请稍候..."
    fi
    
    if docker ps | grep -q "xiaozhi-esp32-server "; then
        print_success "WebSocket 服务已启动!"
    else
        print_warning "WebSocket 服务启动中，请稍候..."
    fi
}

# =============================================================================
# Step 9: 保存部署信息
# =============================================================================
save_deployment_info() {
    print_info "保存部署信息..."
    
    cat > $INSTALL_DIR/deployment-info.txt << EOF
================================================================================
                    Live-Agent 部署信息
                    生成时间: $(date)
================================================================================

【服务地址】
智控台:          http://$PUBLIC_IP:8002
WebSocket:       ws://$PUBLIC_IP:8000/xiaozhi/v1/
OTA 接口:        http://$PUBLIC_IP:8002/xiaozhi/ota/
视觉分析接口:    http://$PUBLIC_IP:8003/mcp/vision/explain
Dokploy 面板:    http://$PUBLIC_IP:3000

【数据库信息】
MySQL Root 密码: $MYSQL_ROOT_PASSWORD
MySQL 用户密码:  $MYSQL_PASSWORD
数据库名称:      xiaozhi_esp32_server

【安装目录】
$INSTALL_DIR/
├── data/              # Server 配置和数据
├── models/            # 语音识别模型
├── mysql/data/        # MySQL 数据
├── uploadfile/        # 上传文件
├── logs/              # 日志文件
├── docker-compose.yml # Docker 配置
└── .env               # 环境变量

【部署后必做事项】
1. 访问智控台 http://$PUBLIC_IP:8002 注册超级管理员账号
2. 登录后进入 [参数管理]，复制 server.secret 的参数值
3. 编辑配置文件: nano $INSTALL_DIR/data/.config.yaml
   将 secret 的值替换为刚才复制的 server.secret
4. 重启 Server: docker restart xiaozhi-esp32-server
5. 进入 [模型配置] > [大语言模型]，配置你的 LLM API 密钥

【常用命令】
查看所有容器状态:    docker ps
查看 Server 日志:    docker logs -f xiaozhi-esp32-server
查看智控台日志:      docker logs -f xiaozhi-esp32-server-web
重启所有服务:        cd $INSTALL_DIR && docker compose restart
停止所有服务:        cd $INSTALL_DIR && docker compose down
启动所有服务:        cd $INSTALL_DIR && docker compose up -d

================================================================================
EOF

    print_success "部署信息已保存到: $INSTALL_DIR/deployment-info.txt"
}

# =============================================================================
# Step 10: 打印完成信息
# =============================================================================
print_completion() {
    echo ""
    echo -e "${GREEN}=============================================================================${NC}"
    echo -e "${GREEN}                    🎉 部署完成！                                           ${NC}"
    echo -e "${GREEN}=============================================================================${NC}"
    echo ""
    echo -e "${CYAN}【服务地址】${NC}"
    echo -e "  智控台:          ${YELLOW}http://$PUBLIC_IP:8002${NC}"
    echo -e "  WebSocket:       ${YELLOW}ws://$PUBLIC_IP:8000/xiaozhi/v1/${NC}"
    echo -e "  Dokploy 面板:    ${YELLOW}http://$PUBLIC_IP:3000${NC}"
    echo ""
    echo -e "${CYAN}【数据库密码】${NC}"
    echo -e "  MySQL Root:      ${YELLOW}$MYSQL_ROOT_PASSWORD${NC}"
    echo ""
    echo -e "${RED}【重要！部署后必做事项】${NC}"
    echo -e "  1. 访问智控台注册超级管理员账号"
    echo -e "  2. 从 [参数管理] 复制 server.secret"
    echo -e "  3. 更新配置: ${YELLOW}nano $INSTALL_DIR/data/.config.yaml${NC}"
    echo -e "  4. 重启服务: ${YELLOW}docker restart xiaozhi-esp32-server${NC}"
    echo -e "  5. 配置 LLM API 密钥"
    echo ""
    echo -e "${CYAN}详细信息已保存到: ${YELLOW}$INSTALL_DIR/deployment-info.txt${NC}"
    echo ""
}

# =============================================================================
# 主流程
# =============================================================================
main() {
    echo ""
    print_info "开始部署 Live-Agent..."
    echo ""
    
    install_docker
    install_dokploy
    setup_directories
    download_model
    generate_docker_compose
    generate_env_file
    generate_config
    start_services
    save_deployment_info
    print_completion
}

# 执行主流程
main

