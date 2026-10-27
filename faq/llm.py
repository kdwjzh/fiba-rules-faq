"""LLM 設定抽象化：同一份程式碼，靠環境變數切換本地與雲端模型（改自課程 Lab 5）。"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # 讀取 repo 根目錄的 .env；不會覆蓋已存在的環境變數

PRESETS = {  # 預設值；實際以 .env 為準
    "local": ("http://127.0.0.1:11434/v1", "qwen3:1.7b"),
    "openai": ("https://api.openai.com/v1", "gpt-6-luna"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/", "gemini-3.8-flash"),
    "anthropic": ("https://api.anthropic.com/v1/", "claude-haiku-5-5"),
}

EMBED_MODEL = os.getenv("EMBED_MODEL", "qwen3-embedding:0.6b")


@dataclass
class LLM:
    profile: str
    client: OpenAI
    model: str


def get_llm(profile: str | None = None) -> LLM:
    profile = profile or os.getenv("LLM_PROFILE", "local")
    if profile not in PRESETS:
        raise ValueError(f"未知的 profile：{profile}（可用：{', '.join(PRESETS)}）")
    p = profile.upper()
    base, model = PRESETS[profile]
    base = os.getenv(f"{p}_BASE_URL", base)
    # Lab 5 原版雲端也會 fallback 到 LLM_MODEL，把 qwen3 拿去打雲端導致 404；只有 local 讀 LLM_MODEL
    if profile == "local":
        model = os.getenv("LOCAL_MODEL", os.getenv("LLM_MODEL", model))
    else:
        model = os.getenv(f"{p}_MODEL", model)
    key = os.getenv(f"{p}_API_KEY", "ollama")  # Ollama 不驗 key
    return LLM(profile, OpenAI(base_url=base, api_key=key, timeout=120), model)


# 每百萬 token 的美元價格（輸入, 輸出），沿用課程 Lab 5 的價目表；本地模型以 0 計
# 要包含 .env 實際使用的雲端模型，否則費用會顯示 0
PRICES = {
    "gpt-6-luna": (0.10, 0.50),
    "gpt-6.1-sol": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "gemini-3.1-pro-preview": (2.00, 12.00),
}


def cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pin, pout = PRICES.get(model, (0.0, 0.0))
    return (prompt_tokens * pin + completion_tokens * pout) / 1_000_000
