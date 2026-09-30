"""官方 skill 的命令行工具：起课、拼提示词、生成实占 issue。只依赖 liuren_core。

    python skill/liuren_skill.py prompt --question "…" --deadline 2027-05-31 [--time "2026-09-30 22:52"]
    python skill/liuren_skill.py issue  --question "…" --category 考试 --deadline 2027-05-31 --time "…" \\
        --model claude-opus-5-5 --harness "claude-code 2.1" --tools \\
        --outcome 不成 --confidence 0.6 [--window "2027-05-01 ~ 2027-05-31"] [--basis "…"] [--url | --submit]

提示词与 web/ui.js 的 buildPrompt 逐字一致（CI 比对）。issue 正文与 .github/ISSUE_TEMPLATE/live.yml 渲染出的一致，
封存机器人按同一套标题解析。
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from liuren_core import cast_at
from liuren_core.text import GENERAL_NAMES, SHEN_NAMES, chart_text

HERE = Path(__file__).resolve().parent
PROMPT_VERSION = "liuren-prompt 0.2"   # 与 prompt.md 里的 skill 行一致
SKILL_VERSION = "liuren-skill 0.1"     # 与 SKILL.md 的 version 一致；用 skill 断的，断者记这个
REPO = "arlen-liang/liuren-bench"
CATEGORIES = ["求职", "工作", "财运", "感情", "健康（仅限本人）", "出行", "失物", "考试", "其他"]
BJT = timezone(timedelta(hours=8))


def load():
    return (HERE / "prompt.md").read_text("utf-8"), json.loads((HERE / "duanfa" / "daquan.json").read_text("utf-8"))


def gate_key(chart: dict) -> str:
    m = chart["method"]
    return f"贼克·{m['name']}" if m["gate"] == "贼克" else m["gate"]


def excerpts(chart: dict, daquan: dict) -> str:
    parts = [f"【参考原文】以下摘自{daquan['source']}，供断课引据，未必句句切题："]
    parts.append(f"〈课体·{gate_key(chart)}〉\n{daquan['gate'][gate_key(chart)]}")
    branches = list(dict.fromkeys(n["branch"] for n in chart["transmissions"]))
    generals = list(dict.fromkeys(n["general"] for n in chart["transmissions"]))
    parts += [f"〈十二神·{b}（{SHEN_NAMES[b]}）〉\n{daquan['shen'][b]}" for b in branches]
    parts += [f"〈天将·{GENERAL_NAMES[g]}〉\n{daquan['jiang'][g]}" for g in generals]
    return "\n\n".join(parts)


def build_prompt(chart: dict, question: str, deadline: str, template=None, daquan=None) -> str:
    if template is None:
        template, daquan = load()
    # 一次替换全部占位符，只扫模板：用户文本里就算写了 {{chart}} 也不会被二次替换
    values = {"question": question, "deadline": deadline, "chart": chart_text(chart), "excerpts": excerpts(chart, daquan)}
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], template)


def issue_fields(a) -> dict:
    return {
        "time": a.time, "question": a.question, "category": a.category, "deadline": a.deadline,
        "judge_type": "AI", "model": a.model, "harness": a.harness, "skill": a.skill or SKILL_VERSION,
        "tools": "能（可跑代码或查资料）" if a.tools else "不能",
        "outcome": a.outcome, "window": a.window if a.outcome == "成" else "",
        "confidence": f"{float(a.confidence):.1f}", "basis": a.basis or "",
    }


FORM_LABELS = [("time", "起课时间"), ("question", "占事"), ("category", "类别"), ("deadline", "截止日"),
               ("judge_type", "谁断的"), ("model", "模型（AI 断的必填）"), ("harness", "harness（AI 断的必填）"),
               ("skill", "skill 或提示词（AI 断的必填）"), ("tools", "能否调用工具（AI 断的必填）"),
               ("outcome", "断：成还是不成"), ("window", "应期（断\"成\"时填）"), ("confidence", "把握"),
               ("basis", "依据（可选）")]


def issue_body(f: dict) -> str:
    """与 issue 表单渲染出的正文同构。确认四项默认勾上：用户已在 skill 里逐项确认过才会走到这一步。"""
    out = ["### 确认", "",
           "- [X] 这是我自己的事；或者涉及别人，但别人看了认不出是谁",
           "- [X] 没有真名、单位名、具体地址，不涉及未成年人",
           "- [X] 内容我自己看过（由 AI 或网页代填的也一样）",
           "- [X] 同意公开，并按 CC-BY-4.0 发布", ""]
    for key, label in FORM_LABELS:
        out += [f"### {label}", "", f[key] or "_No response_", ""]
    return "\n".join(out)


def issue_url(f: dict) -> str:
    q = {"template": "live.yml", "title": f"[实占] {f['question']}"[:120]}
    q.update({k: v for k, v in f.items() if v})
    return f"https://github.com/{REPO}/issues/new?" + urllib.parse.urlencode(q)


def main():
    ap = argparse.ArgumentParser(prog="liuren_skill")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prompt", help="起课并输出完整提示词")
    i = sub.add_parser("issue", help="生成实占 issue：默认打印正文；--url 打印预填链接；--submit 用 gh 提交")
    for s in (p, i):
        s.add_argument("--time", help='北京时间 "2026-10-08 14:20"，不给即现在')
        s.add_argument("--question", required=True)
        s.add_argument("--deadline", required=True)
    i.add_argument("--category", required=True, choices=CATEGORIES)
    i.add_argument("--model", required=True)
    i.add_argument("--harness", required=True)
    i.add_argument("--skill")
    i.add_argument("--tools", action="store_true")
    i.add_argument("--outcome", required=True, choices=["成", "不成"])
    i.add_argument("--confidence", required=True)
    i.add_argument("--window", default="")
    i.add_argument("--basis", default="")
    g = i.add_mutually_exclusive_group()
    g.add_argument("--url", action="store_true")
    g.add_argument("--submit", action="store_true")
    a = ap.parse_args()
    a.time = a.time or datetime.now(BJT).strftime("%Y-%m-%d %H:%M")
    if a.cmd == "prompt":
        chart = cast_at(datetime.strptime(a.time, "%Y-%m-%d %H:%M"))
        print(build_prompt(chart, a.question, a.deadline))
        return
    f = issue_fields(a)
    if a.url:
        print(issue_url(f))
    elif a.submit:
        r = subprocess.run(["gh", "issue", "create", "--repo", REPO, "--title", f"[实占] {a.question}"[:120],
                            "--body", issue_body(f)], capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip())
        sys.exit(r.returncode)
    else:
        print(issue_body(f))


if __name__ == "__main__":
    main()
