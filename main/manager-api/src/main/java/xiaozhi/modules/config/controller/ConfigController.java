package xiaozhi.modules.config.controller;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.AllArgsConstructor;
import xiaozhi.common.utils.Result;
import xiaozhi.common.validator.ValidatorUtils;
import xiaozhi.modules.config.dto.AgentModelsDTO;
import xiaozhi.modules.config.service.ConfigService;

/**
 * xiaozhi-server 配置获取
 *
 * @since 1.0.0
 */
@RestController
@RequestMapping("config")
@Tag(name = "参数管理")
@AllArgsConstructor
public class ConfigController {
    private final ConfigService configService;

    @PostMapping("server-base")
    @Operation(summary = "服务端获取配置接口")
    public Result<Object> getConfig() {
        Object config = configService.getConfig(true);
        return new Result<Object>().ok(config);
    }

    @PostMapping("agent-models")
    @Operation(summary = "获取智能体模型")
    public Result<Object> getAgentModels(@Valid @RequestBody AgentModelsDTO dto) {
        // 效验数据
        ValidatorUtils.validateEntity(dto);
        Object models = configService.getAgentModels(dto.getMacAddress(), dto.getSelectedModule());
        return new Result<Object>().ok(models);
    }

    @GetMapping("internal/agent/{agentId}/config")
    @Operation(summary = "内部接口：根据智能体ID获取完整配置（供xiaozhi-server和live-agent-api调用）")
    public Result<Map<String, Object>> getAgentConfig(@PathVariable("agentId") String agentId) {
        Map<String, Object> config = configService.getAgentConfigById(agentId);
        return new Result<Map<String, Object>>().ok(config);
    }

    @GetMapping("internal/user/{userId}/agents")
    @Operation(summary = "内部接口：批量获取用户所有智能体配置（用于缓存预热）")
    public Result<java.util.List<Map<String, Object>>> getUserAgentConfigs(@PathVariable("userId") Long userId) {
        java.util.List<Map<String, Object>> configs = configService.getUserAgentConfigs(userId);
        return new Result<java.util.List<Map<String, Object>>>().ok(configs);
    }
}
