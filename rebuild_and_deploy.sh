#!/bin/bash
#
# 快速重新构建和部署 manager-api 服务
#

set -e

cd "$(dirname "$0")/main/manager-api"

echo "=== 1. 编译项目（跳过测试） ==="
mvn clean package -DskipTests

echo ""
echo "=== 2. 检查编译结果 ==="
if [ ! -f "target/xiaozhi-esp32-api.jar" ]; then
    echo "错误：编译失败，未找到 jar 文件"
    exit 1
fi

echo ""
echo "=== 3. 停止容器 ==="
docker stop xiaozhi-esp32-server-web || true

echo ""
echo "=== 4. 替换 jar 包 ==="
docker cp target/xiaozhi-esp32-api.jar xiaozhi-esp32-server-web:/app/xiaozhi-esp32-api.jar

echo ""
echo "=== 5. 启动容器 ==="
docker start xiaozhi-esp32-server-web

echo ""
echo "=== 6. 等待服务启动 ==="
sleep 30

echo ""
echo "=== 7. 检查服务状态 ==="
docker logs xiaozhi-esp32-server-web --tail 10

echo ""
echo "✅ 部署完成！"
echo "现在可以使用用户名和密码登录，无需验证码"
echo ""
echo "测试命令："
echo 'curl -X POST http://localhost:8002/xiaozhi/user/login -H "Content-Type: application/json" -d '"'"'{"username":"admin","password":"admin"}'"'"''

