# APP 端预热接口接入指南

## 概述

预热接口用于提前加载用户的 Agent 配置到服务端缓存，减少首次对话的冷启动延迟。

**预期效果**：首次对话配置加载时间从 ~150ms 降低到 <10ms

---

## 接口定义

### 请求

```
POST /api/live_agent/v1/internal/warmup
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | 否 | 用户 ID，预热该用户的 agents（最多 5 个） |
| `agent_ids` | string[] | 否 | 指定要预热的 Agent ID 列表 |

**注意**：`user_id` 和 `agent_ids` 至少提供一个，如果都提供则优先使用 `agent_ids`

### 请求示例

```json
// 方式 1: 按用户预热（推荐用于登录/启动时）
{
  "user_id": "user_01KFZXXXX"
}

// 方式 2: 指定 Agent 预热（推荐用于切换 Agent 时）
{
  "agent_ids": ["agent_01KG4ECQCM4H2K9V645PGZKVD0"]
}

// 方式 3: 同时指定（agent_ids 优先）
{
  "user_id": "user_01KFZXXXX",
  "agent_ids": ["agent_xxx", "agent_yyy"]
}
```

### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "warmed_agents": ["agent_xxx", "agent_yyy"],  // 成功预热的 agents
    "failed_agents": [],                           // 预热失败的 agents
    "total_time_ms": 152.63                        // 预热总耗时（毫秒）
  }
}
```

---

## 调用时机

### 1. APP 启动时（含自动登录）

```
时机：APP 启动 → 自动登录成功 → 立即调用预热
策略：
  - 如果有本地最近使用记录 → {"agent_ids": [最近使用的AgentIDs]}
  - 否则 → {"user_id": "当前登录用户ID"}
```

### 2. 用户登录成功后

```
时机：用户手动登录成功 → 立即调用预热
策略：同上（优先使用本地最近使用记录）
```

### 3. 进入对话页面时

```
时机：用户选择某个 Agent → 进入对话页面
操作：
  1. 记录本次使用到本地存储
  2. 调用预热 {"agent_ids": ["当前AgentID"]}
```

### 4. 切换 Agent 时（可选）

```
时机：用户在 Agent 列表切换选中 → 调用预热
参数：{"agent_ids": ["新选中的AgentID"]}
```

---

## 最近使用记录（推荐）

为了更精准地预热用户常用的 Agents，建议 APP 端本地记录"最近使用的 Agent"列表。

### 存储实现

```dart
import 'package:shared_preferences/shared_preferences.dart';

/// 最近使用的 Agent 记录管理
class RecentAgentsStorage {
  static const _key = 'recent_agent_ids';
  static const _maxCount = 5;  // 最多保留 5 个
  
  /// 记录 Agent 使用（每次进入对话时调用）
  Future<void> recordUsage(String agentId) async {
    final prefs = await SharedPreferences.getInstance();
    List<String> recent = prefs.getStringList(_key) ?? [];
    
    // 移除已存在的（如果有），然后插入到最前面
    recent.remove(agentId);
    recent.insert(0, agentId);
    
    // 保留最多 _maxCount 个
    if (recent.length > _maxCount) {
      recent = recent.sublist(0, _maxCount);
    }
    
    await prefs.setStringList(_key, recent);
  }
  
  /// 获取最近使用的 Agent IDs
  Future<List<String>> getRecentAgentIds() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getStringList(_key) ?? [];
  }
  
  /// 清除记录（用户登出时调用）
  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }
}
```

### 结合预热使用

```dart
final _recentStorage = RecentAgentsStorage();

/// APP 启动/登录时 - 预热最近使用的 Agents
Future<void> onAppReady(String userId) async {
  final recentIds = await _recentStorage.getRecentAgentIds();
  
  if (recentIds.isNotEmpty) {
    // 有最近使用记录，直接预热这些 agents
    warmupAgents(agentIds: recentIds);
  } else {
    // 没有记录（新用户/新设备），按用户预热
    warmupAgents(userId: userId);
  }
}

/// 进入对话时 - 记录使用 + 预热当前 Agent
Future<void> onEnterChat(Agent agent) async {
  // 1. 记录本次使用
  await _recentStorage.recordUsage(agent.id);
  
  // 2. 预热当前 agent（确保缓存最新）
  warmupAgents(agentIds: [agent.id]);
}

/// 用户登出时 - 清除记录
Future<void> onLogout() async {
  await _recentStorage.clear();
}
```

### 优势

| 特点 | 说明 |
|------|------|
| 本地存储 | 无需服务端改动，读取速度快 |
| 精准预热 | 只预热用户真正使用的 Agents |
| 离线可用 | 无网络时也能获取记录 |
| 自动更新 | 通过实际使用自动维护列表 |

---

## 实现建议

### 调用方式：异步非阻塞

预热接口应**异步调用**，不阻塞 UI 流程：

