#!/bin/bash

# ================================================================================
# AWS 自动化部署脚本
# 用途：在 AWS EC2 Ubuntu 实例上快速部署 XiaoZhi AI Agent 服务
# 作者：AI Assistant
# 日期：2025-11-09
# ================================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_error "请不要使用 root 用户运行此脚本"
        log_info "请使用: bash deploy-aws.sh"
        exit 1
    fi
}

# 检查操作系统
check_os() {
    log_info "检查操作系统..."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "无法检测操作系统"
        exit 1
    fi
    
    if [[ $OS != "Ubuntu" ]]; then
        log_error "此脚本仅支持 Ubuntu 系统"
        exit 1
    fi
    
    log_success "操作系统: $OS $VER"
}

# 更新系统
update_system() {
    log_info "更新系统软件包..."
    sudo apt update && sudo apt upgrade -y
    log_success "系统更新完成"
}

# 安装 Docker
install_docker() {
    if command -v docker &> /dev/null; then
        log_warning "Docker 已安装，跳过"
        docker --version
    else
        log_info "安装 Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        sudo systemctl enable docker
        sudo systemctl start docker
        rm get-docker.sh
        log_success "Docker 安装完成"
        log_warning "请重新登录以使 Docker 组权限生效"
    fi
}

# 安装 Docker Compose
install_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        log_warning "Docker Compose 已安装，跳过"
        docker-compose --version
    else
        log_info "安装 Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        log_success "Docker Compose 安装完成"
        docker-compose --version
    fi
}

# 安装基础工具
install_tools() {
    log_info "安装基础工具..."
    sudo apt install -y git vim curl wget htop net-tools
    log_success "基础工具安装完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙 (UFW)..."
    
    # 检查是否已启用
    if sudo ufw status | grep -q "Status: active"; then
        log_warning "UFW 已启用，跳过配置"
    else
        sudo ufw --force enable
        sudo ufw allow 22/tcp
        sudo ufw allow 8000/tcp
        sudo ufw allow 8002/tcp
        sudo ufw allow 8003/tcp
        log_success "防火墙配置完成"
    fi
    
    sudo ufw status
}

# 配置 Docker 日志轮转
configure_docker_logging() {
    log_info "配置 Docker 日志轮转..."
    
    if [ ! -f /etc/docker/daemon.json ]; then
        sudo mkdir -p /etc/docker
        sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
        sudo systemctl restart docker
        log_success "Docker 日志轮转配置完成"
    else
        log_warning "Docker daemon.json 已存在，跳过配置"
    fi
}

# 克隆或更新项目代码
deploy_code() {
    log_info "部署项目代码..."
    
    PROJECT_DIR="$HOME/live-agent"
    
    if [ -d "$PROJECT_DIR" ]; then
        log_warning "项目目录已存在，是否要更新代码？(y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            cd "$PROJECT_DIR"
            git pull origin main || log_warning "Git pull 失败，请手动更新"
        fi
    else
        log_info "请输入 Git 仓库 URL（留空跳过）："
        read -r GIT_REPO
        
        if [ -n "$GIT_REPO" ]; then
            git clone "$GIT_REPO" "$PROJECT_DIR"
            log_success "代码克隆完成"
        else
            log_warning "未提供 Git 仓库，请手动上传代码到 $PROJECT_DIR"
            log_info "可以使用 scp 命令上传代码"
            return
        fi
    fi
    
    cd "$PROJECT_DIR/main/xiaozhi-server" || exit
}

