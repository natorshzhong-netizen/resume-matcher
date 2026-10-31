"""Gradio 界面：粘贴或给路径，输出匹配分与逐项分析。"""
from __future__ import annotations

import sys
from pathlib import Path

import gradio as gr

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.extract import parse_jd, parse_resume      # noqa: E402
from src.parse import read_text_or_file            # noqa: E402
from src.score import score                        # noqa: E402


def run_match(resume_input: str, jd_input: str):
    resume_text = read_text_or_file(resume_input)
    jd_text = read_text_or_file(jd_input)
    if not resume_text.strip() or not jd_text.strip():
        return "请填写简历和 JD（可直接粘贴文本，也可填文件路径）", ""

    try:
        profile = parse_resume(resume_text)
        jd = parse_jd(jd_text)
        r = score(profile, jd)
    except Exception as e:
        return f"处理失败：{e}", ""

    summary = (
        f"## {r['final_score']} 分 · {r['verdict']}\n\n"
        f"| 指标 | 数值 |\n|---|---|\n"
        f"| 硬技能覆盖 | {r['hard_coverage']}% |\n"
        f"| 加分项覆盖 | {r['preferred_coverage']}% |\n"
        f"| 模型评分 | {r['llm_score']} |\n"
    )
    if r["missing_skills"]:
        summary += f"\n**缺少的必备技能**：{'、'.join(r['missing_skills'])}\n"
    else:
        summary += "\n**必备技能**：全部覆盖 ✓\n"

    for key, label in (("strengths", "优势"), ("gaps", "差距"), ("suggestions", "建议")):
        if r[key]:
            summary += f"\n### {label}\n" + "\n".join(f"- {x}" for x in r[key]) + "\n"

    detail = "### 识别到的简历信息\n```json\n" + \
             __import__("json").dumps(profile, ensure_ascii=False, indent=2) + \
             "\n```\n### 识别到的岗位要求\n```json\n" + \
             __import__("json").dumps(jd, ensure_ascii=False, indent=2) + "\n```"
    return summary, detail


def build() -> gr.Blocks:
    with gr.Blocks(title="简历 × JD 匹配") as demo:
        gr.Markdown(
            "# 简历 × JD 匹配\n"
            "把简历和岗位描述放进来，输出匹配分、缺口和改简历的方向。"
            "支持直接粘贴文本，也支持填 `.docx` / `.pdf` / `.txt` 路径。"
        )
        with gr.Row():
            resume = gr.Textbox(label="简历", lines=12,
                                placeholder="粘贴简历文本，或填 C:\\path\\简历.docx")
            jd = gr.Textbox(label="JD", lines=12, placeholder="粘贴岗位描述")
        btn = gr.Button("开始匹配", variant="primary")
        out = gr.Markdown()
        with gr.Accordion("查看结构化抽取结果", open=False):
            detail = gr.Markdown()
        btn.click(run_match, inputs=[resume, jd], outputs=[out, detail])
    return demo


if __name__ == "__main__":
    build().launch(server_name="127.0.0.1", server_port=7861, inbrowser=False)
