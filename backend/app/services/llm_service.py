"""LLM服务模块"""

import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from ..config import get_settings

# 全局LLM实例
_llm_instance: Optional[BaseChatModel] = None


def get_llm() -> BaseChatModel:
    """
    获取LLM实例(单例模式)
    
    Returns:
        LangChain ChatModel实例
    """
    global _llm_instance
    
    if _llm_instance is None:
        settings = get_settings()
        
        # 从环境变量读取配置，优先级：LLM_* > OPENAI_*
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or settings.openai_api_key
        base_url = os.getenv("LLM_BASE_URL") or settings.openai_base_url
        model = os.getenv("LLM_MODEL_ID") or settings.openai_model
        
        if not api_key:
            raise ValueError(
                "LLM API Key未配置。请在环境变量中设置 LLM_API_KEY 或 OPENAI_API_KEY"
            )
        
        # 创建 ChatOpenAI 实例
        _llm_instance = ChatOpenAI(
            api_key=api_key,
            base_url=base_url if base_url else None,
            model=model,
            temperature=0.7,
            timeout=60,
        )
        
        print(f"✅ LLM服务初始化成功")
        print(f"   模型: {model}")
        print(f"   Base URL: {base_url}")
        print(f"   API Key: {'已配置' if api_key else '未配置'}")
    
    return _llm_instance


def reset_llm():
    """重置LLM实例(用于测试或重新配置)"""
    global _llm_instance
    _llm_instance = None

