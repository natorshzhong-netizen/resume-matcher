"""结构化抽取：把简历和 JD 都转成固定字段的 JSON。

先抽取再评分，好处是：
1. 评分规则可以脱离模型单独测试；
2. 界面能展示「识别到了什么」，模型抽错时一眼可见；
3. 同一份 JD 可以复用到多份简历，不必重复调用。
"""
from __future__ import annotations

from .llm import chat_json

RESUME_SCHEMA = """{
  "name": "姓名，没有就空字符串",
  "years_experience": 0,
  "education": "最高学历：中专/大专/本科/硕士/博士/未知",
  "school": "学校名",
  "major": "专业",
  "skills": ["硬技能，如 Python、SQL、Docker"],
  "projects": [{"name": "项目名", "tech": ["技术"], "summary": "一句话做了什么"}],
  "certificates": ["证书"],
  "highlights": ["最能体现能力的 2-3 条"]
}"""

JD_SCHEMA = """{
  "title": "岗位名称",
  "seniority": "实习/校招/社招",
  "min_years": 0,
  "required_skills": ["必须项技能"],
  "preferred_skills": ["加分项技能"],
  "responsibilities": ["主要职责，简短"],
  "keywords": ["JD 里反复出现的关键词"]
}"""

RESUME_PROMPT = (
    "你是简历解析器。从下面的简历文本中抽取结构化信息，严格输出 JSON，不要任何解释。\n"
    f"JSON 结构：{RESUME_SCHEMA}\n"
    "规则：\n"
    "1. skills 只放可验证的硬技能（语言、框架、数据库、工具），不要放「沟通能力强」这类软素质；\n"
    "2. years_experience 是推断的正式工作年限，实习生按 0 计；\n"
    "3. 文本里没有的信息留空或 0，不要编造。"
)

JD_PROMPT = (
    "你是招聘需求解析器。从下面的 JD 文本中抽取结构化信息，严格输出 JSON，不要任何解释。\n"
    f"JSON 结构：{JD_SCHEMA}\n"
    "规则：\n"
    '1. required_skills 是「必须/熟悉/掌握」的硬技能，preferred_skills 是「优先/加分」的；\n'
    '2. min_years 只填明确写了年限的，没写就 0；\n'
    "3. 不要把公司福利、团队介绍写进技能。"
)


def parse_resume(text: str) -> dict:
    return chat_json([
        {"role": "system", "content": RESUME_PROMPT},
        {"role": "user", "content": f"【简历】\n{text}"},
    ])


def parse_jd(text: str) -> dict:
    return chat_json([
        {"role": "system", "content": JD_PROMPT},
        {"role": "user", "content": f"【JD】\n{text}"},
    ])
