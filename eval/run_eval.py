"""评测：抽取是否完整、匹配是否排序正确。

两个检查点：
1. 结构完整性 —— 抽取结果必须包含约定的字段，否则界面会显示空白；
2. 排序正确性 —— 同一份 JD，强匹配简历的分数必须高于弱匹配简历。
   这是评分系统最基本的性质：如果排序都反了，分数再好看也没意义。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.extract import parse_jd, parse_resume      # noqa: E402
from src.parse import read_any                      # noqa: E402
from src.score import score                         # noqa: E402

REQUIRED_KEYS = {"skills", "projects", "education"}
JD_KEYS = {"required_skills", "preferred_skills"}


def main() -> None:
    cases = [json.loads(l) for l in (ROOT / "eval" / "cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    scores = []
    ok = True

    for case in cases:
        profile = parse_resume(read_any(ROOT / case["resume"]))
        jd = parse_jd(read_any(ROOT / case["jd"]))
        result = score(profile, jd)

        missing_keys = REQUIRED_KEYS - set(profile)
        missing_jd = JD_KEYS - set(jd)
        checks = []
        if missing_keys:
            checks.append(f"抽取缺字段 {sorted(missing_keys)}")
        if missing_jd:
            checks.append(f"JD 缺字段 {sorted(missing_jd)}")
        cov = result["hard_coverage"] / 100
        if "expect_min_coverage" in case and cov < case["expect_min_coverage"]:
            checks.append(f"覆盖度 {cov:.2f} 低于期望 {case['expect_min_coverage']}")
        if "expect_max_coverage" in case and cov > case["expect_max_coverage"]:
            checks.append(f"覆盖度 {cov:.2f} 高于期望 {case['expect_max_coverage']}")

        status = "PASS" if not checks else "FAIL"
        if checks:
            ok = False
        print(f"[{case['id']}] {status}  score={result['final_score']} cov={result['hard_coverage']}% "
              f"missing={result['missing_skills']}")
        for c in checks:
            print(f"    - {c}")
        scores.append(result["final_score"])

    if len(scores) >= 2:
        ordered = scores == sorted(scores, reverse=True)
        print(f"\n排序检查：{'PASS' if ordered else 'FAIL'}  强简历 {scores[0]} vs 弱简历 {scores[-1]}")
        ok = ok and ordered

    print("\n结果：", "全部通过" if ok else "存在失败项")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
