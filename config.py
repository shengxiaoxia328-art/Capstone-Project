"""
配置文件
配置混元API和其他系统参数
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API配置（支持混元或Gemini）
# 优先使用Gemini，如果没有则使用混元
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("HUNYUAN_API_KEY", ""))
# Gemini 默认使用 Google AI 官方 base URL；可改为代理或 Vertex 等
GEMINI_API_ENDPOINT = os.getenv(
    "GEMINI_API_ENDPOINT",
    os.getenv("HUNYUAN_API_ENDPOINT", "https://generativelanguage.googleapis.com/v1beta")
)
# 兼容旧配置（向后兼容）
HUNYUAN_API_KEY = GEMINI_API_KEY
HUNYUAN_API_ENDPOINT = GEMINI_API_ENDPOINT
# 使用的API类型
USE_GEMINI = bool(GEMINI_API_KEY and GEMINI_API_ENDPOINT)

# Gemini模型配置
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-pro")  # 默认模型名称

# 系统配置
MAX_DIALOGUE_ROUNDS = 10  # 单张照片最大对话轮数
MAX_CONTEXT_LENGTH = 4000  # 最大上下文长度
TEMPERATURE = 0.7  # 生成温度

# 向量数据库配置
VECTOR_DB_PATH = "./vector_db"  # 向量数据库存储路径

# 评估配置
EVALUATION_AGENT_MEMORY_SIZE = 50  # 评估Agent记忆库大小
