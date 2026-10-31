"""命令行入口：

    python -m src.cli extract 简历.docx          # 只看抽取结果
    python -m src.cli match 简历.docx JD.txt      # 完整匹配打分
    python -m src.cli match 简历.docx --jd-text "..."
"""
from __future__ import annotations

import argparse
import json
import sys

from .extract import parse_jd, parse_resume
from .parse import read_any, read_text_or_file
from .score import score


def cmd_extract(args) -> None:
    profile = parse_resume(read_any(args.resume))
    print(json.dumps(profile, ensure_ascii=False, indent=2))


def cmd_match(args) -> None:
    resume_text = read_any(args.resume)
    jd_text = args.jd_text or read_text_or_file(args.jd or "")
    if not jd_text.strip():
        sys.exit("请提供 JD 文本或文件")

    profile = parse_resume(resume_text)
    jd = parse_jd(jd_text)
    result = score(profile, jd)

    print(f"\n岗位：{jd.get('title', '')}    最终匹配分：{result['final_score']}")
    print(f"硬技能覆盖：{result['hard_coverage']}%   模型评分：{result['llm_score']}")
    print(f"\n结论：{result['verdict']}")
    if result["missing_skills"]:
        print(f"\n缺少的必备技能：{'、'.join(result['missing_skills'])}")
    else:
        print("\n必备技能：全部覆盖")
    for key, label in (("strengths", "优势"), ("gaps", "差距"), ("suggestions", "建议")):
        if result[key]:
            print(f"\n{label}：")
            for item in result[key]:
                print(f"  · {item}")
    if args.json:
        print("\n" + json.dumps({"profile": profile, "jd": jd, "result": result},
                                ensure_ascii=False, indent=2))


def main() -> None:
    p = argparse.ArgumentParser(description="简历-JD 匹配打分")
    sub = p.add_subparsers(dest="cmd", required=True)

    pe = sub.add_parser("extract", help="只做结构化抽取")
    pe.add_argument("resume")
    pe.set_defaults(func=cmd_extract)

    pm = sub.add_parser("match", help="完整匹配打分")
    pm.add_argument("resume")
    pm.add_argument("jd", nargs="?", help="JD 文件路径")
    pm.add_argument("--jd-text", default="", help="直接粘贴 JD 文本")
    pm.add_argument("--json", action="store_true")
    pm.set_defaults(func=cmd_match)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
