import asyncio
import logging
import subprocess
import sys

from app.config import settings

logger = logging.getLogger(__name__)

_lightrag_process = None


async def start_lightrag_server():
    """在后台启动 LightRAG 服务器"""
    global _lightrag_process

    if not settings.ENABLE_LIGHTRAG_SERVER:
        logger.info("LightRAG server disabled (ENABLE_LIGHTRAG_SERVER=False)")
        return

    try:
        logger.info(f"Starting LightRAG server on {settings.LIGHTRAG_SERVER_HOST}:{settings.LIGHTRAG_SERVER_PORT}...")

        # 构建环境变量
        env = {
            **subprocess.os.environ,
            "HOST": settings.LIGHTRAG_SERVER_HOST,
            "PORT": str(settings.LIGHTRAG_SERVER_PORT),
            "LLM_BINDING": settings.LIGHTRAG_LLM_BINDING,
            "LLM_MODEL": settings.LIGHTRAG_LLM_MODEL,
            "EMBEDDING_BINDING": settings.LIGHTRAG_EMBEDDING_BINDING,
            "EMBEDDING_MODEL": settings.LIGHTRAG_EMBEDDING_MODEL,
            "EMBEDDING_DIM": str(settings.LIGHTRAG_EMBEDDING_DIM),
            "SUMMARY_LANGUAGE": "Chinese",
            "RERANK_BINDING": "null",
        }

        # LLM 配置
        if settings.LIGHTRAG_LLM_BINDING == "openai":
            env["LLM_BINDING_HOST"] = settings.LIGHTRAG_LLM_HOST or settings.LLM_API_BASE
            env["LLM_BINDING_API_KEY"] = settings.LLM_API_KEY
        elif settings.LIGHTRAG_LLM_BINDING == "ollama":
            env["LLM_BINDING_HOST"] = settings.LIGHTRAG_LLM_HOST or settings.OLLAMA_HOST

        # Embedding 配置
        if settings.LIGHTRAG_EMBEDDING_BINDING == "openai":
            env["EMBEDDING_BINDING_HOST"] = settings.LIGHTRAG_EMBEDDING_HOST or settings.LLM_API_BASE
            env["EMBEDDING_BINDING_API_KEY"] = settings.LLM_API_KEY
        elif settings.LIGHTRAG_EMBEDDING_BINDING == "ollama":
            env["EMBEDDING_BINDING_HOST"] = settings.LIGHTRAG_EMBEDDING_HOST or settings.OLLAMA_HOST

        _lightrag_process = subprocess.Popen(
            [sys.executable, "-m", "lightrag.api.lightrag_server"],
            env=env,
        )

        logger.info(f"LightRAG server started (PID: {_lightrag_process.pid})")

    except Exception as e:
        logger.error(f"Failed to start LightRAG server: {e}")


async def stop_lightrag_server():
    """停止 LightRAG 服务器"""
    global _lightrag_process

    if _lightrag_process:
        logger.info("Stopping LightRAG server...")
        _lightrag_process.terminate()
        try:
            _lightrag_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _lightrag_process.kill()
        _lightrag_process = None
