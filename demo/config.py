"""
配置文件
配置混元API和其他系统参数
"""
import os
from dotenv import load_dotenv

# 固定从 demo 目录加载 .env，避免从项目根运行时读到根目录的 .env
_demo_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_demo_dir, ".env"))

# ---------- 混元 API（腾讯）-----------
HUNYUAN_API_KEY = os.getenv("HUNYUAN_API_KEY", "")
HUNYUAN_API_ENDPOINT = os.getenv(
    "HUNYUAN_API_ENDPOINT",
    "https://api.hunyuan.cloud.tencent.com/v1/chat/completions"
)
USE_HUNYUAN = bool(HUNYUAN_API_KEY and HUNYUAN_API_ENDPOINT)
# 混元视觉模型名（看图）、文本模型名（生成问题/故事，可与视觉相同）
HUNYUAN_VISION_MODEL = os.getenv("HUNYUAN_VISION_MODEL", "hunyuan-vision")
HUNYUAN_TEXT_MODEL = os.getenv("HUNYUAN_TEXT_MODEL", "hunyuan-vision")

# ---------- Gemini API -----------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_ENDPOINT = os.getenv(
    "GEMINI_API_ENDPOINT",
    "https://generativelanguage.googleapis.com/v1beta"
)
USE_GEMINI = bool(GEMINI_API_KEY and GEMINI_API_ENDPOINT)


# Gemini模型配置
# 默认 gemini-2.5-pro 质量好但较慢；可改为 gemini-2.0-flash 以加快速度（略降质量）
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-pro")
# 故事生成最大 token 数，减小可加快生成但故事更短（默认 4096）
STORY_MAX_OUTPUT_TOKENS = int(os.getenv("STORY_MAX_OUTPUT_TOKENS", "4096"))

# 系统配置
MAX_DIALOGUE_ROUNDS = 1  # 单张照片只问一个问题，不再追问
MAX_CONTEXT_LENGTH = 4000  # 最大上下文长度
TEMPERATURE = 0.7  # 生成温度

# 向量数据库配置
VECTOR_DB_PATH = "./vector_db"  # 向量数据库存储路径

# 评估配置
EVALUATION_AGENT_MEMORY_SIZE = 50  # 评估Agent记忆库大小
