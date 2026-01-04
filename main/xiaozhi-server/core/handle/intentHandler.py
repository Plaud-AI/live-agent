import re
import json
import uuid
import asyncio
from core.utils.dialogue import Message
from core.providers.tts.dto.dto import ContentType
from core.handle.helloHandle import checkWakeupWords
from plugins_func.register import Action, ActionResponse
from core.handle.sendAudioHandle import send_stt_message
from core.utils.util import remove_punctuation_and_length
from core.providers.tts.dto.dto import TTSMessageDTO, SentenceType

TAG = __name__

# ==================== 退出意图词表 ====================
# 设计原则：多层匹配，覆盖中英文自然语言中各种退出表达

# 告别语 + 结束意图词表（精确匹配，忽略大小写在匹配时处理）
EXIT_PHRASES = frozenset({
    # ========== 中文 ==========
    # 告别语
    "再见", "拜拜", "回头见", "下次见", "改天见", "有空再聊",
    "晚安", "早安",
    "走了", "先走了", "我走了", "我先走了",
    # 结束意图
    "不聊了", "不想聊了", "不想说了", "不说了",
    "聊完了", "说完了", "没事了", "好了",
    "结束", "结束对话", "结束聊天",
    # 退下/离开
    "退下", "退下吧", "下去吧",
    
    # ========== 英文 ==========
    # Goodbye phrases
    "bye", "goodbye", "good bye", "bye bye", "byebye",
    "see you", "see ya", "see you later", "see you soon",
    "later", "catch you later", "talk to you later",
    "take care", "have a good one", "have a nice day",
    "good night", "goodnight", "night", "nite",
    "good morning", "good evening",
    "farewell", "so long", "peace", "peace out",
    "gotta go", "got to go", "i gotta go", "i got to go",
    "im out", "i am out", "im leaving", "i am leaving",
    # End conversation intent
    "stop", "end", "quit", "exit", "close",
    "done", "im done", "i am done", "all done",
    "thats all", "that is all", "thats it", "that is it",
    "no more", "nothing else", "nothing more",
    "stop talking", "stop chatting",
    "end conversation", "end chat", "end session",
    "close conversation", "close chat", "close session",
    "disconnect", "shut down", "shutdown",
    # Dismissal
    "leave", "go away", "leave me alone",
    "enough", "thats enough", "that is enough",
    "im good", "i am good", "all good",
    "thank you bye", "thanks bye", "ok bye", "okay bye",
})

# 核心退出关键词（用于后缀匹配）
EXIT_CORE_KEYWORDS = (
    # 中文
    "退出", "关闭", "退下", "关机", "断开",
    # 英文
    "exit", "quit", "close", "stop", "end", "bye", "disconnect",
)

# 正则模式（用于复杂表达，启动时预编译）
EXIT_PATTERNS = [
    # 中文模式
    re.compile(r"不想.{0,3}聊"),          # "不想和你聊了"
    re.compile(r"不.{0,3}说话"),          # "不想说话了"
    re.compile(r"我要.{0,2}走"),          # "我要走了"
    # 英文模式 (case insensitive)
    re.compile(r"i\s*(don.?t|do not)\s*want\s*to\s*(talk|chat)", re.IGNORECASE),  # "I don't want to talk"
    re.compile(r"stop\s*(talking|chatting)", re.IGNORECASE),                       # "stop talking"
    re.compile(r"(end|close|quit)\s*(this|the)?\s*(conversation|chat|session)?", re.IGNORECASE),  # "end this conversation"
    re.compile(r"(i.?m|i am)\s*(done|leaving|going|out)", re.IGNORECASE),         # "I'm done", "I'm leaving"
    re.compile(r"(gotta|got to|have to|need to)\s*(go|leave)", re.IGNORECASE),    # "gotta go", "have to leave"
]


