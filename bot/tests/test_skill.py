"""官方 skill 生成的 issue 正文，必须能被封存机器人原样解析。"""

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

from liuren_bot.parse import form_fields, question_from_form, verdict_from_form

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("liuren_skill", ROOT / "skill" / "liuren_skill.py")
skill = importlib.util.module_from_spec(spec)
sys.modules["liuren_skill"] = skill
spec.loader.exec_module(skill)


def args(**kw):
    base = dict(time="2026-10-08 14:20", question="能否一次通过", category="考试", deadline="2027-05-31",
                model="claude-opus-5-5", harness="claude-code 2.1", skill=None, tools=True,
                outcome="成", confidence="0.65", window="2027-05-06 ~ 2027-06-05", basis="铸印乘轩")
    base.update(kw)
    return SimpleNamespace(**base)


def test_skill_issue_body_parses():
    f = form_fields(skill.issue_body(skill.issue_fields(args())))
    q = question_from_form(f)
    v = verdict_from_form(f)
    assert q == {"time": "2026-10-08 14:20", "question": "能否一次通过", "category": "考试", "deadline": "2027-05-31"}
    assert v["judge"] == {"model": "claude-opus-5-5", "harness": "claude-code 2.1", "skill": skill.SKILL_VERSION, "tools": True}
    assert v["complete"] and v["confidence"] == 0.7 and v["window"] == {"from": "2027-05-06", "to": "2027-06-05"}


def test_skill_bucheng_drops_window():
    v = verdict_from_form(form_fields(skill.issue_body(skill.issue_fields(args(outcome="不成", basis="")))))
    assert v["outcome"] == "不成" and v["window"] is None and v["basis"] == ""


def test_versions_consistent():
    assert skill.PROMPT_VERSION in (ROOT / "skill" / "prompt.md").read_text("utf-8")
    assert f"version: {skill.SKILL_VERSION.split()[-1]}" in (ROOT / "skill" / "SKILL.md").read_text("utf-8")
    ui = (ROOT / "web" / "ui.js").read_text("utf-8")
    assert f'PROMPT_VERSION = "{skill.PROMPT_VERSION}"' in ui
