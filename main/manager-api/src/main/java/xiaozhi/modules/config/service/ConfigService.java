package xiaozhi.modules.config.service;

import java.util.List;
import java.util.Map;

public interface ConfigService {
    /**
     * 获取服务器配置
     * 
     * @param isCache 是否缓存
     * @return 配置信息
     */
    Object getConfig(Boolean isCache);

    /**
     * 获取智能体模型配置
     * 
     * @param macAddress     MAC地址
     * @param selectedModule 客户端已实例化的模型
     * @return 模型配置信息
     */
    Map<String, Object> getAgentModels(String macAddress, Map<String, String> selectedModule);

    /**
     * 根据智能体ID获取完整配置（内部接口，供xiaozhi-server和live-agent-api调用）
     * 
     * @param agentId 智能体ID
     * @return 配置信息，包含selected_module、LLM、TTS、ASR等所有模块配置
     */
    Map<String, Object> getAgentConfigById(String agentId);

    /**
     * 批量获取用户所有智能体配置（内部接口，用于缓存预热）
     * 
     * @param userId 用户ID
     * @return 该用户所有智能体的配置列表
     */
    List<Map<String, Object>> getUserAgentConfigs(Long userId);
}