async def handle_user_intent(conn, text):
    # 预处理输入文本，处理可能的JSON格式
    try:
        if text.strip().startswith('{') and text.strip().endswith('}'):
            parsed_data = json.loads(text)
            if isinstance(parsed_data, dict) and "content" in parsed_data:
                text = parsed_data["content"]  # 提取content用于意图分析
                conn.current_speaker = parsed_data.get("speaker")  # 保留说话人信息
    except (json.JSONDecodeError, TypeError):
        pass

    # 检查是否有明确的退出命令
    _, filtered_text = remove_punctuation_and_length(text)
    if await check_direct_exit(conn, filtered_text):
        return True

    # 检查是否是唤醒词
    if await checkWakeupWords(conn, filtered_text):
        return True

    if conn.intent_type == "function_call":
        # 使用支持function calling的聊天方法,不再进行意图分析
        return False
    # 使用LLM进行意图分析
    intent_result = await analyze_intent_with_llm(conn, text)
    if not intent_result:
        return False
    # 会话开始时生成sentence_id
    conn.sentence_id = str(uuid.uuid4().hex)
    # 处理各种意图
    return await process_intent_result(conn, intent_result, text)


async def check_direct_exit(conn, text):
    """检查是否有退出意图 - 多层匹配策略
    
    匹配层级:
    - Layer 1: 配置词表精确匹配 (cmd_exit from config)
    - Layer 2: 内置词表精确匹配 (EXIT_PHRASES, 支持英文大小写不敏感)
    - Layer 3: 核心词后缀匹配 (EXIT_CORE_KEYWORDS)
    - Layer 4: 正则模式匹配 (EXIT_PATTERNS)
    
    任意一层命中即触发：播放告别语 + 关闭连接
    """
    _, clean_text = remove_punctuation_and_length(text)
    # 英文转小写用于匹配（词表中英文均为小写）
    clean_text_lower = clean_text.lower()
    
    matched = False
    match_source = ""
    
    # Layer 1: 配置词表精确匹配
    cmd_exit = set(conn.cmd_exit) if conn.cmd_exit else set()
    if clean_text in cmd_exit or clean_text_lower in cmd_exit:
        matched = True
        match_source = f"config:{clean_text}"
    
    # Layer 2: 内置词表精确匹配（英文大小写不敏感）
    elif clean_text in EXIT_PHRASES or clean_text_lower in EXIT_PHRASES:
        matched = True
        match_source = f"builtin:{clean_text}"
    
    # Layer 3: 核心词后缀匹配（处理 "请退出"、"please exit" 等）
    elif any(clean_text_lower.endswith(kw) for kw in EXIT_CORE_KEYWORDS):
        matched = True
        matched_kw = next(kw for kw in EXIT_CORE_KEYWORDS if clean_text_lower.endswith(kw))
        match_source = f"suffix:{clean_text}(kw={matched_kw})"
    
    # Layer 4: 正则模式匹配（处理 "不想和你聊了"、"I don't want to talk" 等复杂表达）
    else:
        for pattern in EXIT_PATTERNS:
            if pattern.search(clean_text):
                matched = True
                match_source = f"pattern:{pattern.pattern}"
                break
    
    if matched:
        conn.logger.bind(tag=TAG).info(f"识别到退出意图: '{text}' (来源: {match_source})")
        await _say_goodbye_and_close(conn, text)
        return True
    
    return False


async def _say_goodbye_and_close(conn, original_text):
    """播放告别语并关闭连接
    
    Args:
        conn: 连接处理器
        original_text: 用户原始输入（用于上报）
    """
    # 获取告别语：优先使用配置的结束语，否则使用默认值
    goodbye_text = getattr(conn, '_voice_closing', None) or "好的，再见！"
    
    # 发送用户消息（上报）
    await send_stt_message(conn, original_text)
    
    # 生成 sentence_id 用于 TTS
    conn.sentence_id = str(uuid.uuid4().hex)
    
    # 播放告别语
    conn.tts.tts_text_queue.put(
        TTSMessageDTO(
            sentence_id=conn.sentence_id,
            sentence_type=SentenceType.FIRST,
            content_type=ContentType.ACTION,
        )
    )
    conn.tts.tts_one_sentence(conn, ContentType.TEXT, content_detail=goodbye_text)
    conn.tts.tts_text_queue.put(
        TTSMessageDTO(
            sentence_id=conn.sentence_id,
            sentence_type=SentenceType.LAST,
            content_type=ContentType.ACTION,
        )
    )
    
    # 记录对话
    conn.dialogue.put(Message(role="assistant", content=goodbye_text))
    
    # 标记：TTS 播放完成后关闭连接
    conn.close_after_chat = True


async def analyze_intent_with_llm(conn, text):
    """使用LLM分析用户意图"""
    if not hasattr(conn, "intent") or not conn.intent:
        conn.logger.bind(tag=TAG).warning("意图识别服务未初始化")
        return None

    # 对话历史记录
    dialogue = conn.dialogue
    try:
        intent_result = await conn.intent.detect_intent(conn, dialogue.dialogue, text)
        return intent_result
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"意图识别失败: {str(e)}")

    return None


