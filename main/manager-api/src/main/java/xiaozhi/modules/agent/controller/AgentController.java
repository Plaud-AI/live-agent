package xiaozhi.modules.agent.controller;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.apache.commons.lang3.StringUtils;
import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.Parameters;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.AllArgsConstructor;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.page.PageData;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.user.UserDetail;
import xiaozhi.common.utils.AuthTokenUtil;
import xiaozhi.common.utils.Result;
import xiaozhi.common.utils.ResultUtils;
import xiaozhi.modules.agent.dto.AgentChatHistoryDTO;
import xiaozhi.modules.agent.dto.AgentChatSessionDTO;
import xiaozhi.modules.agent.dto.AgentCreateDTO;
import xiaozhi.modules.agent.dto.AgentDTO;
import xiaozhi.modules.agent.dto.AgentMemoryDTO;
import xiaozhi.modules.agent.dto.AgentUpdateDTO;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.agent.entity.AgentTemplateEntity;
import xiaozhi.modules.agent.service.AgentChatAudioService;
import xiaozhi.modules.agent.service.AgentChatHistoryService;
import xiaozhi.modules.agent.service.AgentPluginMappingService;
import xiaozhi.modules.agent.service.AgentService;
import xiaozhi.modules.agent.service.AgentTemplateService;
import xiaozhi.modules.agent.vo.AgentChatHistoryUserVO;
import xiaozhi.modules.agent.vo.AgentInfoVO;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.service.DeviceService;
import xiaozhi.modules.security.user.SecurityUser;
import xiaozhi.modules.sys.service.SysParamsService;

@Tag(name = "智能体管理")
@AllArgsConstructor
@RestController
@RequestMapping("/agent")
public class AgentController {
    private final AgentService agentService;
    private final AgentTemplateService agentTemplateService;
    private final DeviceService deviceService;
    private final AgentChatHistoryService agentChatHistoryService;
    private final AgentChatAudioService agentChatAudioService;
    private final AgentPluginMappingService agentPluginMappingService;
    private final RedisUtils redisUtils;
    private final SysParamsService sysParamsService;

    @GetMapping("/list")
    @Operation(summary = "获取用户智能体列表")
    @RequiresPermissions("sys:role:normal")
    public Result<List<AgentDTO>> getUserAgents() {
        UserDetail user = SecurityUser.getUser();
        List<AgentDTO> agents = agentService.getUserAgents(user.getId());
        return new Result<List<AgentDTO>>().ok(agents);
    }

