# -*- coding: utf-8 -*-
"""
延迟指标收集工具

用于监控实时语音对话系统的关键延迟指标：
- ASR 延迟：用户说完到识别结果返回的时间
- LLM TTFT：请求发出到首个 token 返回的时间
- TTS 延迟：文本发送到首个音频块返回的时间
- E2E TTFB：端到端首字节时间（用户说完到听到第一个音节）
"""

import time
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


@dataclass
class LatencyRecord:
    """单次延迟记录"""
    metric_name: str
    value_ms: float
    timestamp: float = field(default_factory=time.time)
    session_id: Optional[str] = None
    extra_info: Optional[Dict] = None


class LatencyMetrics:
    """延迟指标收集器"""
    
    def __init__(self, session_id: str = None, enable_logging: bool = True):
        self.session_id = session_id
        self.enable_logging = enable_logging
        
        # 时间戳记录
        self.asr_start_time: Optional[float] = None  # ASR 开始时间（用户开始说话）
        self.asr_final_time: Optional[float] = None  # ASR Final 结果时间
        self.llm_request_time: Optional[float] = None  # LLM 请求发出时间
        self.llm_first_token_time: Optional[float] = None  # LLM 首 token 时间
        self.tts_request_time: Optional[float] = None  # TTS 请求发出时间
        self.tts_first_audio_time: Optional[float] = None  # TTS 首音频时间
        self.first_audio_play_time: Optional[float] = None  # 首音频播放时间
        
        # 历史记录
        self.records: List[LatencyRecord] = []
        
    def reset(self):
        """重置 LLM/TTS 相关时间戳（chat 开始时调用）
        
        注意：保留 ASR 相关时间戳（asr_start_time, asr_final_time），
        因为 ASR 在 chat() 之前完成，用于计算 e2e_ttfb
        """
        # 保留 ASR 时间戳，只重置 LLM/TTS 相关
        self.llm_request_time = None
        self.llm_first_token_time = None
        self.tts_request_time = None
        self.tts_first_audio_time = None
        self.first_audio_play_time = None
    
    def reset_all(self):
        """重置所有时间戳（新会话开始时调用）"""
        self.asr_start_time = None
        self.asr_final_time = None
        self.reset()
    
    def mark_asr_start(self):
        """标记 ASR 开始（用户开始说话）"""
        self.asr_start_time = time.time() * 1000  # 转换为毫秒
        
    def mark_asr_final(self):
        """标记 ASR Final 结果返回"""
        self.asr_final_time = time.time() * 1000
        
        if self.asr_start_time:
            latency = self.asr_final_time - self.asr_start_time
            self._record("asr_latency", latency)
    
    def record_asr_latency(self, latency_ms: float):
        """直接记录 ASR 延迟值（用于流式 ASR 如 Deepgram）
        
        流式 ASR 中，每次识别结果的延迟应该独立计算，
        而不是从会话开始累积计算。
        """
        self.asr_final_time = time.time() * 1000
        self._record("asr_latency", latency_ms)
            
    def mark_llm_request(self):
        """标记 LLM 请求发出"""
        self.llm_request_time = time.time() * 1000
        
    def mark_llm_first_token(self):
        """标记 LLM 首 token 返回"""
        if self.llm_first_token_time is None:  # 只记录第一个 token
            self.llm_first_token_time = time.time() * 1000
            
            if self.llm_request_time:
                latency = self.llm_first_token_time - self.llm_request_time
                self._record("llm_ttft", latency)
                
    def mark_tts_request(self, text: str = None):
        """标记 TTS 请求发出"""
        self.tts_request_time = time.time() * 1000
        
    def mark_tts_first_audio(self):
        """标记 TTS 首音频返回"""
        if self.tts_first_audio_time is None:  # 只记录第一个音频块
            self.tts_first_audio_time = time.time() * 1000
            
            if self.tts_request_time:
                latency = self.tts_first_audio_time - self.tts_request_time
                self._record("tts_latency", latency)
                
    def mark_first_audio_play(self):
        """标记首音频开始播放"""
        if self.first_audio_play_time is None:
            self.first_audio_play_time = time.time() * 1000
            
            # 计算端到端 TTFB
            if self.asr_final_time:
                e2e_ttfb = self.first_audio_play_time - self.asr_final_time
                self._record("e2e_ttfb", e2e_ttfb)
                
            # 计算完整链路延迟（从用户开始说话到听到回复）
            if self.asr_start_time:
                full_latency = self.first_audio_play_time - self.asr_start_time
                self._record("full_latency", full_latency)
    
    def _record(self, metric_name: str, value_ms: float, extra_info: Dict = None):
        """记录延迟指标"""
        record = LatencyRecord(
            metric_name=metric_name,
            value_ms=value_ms,
            session_id=self.session_id,
            extra_info=extra_info
        )
        self.records.append(record)
        
        if self.enable_logging:
            logger.bind(tag=TAG).info(
                f"LATENCY_METRIC | {metric_name}={value_ms:.1f}ms | session={self.session_id}"
            )
    
    def get_summary(self) -> Dict:
        """获取延迟摘要"""
        summary = {}
        for record in self.records:
            if record.metric_name not in summary:
                summary[record.metric_name] = []
            summary[record.metric_name].append(record.value_ms)
        
        # 计算平均值
        result = {}
        for name, values in summary.items():
            result[name] = {
                "count": len(values),
                "avg_ms": sum(values) / len(values) if values else 0,
                "min_ms": min(values) if values else 0,
                "max_ms": max(values) if values else 0,
            }
        return result
    
    def get_last_metrics(self) -> Dict:
        """获取最近一轮对话的延迟指标"""
        return {
            "asr_latency_ms": (self.asr_final_time - self.asr_start_time) 
                if self.asr_start_time and self.asr_final_time else None,
            "llm_ttft_ms": (self.llm_first_token_time - self.llm_request_time)
                if self.llm_request_time and self.llm_first_token_time else None,
            "tts_latency_ms": (self.tts_first_audio_time - self.tts_request_time)
                if self.tts_request_time and self.tts_first_audio_time else None,
            "e2e_ttfb_ms": (self.first_audio_play_time - self.asr_final_time)
                if self.asr_final_time and self.first_audio_play_time else None,
        }


# 全局延迟指标实例（可选，用于简化访问）
_global_metrics: Dict[str, LatencyMetrics] = {}


def get_metrics(session_id: str) -> LatencyMetrics:
    """获取或创建指定会话的延迟指标实例"""
    if session_id not in _global_metrics:
        _global_metrics[session_id] = LatencyMetrics(session_id=session_id)
    return _global_metrics[session_id]


def remove_metrics(session_id: str):
    """移除指定会话的延迟指标实例"""
    if session_id in _global_metrics:
        del _global_metrics[session_id]