async def process_intent_result(conn, intent_result, original_text):
    """处理意图识别结果"""
    try:
        # 尝试将结果解析为JSON
        intent_data = json.loads(intent_result)

        # 检查是否有function_call
        if "function_call" in intent_data:
            # 直接从意图识别获取了function_call
            conn.logger.bind(tag=TAG).debug(
                f"检测到function_call格式的意图结果: {intent_data['function_call']['name']}"
            )
            function_name = intent_data["function_call"]["name"]
            if function_name == "continue_chat":
                return False

            if function_name == "result_for_context":
                await send_stt_message(conn, original_text)
                conn.client_abort = False
                
                def process_context_result():
                    conn.dialogue.put(Message(role="user", content=original_text))
                    
                    from core.utils.current_time import get_current_time_info

                    current_time, today_date, today_weekday, lunar_date = get_current_time_info()
                    
                    # 构建带上下文的基础提示
                    context_prompt = f"""当前时间：{current_time}
                                        今天日期：{today_date} ({today_weekday})
                                        今天农历：{lunar_date}

                                        请根据以上信息回答用户的问题：{original_text}"""
                    
                    response = conn.intent.replyResult(context_prompt, original_text)
                    speak_txt(conn, response)
                
                conn.executor.submit(process_context_result)
                return True

            function_args = {}
            if "arguments" in intent_data["function_call"]:
                function_args = intent_data["function_call"]["arguments"]
                if function_args is None:
                    function_args = {}
            # 确保参数是字符串格式的JSON
            if isinstance(function_args, dict):
                function_args = json.dumps(function_args)

            function_call_data = {
                "name": function_name,
                "id": str(uuid.uuid4().hex),
                "arguments": function_args,
            }

            await send_stt_message(conn, original_text)
            conn.client_abort = False

            # 使用executor执行函数调用和结果处理
            def process_function_call():
                conn.dialogue.put(Message(role="user", content=original_text))

                # 使用统一工具处理器处理所有工具调用
                try:
                    result = asyncio.run_coroutine_threadsafe(
                        conn.func_handler.handle_llm_function_call(
                            conn, function_call_data
                        ),
                        conn.loop,
                    ).result()
                except Exception as e:
                    conn.logger.bind(tag=TAG).error(f"工具调用失败: {e}")
                    result = ActionResponse(
                        action=Action.ERROR, result=str(e), response=str(e)
                    )

                if result:
                    if result.action == Action.RESPONSE:  # 直接回复前端
                        text = result.response
                        if text is not None:
                            speak_txt(conn, text)
                    elif result.action == Action.REQLLM:  # 调用函数后再请求llm生成回复
                        text = result.result
                        conn.dialogue.put(Message(role="tool", content=text))
                        llm_result = conn.intent.replyResult(text, original_text)
                        if llm_result is None:
                            llm_result = text
                        speak_txt(conn, llm_result)
                    elif (
                        result.action == Action.NOTFOUND
                        or result.action == Action.ERROR
                    ):
                        text = result.result
                        if text is not None:
                            speak_txt(conn, text)
                    elif function_name != "play_music":
                        # For backward compatibility with original code
                        # 获取当前最新的文本索引
                        text = result.response
                        if text is None:
                            text = result.result
                        if text is not None:
                            speak_txt(conn, text)

            # 将函数执行放在线程池中
            conn.executor.submit(process_function_call)
            return True
        return False
    except json.JSONDecodeError as e:
        conn.logger.bind(tag=TAG).error(f"处理意图结果时出错: {e}")
        return False


def speak_txt(conn, text):
    conn.tts.tts_text_queue.put(
        TTSMessageDTO(
            sentence_id=conn.sentence_id,
            sentence_type=SentenceType.FIRST,
            content_type=ContentType.ACTION,
        )
    )
    conn.tts.tts_one_sentence(conn, ContentType.TEXT, content_detail=text)
    conn.tts.tts_text_queue.put(
        TTSMessageDTO(
            sentence_id=conn.sentence_id,
            sentence_type=SentenceType.LAST,
            content_type=ContentType.ACTION,
        )
    )
    conn.dialogue.put(Message(role="assistant", content=text))