    @GetMapping("/all")
    @Operation(summary = "智能体列表（管理员）")
    @RequiresPermissions("sys:role:superAdmin")
    @Parameters({
            @Parameter(name = Constant.PAGE, description = "当前页码，从1开始", required = true),
            @Parameter(name = Constant.LIMIT, description = "每页显示记录数", required = true),
    })
    public Result<PageData<AgentEntity>> adminAgentList(
            @Parameter(hidden = true) @RequestParam Map<String, Object> params) {
        PageData<AgentEntity> page = agentService.adminAgentList(params);
        return new Result<PageData<AgentEntity>>().ok(page);
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取智能体详情")
    @RequiresPermissions("sys:role:normal")
    public Result<AgentInfoVO> getAgentById(@PathVariable("id") String id) {
        AgentInfoVO agent = agentService.getAgentById(id);
        return ResultUtils.success(agent);
    }

    @PostMapping
    @Operation(summary = "创建智能体")
    @RequiresPermissions("sys:role:normal")
    public Result<String> save(@RequestBody @Valid AgentCreateDTO dto) {
        String agentId = agentService.createAgent(dto);
        return new Result<String>().ok(agentId);
    }

    @PutMapping("/saveMemory/{macAddress}")
    @Operation(summary = "根据设备id更新智能体")
    public Result<Void> updateByDeviceId(@PathVariable String macAddress, @RequestBody @Valid AgentMemoryDTO dto) {
        DeviceEntity device = deviceService.getDeviceByMacAddress(macAddress);
        if (device == null) {
            return new Result<>();
        }
        AgentUpdateDTO agentUpdateDTO = new AgentUpdateDTO();
        agentUpdateDTO.setSummaryMemory(dto.getSummaryMemory());
        agentService.updateAgentById(device.getAgentId(), agentUpdateDTO);
        return new Result<>();
    }

    @PutMapping("/{id}")
    @Operation(summary = "更新智能体")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> update(@PathVariable String id, @RequestBody @Valid AgentUpdateDTO dto) {
        agentService.updateAgentById(id, dto);
        return new Result<>();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除智能体")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> delete(@PathVariable String id) {
        // 先删除关联的设备
        deviceService.deleteByAgentId(id);
        // 删除关联的聊天记录
        agentChatHistoryService.deleteByAgentId(id, true, true);
        // 删除关联的插件
        agentPluginMappingService.deleteByAgentId(id);
        // 再删除智能体
        agentService.deleteById(id);
        return new Result<>();
    }

    @GetMapping("/template")
    @Operation(summary = "智能体模板模板列表")
    @RequiresPermissions("sys:role:normal")
    public Result<List<AgentTemplateEntity>> templateList() {
        List<AgentTemplateEntity> list = agentTemplateService
                .list(new QueryWrapper<AgentTemplateEntity>().orderByAsc("sort"));
        return new Result<List<AgentTemplateEntity>>().ok(list);
    }

    @GetMapping("/{id}/sessions")
    @Operation(summary = "获取智能体会话列表")
    @RequiresPermissions("sys:role:normal")
    @Parameters({
            @Parameter(name = Constant.PAGE, description = "当前页码，从1开始", required = true),
            @Parameter(name = Constant.LIMIT, description = "每页显示记录数", required = true),
    })
    public Result<PageData<AgentChatSessionDTO>> getAgentSessions(
            @PathVariable("id") String id,
            @Parameter(hidden = true) @RequestParam Map<String, Object> params) {
        params.put("agentId", id);
        PageData<AgentChatSessionDTO> page = agentChatHistoryService.getSessionListByAgentId(params);
        return new Result<PageData<AgentChatSessionDTO>>().ok(page);
    }

    @GetMapping("/{id}/chat-history/{sessionId}")
    @Operation(summary = "获取智能体聊天记录")
    @RequiresPermissions("sys:role:normal")
    public Result<List<AgentChatHistoryDTO>> getAgentChatHistory(
            @PathVariable("id") String id,
            @PathVariable("sessionId") String sessionId) {
        // 获取当前用户
        UserDetail user = SecurityUser.getUser();

        // 检查权限
        if (!agentService.checkAgentPermission(id, user.getId())) {
            return new Result<List<AgentChatHistoryDTO>>().error("没有权限查看该智能体的聊天记录");
        }

        // 查询聊天记录
        List<AgentChatHistoryDTO> result = agentChatHistoryService.getChatHistoryBySessionId(id, sessionId);
        return new Result<List<AgentChatHistoryDTO>>().ok(result);
    }
    @GetMapping("/{id}/chat-history/user")
    @Operation(summary = "获取智能体聊天记录（用户）")
    @RequiresPermissions("sys:role:normal")
    public Result<List<AgentChatHistoryUserVO>> getRecentlyFiftyByAgentId(
            @PathVariable("id") String id) {
        // 获取当前用户
        UserDetail user = SecurityUser.getUser();

        // 检查权限
        if (!agentService.checkAgentPermission(id, user.getId())) {
            return new Result<List<AgentChatHistoryUserVO>>().error("没有权限查看该智能体的聊天记录");
        }

        // 查询聊天记录
        List<AgentChatHistoryUserVO> data = agentChatHistoryService.getRecentlyFiftyByAgentId(id);
        return new Result<List<AgentChatHistoryUserVO>>().ok(data);
    }

    @GetMapping("/{id}/chat-history/audio")
    @Operation(summary = "获取音频内容")
    @RequiresPermissions("sys:role:normal")
    public Result<String> getContentByAudioId(
            @PathVariable("id") String id) {
        // 查询聊天记录
        String data = agentChatHistoryService.getContentByAudioId(id);
        return new Result<String>().ok(data);
    }

    @PostMapping("/audio/{audioId}")
    @Operation(summary = "获取音频下载ID")
    @RequiresPermissions("sys:role:normal")
    public Result<String> getAudioId(@PathVariable("audioId") String audioId) {
        byte[] audioData = agentChatAudioService.getAudio(audioId);
        if (audioData == null) {
            return new Result<String>().error("音频不存在");
        }
        String uuid = UUID.randomUUID().toString();
        redisUtils.set(RedisKeys.getAgentAudioIdKey(uuid), audioId);
        return new Result<String>().ok(uuid);
    }

    @GetMapping("/play/{uuid}")
    @Operation(summary = "播放音频")
    public ResponseEntity<byte[]> playAudio(@PathVariable("uuid") String uuid) {

        String audioId = (String) redisUtils.get(RedisKeys.getAgentAudioIdKey(uuid));
        if (StringUtils.isBlank(audioId)) {
            return ResponseEntity.notFound().build();
        }

        byte[] audioData = agentChatAudioService.getAudio(audioId);
        if (audioData == null) {
            return ResponseEntity.notFound().build();
        }
        redisUtils.delete(RedisKeys.getAgentAudioIdKey(uuid));
        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"play.wav\"")
                .body(audioData);
    }

