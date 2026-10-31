"""匹配打分：确定性规则 + 模型判断，两部分加权。

为什么不是全交给模型：
- 规则部分（硬技能覆盖）可复现、可单测，同一输入永远同一结果；
- 模型部分负责规则算不出的东西（项目相关性、年限匹配、表述质量）；
- 两者分开输出，用户能看到「分是从哪来的」。
"""
from __future__ import annotations

import re

from .config import W_COVERAGE, W_LLM
from .llm import chat_json

# 同义词归一：不同写法指向同一个技能，否则覆盖率会被无谓拉低
SYNONYMS = {
    "js": "javascript", "ts": "typescript", "py": "python", "golang": "go",
    "k8s": "kubernetes", "postgres": "postgresql", "mysql": "mysql",
    "大模型": "llm", "机器学习": "machine learning", "深度学习": "deep learning",
    "自然语言处理": "nlp", "计算机视觉": "cv", "向量数据库": "vector database",
    "爬虫": "web scraping", "前后端": "full stack",
}
PUNCT = re.compile(r"[\s\-_/·、，,。.;；:：()（）\[\]【】]+")


def canon(skill: str) -> str:
    s = PUNCT.sub("", (skill or "").lower())
    return SYNONYMS.get(s, s)


def skill_match(required: str, have: list[str]) -> bool:
    r = canon(required)
    if not r:
        return True
    for h in have:
        hc = canon(h)
        if not hc:
            continue
        if r == hc:
            return True
        # 允许包含关系，但太短的词（如 go）容易误判，要求至少 3 个字符
        if len(r) >= 3 and len(hc) >= 3 and (r in hc or hc in r):
            return True
    return False


def coverage(required: list[str], have: list[str]) -> dict:
    required = [s for s in dict.fromkeys(required) if s and s.strip()]
    if not required:
        return {"ratio": 1.0, "matched": [], "missing": []}
    matched = [s for s in required if skill_match(s, have)]
    missing = [s for s in required if s not in matched]
    return {"ratio": len(matched) / len(required), "matched": matched, "missing": missing}


JUDGE_PROMPT = """你是资深技术招聘官。请对比候选人画像与岗位要求，给出客观评估。
只输出 JSON：
{
  "score": 0-100 的整数,
  "verdict": "一句话结论，不超过 30 字",
  "strengths": ["匹配得好的点，最多 3 条"],
  "gaps": ["明确的差距，最多 3 条"],
  "suggestions": ["给候选人最有价值的 2 条改进建议"]
}
评分参考：硬技能覆盖 50%，项目相关度 30%，年限与学历匹配 20%。
只依据给出的信息判断，不要假设候选人具备未提及的能力。"""


def llm_judge(profile: dict, jd: dict) -> dict:
    return chat_json([
        {"role": "system", "content": JUDGE_PROMPT},
        {"role": "user", "content": (
            f"【候选人画像】\n{profile}\n\n【岗位要求】\n{jd}"
        )},
    ])


def score(profile: dict, jd: dict) -> dict:
    have = list(profile.get("skills") or [])
    req = list(jd.get("required_skills") or [])
    pref = list(jd.get("preferred_skills") or [])

    cov = coverage(req, have)
    cov_pref = coverage(pref, have)
    judge = llm_judge(profile, jd)

    llm_score = float(judge.get("score", 0))
    final = round(W_COVERAGE * cov["ratio"] * 100 + W_LLM * llm_score, 1)

    return {
        "final_score": final,
        "hard_coverage": round(cov["ratio"] * 100, 1),
        "preferred_coverage": round(cov_pref["ratio"] * 100, 1),
        "llm_score": llm_score,
        "matched_skills": cov["matched"],
        "missing_skills": cov["missing"],
        "missing_preferred": cov_pref["missing"],
        "verdict": judge.get("verdict", ""),
        "strengths": judge.get("strengths", []),
        "gaps": judge.get("gaps", []),
        "suggestions": judge.get("suggestions", []),
    }
