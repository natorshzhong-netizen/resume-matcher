"""LLM 调用封装：统一走 OpenAI 兼容接口，默认 DeepSeek。"""
from __future__ import annotations

import json
import time

import requests

from .config import API_BASE, API_KEY, MODEL, TEMPERATURE, TIMEOUT


class LLMError(RuntimeError):
    pass


def chat(messages: list[dict], json_mode: bool = False, retries: int = 2) -> str:
    if not API_KEY:
        raise LLMError("未配置 DEEPSEEK_API_KEY，请在 .env 中填写")
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": TEMPERATURE,
        "response_format": {"type": "json_object"} if json_mode else None,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    last = None
    for attempt in range(retries + 1):
        try:
            r = requests.post(f"{API_BASE}/chat/completions", json=payload,
                              headers={"Authorization": f"Bearer {API_KEY}"},
                              timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:      # 网络抖动重试，业务错误直接抛出
            last = e
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise LLMError(f"调用失败：{last}")


def chat_json(messages: list[dict]) -> dict:
    """要求模型只输出 JSON，并做一次容错解析（去掉 ```json 代码块）。"""
    text = chat(messages, json_mode=True)
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        text = text[4:] if text.lower().startswith("json") else text
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMError(f"模型返回的不是合法 JSON：{text[:200]}") from e
