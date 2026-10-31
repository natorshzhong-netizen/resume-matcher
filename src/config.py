"""配置：全部走环境变量，密钥不落代码。"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_BASE = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
TEMPERATURE = float(os.getenv("TEMPERATURE", 0))
TIMEOUT = int(os.getenv("LLM_TIMEOUT", 120))

# 硬技能覆盖度与模型主观评分的权重
W_COVERAGE = float(os.getenv("W_COVERAGE", 0.6))
W_LLM = float(os.getenv("W_LLM", 0.4))
