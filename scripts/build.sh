#!/bin/bash
# =============================================================================
# 智能构建脚本 - 支持通过 commit message 控制缓存行为
# =============================================================================
#
# 使用方法：
#   在 commit message 中添加以下标记：
#   - [no-cache]    : 强制重新构建所有服务
#   - [rebuild]     : 同上，强制重新构建
#   - [force-build] : 同上，强制重新构建
#
# 示例：
#   git commit -m "feat: 添加新功能 [no-cache]"
#   git commit -m "[rebuild] fix: 修复紧急问题"
#
# =============================================================================

set -e

# 获取最新 commit message
COMMIT_MSG=$(git log -1 --pretty=%B 2>/dev/null || echo "")
COMMIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo "=================================================="
echo "构建信息"
echo "=================================================="
echo "Commit: $COMMIT_HASH"
echo "Message: $COMMIT_MSG"
echo ""

# 检查是否需要跳过缓存
NO_CACHE=""
if echo "$COMMIT_MSG" | grep -qiE '\[(no-?cache|rebuild|force-?build)\]'; then
    echo "🔄 检测到强制构建标记，将跳过 Docker 缓存"
    NO_CACHE="--no-cache"
    
    # 清理 Docker 构建缓存
    echo "清理 Docker 构建缓存..."
    docker builder prune -f 2>/dev/null || true
else
    echo "📦 使用 Docker 缓存（如需强制重建，请在 commit message 中添加 [no-cache]）"
fi
echo ""

# 设置构建参数
export GIT_COMMIT="$COMMIT_HASH"

echo "=================================================="
echo "开始构建"
echo "=================================================="

# 执行构建
docker-compose -f docker-compose.dokploy.yml build $NO_CACHE

echo ""
echo "=================================================="
echo "✅ 构建完成"
echo "=================================================="
