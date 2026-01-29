"""
GIF 表情管理器模块
负责加载和管理 GIF 表情配置
"""

import os
import yaml
from typing import Dict, List, Optional
from config.logger import setup_logging

TAG = __name__


class ExpressionManager:
    """GIF 表情管理器（单例模式）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.logger = setup_logging()
        self.expressions: Dict[str, dict] = {}
        self.categories: Dict[str, dict] = {}
        self.default_expression = "平静"
        self.base_path = "emo-gif/gifs"
        self._load_config()

    def _load_config(self):
        """加载表情配置"""
        # 尝试多个可能的配置文件路径
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "../../config/expressions.yaml"),
            os.path.join(os.path.dirname(__file__), "../../../config/expressions.yaml"),
            "config/expressions.yaml",
            "main/xiaozhi-server/config/expressions.yaml",
        ]

        config_path = None
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                config_path = abs_path
                break

        if not config_path:
            self.logger.bind(tag=TAG).warning("未找到表情配置文件 expressions.yaml")
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            self.default_expression = config.get("default_expression", "平静")
            self.base_path = config.get("paths", {}).get("base_path", "emo-gif/gifs")
            self.categories = config.get("categories", {})
            self.expressions = config.get("expressions", {})

            self.logger.bind(tag=TAG).info(
                f"加载表情配置成功: {len(self.expressions)} 个表情, "
                f"{len(self.categories)} 个大分类"
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"加载表情配置失败: {e}")

    def is_valid_expression(self, expression_name: str) -> bool:
        """检查表情名称是否有效"""
        return expression_name in self.expressions

    def get_expression_info(self, expression_name: str) -> Optional[dict]:
        """获取表情信息"""
        return self.expressions.get(expression_name)

    def get_expression_file_path(self, expression_name: str) -> Optional[str]:
        """获取表情文件的相对路径"""
        info = self.get_expression_info(expression_name)
        if info:
            return f"{info.get('dir', 'gif')}/{info.get('file', f'{expression_name}.gif')}"
        return None

    def get_all_expression_names(self) -> List[str]:
        """获取所有表情名称列表"""
        return list(self.expressions.keys())

    def get_expressions_by_category(self, main_category: str, sub_category: str = None) -> List[str]:
        """获取分类下的所有表情名称"""
        if main_category not in self.categories:
            return []
        
        category_data = self.categories[main_category]
        if sub_category:
            return category_data.get(sub_category, [])
        
        # 返回该大分类下所有表情
        all_expressions = []
        for sub_cat, expressions in category_data.items():
            all_expressions.extend(expressions)
        return all_expressions

    def get_expression_list_for_prompt(self) -> str:
        """
        生成用于 prompt 的表情列表描述
        按分类组织，便于 LLM 理解和选择
        """
        result = []
        
        for main_cat, sub_cats in self.categories.items():
            result.append(f"\n  【{main_cat}类】")
            for sub_cat, expressions in sub_cats.items():
                # 每个子分类显示所有表情
                expr_str = "、".join(expressions)
                result.append(f"    - {sub_cat}: {expr_str}")
        
        return "\n".join(result)

    def get_simple_expression_list(self) -> str:
        """
        生成简化的表情列表（仅表情名，逗号分隔）
        用于 prompt 中快速参考
        """
        # 按使用频率排序的常用表情
        common_expressions = [
            # 基础情绪
            "开心", "傻笑", "满足", "小骄傲",
            "悲伤", "失望", "叹气", "大哭",
            "生气", "烦躁", "炸毛",
            "惊讶", "好奇", "吐",
            "害怕", "紧张", "担忧",
            "害羞", "尴尬",
            "困惑", "怀疑", "晕",
            "思考中", "严肃", "坚定",
            "平静", "禅意", "轻微呼吸",
            "困倦", "打哈欠", "困",
            "爱心浮现", "亲吻", "感激",
            "冷漠", "无聊", "直视",
            # 动作
            "用力点头", "摇头(说不)", "挥手", "拍手",
            # 常用活动
            "听音乐", "阅读", "敲代码",
        ]
        return "、".join(common_expressions)


# 全局单例
expression_manager = ExpressionManager()