# 配置环境变量
configure_env() {
    log_info "配置环境变量..."
    
    cd "$HOME/live-agent/main/xiaozhi-server" || exit
    
    # 检查配置文件是否存在
    if [ ! -f custom_config.yaml ]; then
        log_error "找不到 custom_config.yaml，请确保代码已正确部署"
        exit 1
    fi
    
    log_info "是否需要修改 Groq API Key？(y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "请输入您的 Groq API Key:"
        read -r GROQ_API_KEY
        
        # 更新 custom_config.yaml
        if command -v yq &> /dev/null; then
            yq -i ".LLM.GroqLLM.api_key = \"$GROQ_API_KEY\"" custom_config.yaml
            log_success "Groq API Key 已更新"
        else
            log_warning "yq 未安装，请手动修改 custom_config.yaml 中的 Groq API Key"
        fi
    fi
    
    log_success "环境配置完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    cd "$HOME/live-agent/main/xiaozhi-server" || exit
    
    # 拉取最新镜像
    log_info "拉取 Docker 镜像（可能需要几分钟）..."
    docker-compose -f docker-compose_all.yml pull
    
    # 启动服务
    log_info "启动所有服务..."
    docker-compose -f docker-compose_all.yml up -d
    
    # 等待服务启动
    log_info "等待服务启动（30秒）..."
    sleep 30
    
    # 检查服务状态
    log_info "检查服务状态..."
    docker-compose -f docker-compose_all.yml ps
    
    log_success "服务启动完成"
}

# 验证部署
verify_deployment() {
    log_info "验证部署..."
    
    # 获取公网 IP
    PUBLIC_IP=$(curl -s ifconfig.me)
    
    echo ""
    log_success "==================== 部署成功 ===================="
    echo ""
    echo "📋 服务访问信息："
    echo "  - 管理后台: http://$PUBLIC_IP:8002"
    echo "  - WebSocket: ws://$PUBLIC_IP:8000/xiaozhi/v1/"
    echo "  - 视觉接口: http://$PUBLIC_IP:8003"
    echo ""
    echo "🔑 默认登录信息："
    echo "  - 用户名: admin"
    echo "  - 密码: admin（请登录后立即修改）"
    echo ""
    echo "📊 查看日志："
    echo "  - cd ~/live-agent/main/xiaozhi-server"
    echo "  - docker-compose -f docker-compose_all.yml logs -f"
    echo ""
    echo "🔄 管理服务："
    echo "  - 停止: docker-compose -f docker-compose_all.yml down"
    echo "  - 启动: docker-compose -f docker-compose_all.yml up -d"
    echo "  - 重启: docker-compose -f docker-compose_all.yml restart"
    echo ""
    log_success "================================================="
    echo ""
}

# 创建备份脚本
create_backup_script() {
    log_info "创建自动备份脚本..."
    
    BACKUP_SCRIPT="$HOME/backup.sh"
    
    cat > "$BACKUP_SCRIPT" <<'EOF'
#!/bin/bash

BACKUP_DIR="$HOME/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
docker exec xiaozhi-esp32-server-db mysqldump -uroot -p123456 xiaozhi_esp32_server > $BACKUP_DIR/db_$DATE.sql

# 备份配置文件
tar -czf $BACKUP_DIR/config_$DATE.tar.gz $HOME/live-agent/main/xiaozhi-server/data $HOME/live-agent/main/xiaozhi-server/custom_config.yaml

# 保留最近 7 天的备份
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "config_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF
    
    chmod +x "$BACKUP_SCRIPT"
    
    log_info "是否配置每天自动备份？(y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # 添加到 crontab
        (crontab -l 2>/dev/null; echo "0 2 * * * $BACKUP_SCRIPT >> $HOME/backup.log 2>&1") | crontab -
        log_success "自动备份已配置（每天凌晨 2 点）"
    fi
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  XiaoZhi AI Agent - AWS 部署脚本"
    echo "=========================================="
    echo ""
    
    check_root
    check_os
    
    log_info "开始部署流程..."
    echo ""
    
    # 安装依赖
    update_system
    install_docker
    install_docker_compose
    install_tools
    
    # 配置系统
    configure_firewall
    configure_docker_logging
    
    # 部署代码
    deploy_code
    configure_env
    
    # 启动服务
    start_services
    
    # 创建备份
    create_backup_script
    
    # 验证部署
    verify_deployment
    
    log_success "部署流程完成！"
    
    # 检查是否需要重新登录
    if groups | grep -q docker; then
        log_info "无需重新登录，Docker 组权限已生效"
    else
        log_warning "请退出并重新登录以使 Docker 组权限生效"
        log_info "退出命令: exit"
    fi
}

# 运行主函数
main