    @PostMapping("/{agentId}/memory")
    @Operation(summary = "查询智能体记忆")
    @RequiresPermissions("sys:role:normal")
    public Result<Map<String, Object>> getAgentMemory(
            @PathVariable("agentId") String agentId,
            @RequestBody(required = false) Map<String, Object> requestBody) {
        
        // 1. 获取当前用户
        UserDetail user = SecurityUser.getUser();
        
        // 2. 验证 Agent 权限
        if (!agentService.checkAgentPermission(agentId, user.getId())) {
            return new Result<Map<String, Object>>().error("没有权限查看该智能体的记忆");
        }
        
        // 3. 获取 Agent 信息
        AgentInfoVO agent = agentService.getAgentById(agentId);
        if (agent == null) {
            return new Result<Map<String, Object>>().error("智能体不存在");
        }
        
        // 4. 获取记忆模型类型
        String memModelId = agent.getMemModelId();
        
        // 5. 根据记忆类型处理
        if ("Memory_mem_local_short".equals(memModelId)) {
            // 本地记忆：直接从数据库返回
            Map<String, Object> result = new HashMap<>();
            result.put("memory_type", memModelId);
            result.put("summary_memory", agent.getSummaryMemory());
            return new Result<Map<String, Object>>().ok(result);
            
        } else if ("Memory_mem0ai".equals(memModelId)) {
            // mem0ai 云端记忆：调用 Python 服务查询
            try {
                // 5.1 获取设备ID（使用 Agent 绑定的第一个设备）
                List<DeviceEntity> devices = deviceService.getUserDevices(user.getId(), agentId);
                if (devices.isEmpty()) {
                    return new Result<Map<String, Object>>().error("该智能体尚未绑定设备");
                }
                String deviceId = devices.get(0).getMacAddress();
                
                // 5.2 生成 JWT token（用于调用 Python API）
                String authKey = sysParamsService.getValue("server.auth_key", false);
                if (StringUtils.isBlank(authKey)) {
                    authKey = sysParamsService.getValue("server.secret", true);
                }
                if (StringUtils.isBlank(authKey)) {
                    return new Result<Map<String, Object>>().error("服务器配置错误：缺少 auth_key");
                }
                
                AuthTokenUtil authTokenUtil = new AuthTokenUtil(authKey);
                String jwtToken = authTokenUtil.generateToken(deviceId);
                
                // 5.3 调用 Python Memory API
                String pythonServiceUrl = sysParamsService.getValue("server.python_url", false);
                if (StringUtils.isBlank(pythonServiceUrl)) {
                    // 默认使用容器内网络
                    pythonServiceUrl = "http://xiaozhi-esp32-server:8003";
                }
                
                String memoryApiUrl = pythonServiceUrl + "/api/memory";
                
                // 构建请求头
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.APPLICATION_JSON);
                headers.set("Authorization", "Bearer " + jwtToken);
                headers.set("Device-Id", deviceId);
                headers.set("Client-Id", user.getId().toString());
                
                // 构建请求体
                Map<String, Object> requestPayload = new HashMap<>();
                if (requestBody != null) {
                    requestPayload.put("query", requestBody.getOrDefault("query", "user information, preferences, background"));
                    requestPayload.put("limit", requestBody.getOrDefault("limit", 10));
                } else {
                    requestPayload.put("query", "user information, preferences, background");
                    requestPayload.put("limit", 10);
                }
                
                HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestPayload, headers);
                
                // 发送请求
                RestTemplate restTemplate = new RestTemplate();
                ResponseEntity<Map> response = restTemplate.exchange(
                    memoryApiUrl,
                    HttpMethod.POST,
                    entity,
                    Map.class
                );
                
                // 返回结果
                if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                    Map<String, Object> responseBody = response.getBody();
                    if (Boolean.TRUE.equals(responseBody.get("success"))) {
                        return new Result<Map<String, Object>>().ok((Map<String, Object>) responseBody.get("data"));
                    } else {
                        String errorMsg = responseBody.getOrDefault("error", "未知错误").toString();
                        return new Result<Map<String, Object>>().error("查询记忆失败: " + errorMsg);
                    }
                } else {
                    return new Result<Map<String, Object>>().error("调用 Python 服务失败");
                }
                
            } catch (Exception e) {
                return new Result<Map<String, Object>>().error("查询记忆异常: " + e.getMessage());
            }
            
        } else {
            // 无记忆或其他类型
            Map<String, Object> result = new HashMap<>();
            result.put("memory_type", memModelId);
            result.put("message", "该智能体未配置记忆模块");
            return new Result<Map<String, Object>>().ok(result);
        }
    }

}