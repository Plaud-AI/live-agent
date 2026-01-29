import os
import re
import yaml
from collections.abc import Mapping
from config.manage_api_client import init_service, get_server_config, get_agent_models


def get_project_dir():
    """获取项目根目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"


def resolve_env_vars(obj):
    """
    递归解析配置中的 ${env:VAR_NAME} 语法，替换为环境变量值
    
    支持格式:
    - ${env:VAR_NAME} -> 环境变量值，未设置则返回空字符串
    - ${env:VAR_NAME|default} -> 环境变量值，未设置则返回 default
    """
    if isinstance(obj, str):
        # 匹配 ${env:VAR_NAME} 或 ${env:VAR_NAME|default}
        pattern = r'\$\{env:([^}|]+)(?:\|([^}]*))?\}'
        
        def replace_env(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            return os.environ.get(var_name, default_value)
        
        return re.sub(pattern, replace_env, obj)
    elif isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_env_vars(item) for item in obj]
    else:
        return obj


def read_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    # 解析环境变量
    config = resolve_env_vars(config)
    return config


def load_config():
    """加载配置文件"""
    from core.utils.cache.manager import cache_manager, CacheType

    # 检查缓存
    cached_config = cache_manager.get(CacheType.CONFIG, "main_config")
    if cached_config is not None:
        return cached_config

    default_config_path = get_project_dir() + "config.yaml"
    custom_config_path = get_project_dir() + "data/.config.yaml"

    # 加载默认配置
    default_config = read_config(default_config_path)
    custom_config = read_config(custom_config_path)

    if custom_config.get("manager-api", {}).get("url"):
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，使用异步版本
            config = asyncio.run_coroutine_threadsafe(
                get_config_from_api_async(custom_config), loop
            ).result()
        except RuntimeError:
            # 如果不在事件循环中（启动时），创建新的事件循环
            config = asyncio.run(get_config_from_api_async(custom_config))
    else:
        # 合并配置
        config = merge_configs(default_config, custom_config)
    # 初始化目录
    ensure_directories(config)

    # 缓存配置
    cache_manager.set(CacheType.CONFIG, "main_config", config)
    return config


async def get_config_from_api_async(config):
    """从Java API获取配置（异步版本）"""
    # 初始化API客户端
    init_service(config)
    # 注意: live_agent_api_client 在 connection.py 中按需初始化，避免循环导入

    # 获取服务器配置
    config_data = await get_server_config()
    if config_data is None:
        raise Exception("Failed to fetch server config from API")

    # 先加载本地默认配置 (config.yaml)，作为基础配置
    # manager-api 只返回部分配置（如 ASR, VAD），TTS/LLM 等需要从本地配置获取
    default_config_path = get_project_dir() + "config.yaml"
    default_config = read_config(default_config_path)
    
    # 将 manager-api 配置合并到默认配置上（API 配置优先）
    merged_config = merge_configs(default_config, config_data)
    
    merged_config["read_config_from_api"] = True
    merged_config["manager-api"] = {
        "url": config["manager-api"].get("url", ""),
        "secret": config["manager-api"].get("secret", ""),
    }
    # server的配置以本地为准（包括 auth 配置）
    # 本地 auth 配置优先，如果本地没有配置则使用 manager-api 的配置
    local_auth = config.get("server", {}).get("auth", {})
    api_auth = merged_config.get("server", {}).get("auth", {})
    # 合并 auth 配置：本地优先
    merged_auth = {**api_auth, **local_auth}
    
    if config.get("server"):
        merged_config["server"] = {
            "ip": config["server"].get("ip", ""),
            "port": config["server"].get("port", ""),
            "http_port": config["server"].get("http_port", ""),
            "vision_explain": config["server"].get("vision_explain", ""),
            "auth_key": config["server"].get("auth_key", ""),
        }
    merged_config["server"]["auth"] = merged_auth
    # 如果服务器没有prompt_template，则从本地配置读取
    if not merged_config.get("prompt_template"):
        merged_config["prompt_template"] = config.get("prompt_template")
    
    # 解析环境变量（API 返回的配置可能包含 ${env:VAR_NAME} 语法）
    merged_config = resolve_env_vars(merged_config)
    
    return merged_config


async def get_private_config_from_api(config, device_id, client_id):
    """从Java API获取私有配置"""
    return await get_agent_models(device_id, client_id, config["selected_module"])


def ensure_directories(config):
    """确保所有配置路径存在"""
    dirs_to_create = set()
    project_dir = get_project_dir()  # 获取项目根目录
    # 日志文件目录
    log_dir = config.get("log", {}).get("log_dir", "tmp")
    dirs_to_create.add(os.path.join(project_dir, log_dir))

    # ASR/TTS模块输出目录
    for module in ["ASR", "TTS"]:
        if config.get(module) is None:
            continue
        for provider in config.get(module, {}).values():
            output_dir = provider.get("output_dir", "")
            if output_dir:
                dirs_to_create.add(output_dir)

    # 根据selected_module创建模型目录
    selected_modules = config.get("selected_module", {})
    for module_type in ["ASR", "LLM", "TTS"]:
        selected_provider = selected_modules.get(module_type)
        if not selected_provider:
            continue
        if config.get(module) is None:
            continue
        if config.get(selected_provider) is None:
            continue
        provider_config = config.get(module_type, {}).get(selected_provider, {})
        output_dir = provider_config.get("output_dir")
        if output_dir:
            full_model_dir = os.path.join(project_dir, output_dir)
            dirs_to_create.add(full_model_dir)

    # 统一创建目录（保留原data目录创建）
    for dir_path in dirs_to_create:
        try:
            os.makedirs(dir_path, exist_ok=True)
        except PermissionError:
            print(f"警告：无法创建目录 {dir_path}，请检查写入权限")


def merge_configs(default_config, custom_config):
    """
    递归合并配置，custom_config优先级更高

    Args:
        default_config: 默认配置
        custom_config: 用户自定义配置

    Returns:
        合并后的配置
    """
    if not isinstance(default_config, Mapping) or not isinstance(
        custom_config, Mapping
    ):
        return custom_config

    merged = dict(default_config)

    for key, value in custom_config.items():
        if (
            key in merged
            and isinstance(merged[key], Mapping)
            and isinstance(value, Mapping)
        ):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value

    return merged