```dart
// Flutter 示例
Future<void> warmupAgents({String? userId, List<String>? agentIds}) async {
  try {
    // 异步调用，不 await
    _api.post('/internal/warmup', data: {
      if (userId != null) 'user_id': userId,
      if (agentIds != null) 'agent_ids': agentIds,
    });
  } catch (e) {
    // 预热失败不影响正常流程，仅记录日志
    debugPrint('Warmup failed: $e');
  }
}

// 登录成功后调用
void onLoginSuccess(User user) {
  warmupAgents(userId: user.id);  // 不 await
  navigateToHome();
}

// 选择 Agent 时调用
void onAgentSelected(Agent agent) {
  warmupAgents(agentIds: [agent.id]);  // 不 await
  navigateToChat(agent);
}
```

### 防重复调用

建议 APP 端实现简单的防抖/去重逻辑：

```dart
class WarmupManager {
  final Set<String> _warmedAgents = {};
  DateTime? _lastUserWarmup;
  
  Future<void> warmupUser(String userId) async {
    // 同一用户 5 分钟内不重复预热
    if (_lastUserWarmup != null && 
        DateTime.now().difference(_lastUserWarmup!) < Duration(minutes: 5)) {
      return;
    }
    _lastUserWarmup = DateTime.now();
    await _callWarmupApi(userId: userId);
  }
  
  Future<void> warmupAgent(String agentId) async {
    // 已预热的 agent 不重复预热
    if (_warmedAgents.contains(agentId)) return;
    _warmedAgents.add(agentId);
    await _callWarmupApi(agentIds: [agentId]);
  }
}
```

### 错误处理

预热失败不应影响用户正常使用：

```dart
try {
  await warmupAgents(userId: userId);
} catch (e) {
  // 静默失败，记录日志即可
  // 后续对话会正常从数据库加载配置（稍慢但可用）
}
```

---

## 缓存有效期

| 缓存层 | 有效期 | 说明 |
|--------|--------|------|
| L1（服务端内存） | 30 秒 | 极速访问，自动过期 |
| L2（Redis） | 10 分钟 | 预热写入的缓存 |

**建议**：如果用户超过 10 分钟未进行对话，在下次对话前再次调用预热。

---

## 缓存失效机制

服务端已实现主动缓存失效，**无需 APP 端额外处理**，配置修改**立即生效**。

### 触发时机

| 操作 | 缓存失效 | 说明 |
|------|---------|------|
| 修改 Agent 配置 | ✅ 自动 | 更新后立即清除 L1 + L2 缓存 |
| 删除 Agent | ✅ 自动 | 删除前清除 L1 + L2 缓存 |

### 实现原理（双层缓存同步失效）

```
用户修改 Agent 配置
    ↓
live-agent-api 更新数据库
    ↓
┌─────────────────────────────────────────┐
│ 1. 删除 Redis 缓存 (L2)                  │
│    pattern: xiaozhi::agent_config:{id}:* │
├─────────────────────────────────────────┤
│ 2. 发布 Redis Pub/Sub 通知               │
│    channel: cache:invalidate             │
│    message: {"type":"agent_config",      │
│              "key":"agent_id"}           │
└─────────────────────────────────────────┘
    ↓
xiaozhi-server 收到 Pub/Sub 通知
    ↓
清除 L1 本地内存缓存
    ↓
下次对话获取最新配置（延迟: 0）
```

### 服务端日志

```
# live-agent-api 日志
[Cache Invalidation] Deleted 1 Redis cache keys for agent agent_xxx
[Cache Invalidation] Published: type=agent_config, key=agent_xxx

# xiaozhi-server 日志
[Redis Pub/Sub] Received invalidation: type=agent_config, key=agent_xxx
[L1缓存] 收到失效通知，清除 1 条 agent_config 缓存: agent_xxx
```

### 技术细节

| 层级 | 失效方式 | 延迟 |
|------|---------|------|
| L2 Redis | 直接删除 key | 0ms |
| L1 本地内存 | Redis Pub/Sub 通知 | <10ms |

---

## 测试验证

### 验证预热成功

1. 调用预热接口，确认返回 `warmed_agents` 非空
2. 立即发起对话，观察服务端日志中配置加载时间应为 `0.00 秒`

### 服务端日志示例

```
# 预热成功后的对话日志
INFO - 0.00 秒，根据 agent_id=agent_xxx 获取配置成功: {...}
```

---

## FAQ

**Q: 预热接口调用失败会怎样？**  
A: 对话仍可正常进行，只是首次配置加载会稍慢（~100-200ms）。

**Q: 需要传递认证 Token 吗？**  
A: 当前为内部接口，无需认证。如需增加安全性可后续添加。

**Q: 预热后修改了 Agent 配置怎么办？**  
A: 服务端已实现主动缓存失效机制，Agent 配置修改后会自动清除相关缓存，下次对话会获取最新配置。

---

## 接口地址

| 环境 | 地址 |
|------|------|
| 生产 | `https://your-domain/api/live_agent/v1/internal/warmup` |
| 开发 | `http://54.218.11.250:8080/api/live_agent/v1/internal/warmup` |
