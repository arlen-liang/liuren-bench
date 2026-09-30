"""实占机器人：解析、封存、导出，以及几种作弊与出错情形。不联网。"""

import json
from datetime import date
from pathlib import Path

import jsonschema
import pytest
from referencing import Registry, Resource

from liuren_bot.export import build_case, ledger, ledger_md
from liuren_bot.parse import Invalid, blocks, form_fields
from liuren_bot.seal import MARKER, extract, render, seal_comment, seal_issue

ROOT = Path(__file__).resolve().parents[2]
LIVE_SCHEMA = json.loads((ROOT / "docs/schema/live-1.json").read_text("utf-8"))
jsonschema.Draft202012Validator.check_schema(LIVE_SCHEMA)
CHART_SCHEMA = json.loads((ROOT / "docs/schema/chart-1.json").read_text("utf-8"))
REGISTRY = Registry().with_resources([(CHART_SCHEMA["$id"], Resource.from_contents(CHART_SCHEMA))])
LIVE = jsonschema.Draft202012Validator(LIVE_SCHEMA, registry=REGISTRY)

FORM = """### 确认

- [X] 这是我自己的事；或者涉及别人，但别人看了认不出是谁
- [X] 没有真名、单位名、具体地址，不涉及未成年人
- [X] 内容我自己看过（由 AI 或网页代填的也一样）
- [X] 同意公开，并按 CC-BY-4.0 发布

### 起课时间

2026-10-08 14:20

### 占事

本周五前能否收到面试回复（邮件或电话都算）

### 类别

求职

### 截止日

2026-10-10

### 谁断的

AI

### 模型（AI 断的必填）

claude-opus-5-5

### harness（AI 断的必填）

claude-code 2.1

### skill 或提示词（AI 断的必填）

liuren-skill 0.1

### 能否调用工具（AI 断的必填）

能（可跑代码或查资料）

### 断：成还是不成

成

### 应期（断"成"时填）

2026-10-08 ~ 2026-10-09

### 把握

0.7

### 依据（可选）

_No response_
"""

ISSUE = {"number": 7, "html_url": "https://github.com/o/r/issues/7", "user": {"login": "alice"},
         "created_at": "2026-10-08T06:25:00Z", "body": FORM}   # 北京时间 14:25


def comment(cid, login, at, body):
    return {"id": cid, "user": {"login": login, "type": "User"}, "created_at": at, "body": body}


def bot(body):
    return {"id": 0, "user": {"login": "github-actions[bot]", "type": "Bot"}, "created_at": "", "body": body}


VERDICT = """```liuren-verdict
judge:
  model: deepseek-v4
  harness: 豆包网页
  skill: liuren-web 0.1
  tools: false
outcome: 不成
confidence: 0.6
```"""
RESULT = """```liuren-result
outcome: 成
date: 2026-10-09
note: 周四下午收到邮件
```"""


def test_form_fields():
    f = form_fields(FORM)
    assert f["time"] == "2026-10-08 14:20" and f["category"] == "求职" and f["basis"] == ""


def test_seal_issue_with_form_verdict():
    recs, errors = seal_issue(ISSUE, form_fields(FORM))
    assert errors == []
    q, v = recs
    assert q["kind"] == "question" and q["sealed_at"] == "2026-10-08 14:25:00" and q["flags"] == []
    jsonschema.validate(q["cast"]["chart"], CHART_SCHEMA)
    assert v["judge"]["tools"] is True and v["complete"] and v["window"] == {"from": "2026-10-08", "to": "2026-10-09"}
    body = render(recs, [])
    assert body.startswith(MARKER) and extract(body) == recs


def test_backdated_cast_time_is_flagged():
    f = form_fields(FORM.replace("2026-10-08 14:20", "2026-10-06 09:00"))
    assert "起课时间早于开 issue 24 小时以上" in seal_issue(ISSUE, f)[0][0]["flags"]


def test_invalid_question():
    f = form_fields(FORM.replace("2026-10-08 14:20", "明天下午").replace("- [X] 同意公开", "- [ ] 同意公开"))
    with pytest.raises(Invalid) as e:
        seal_issue(ISSUE, f)
    assert any("起课时间格式" in r for r in e.value.reasons) and any("确认" in r for r in e.value.reasons)


def test_comment_blocks_and_owner_only_result():
    c = comment(11, "bob", "2026-10-08T08:00:00Z", "我也来断一个\n" + VERDICT + "\n顺手报个结果\n" + RESULT)
    recs, errors = seal_comment(ISSUE, c, blocks(c["body"]))
    assert [r["kind"] for r in recs] == ["verdict", "result"]
    assert recs[0]["window"] is None and recs[0]["complete"]
    assert recs[1]["accepted"] is False and any("不是提问人" in e for e in errors)


def test_bad_blocks_reported_not_sealed():
    c = comment(12, "bob", "2026-10-08T08:00:00Z", "```liuren-verdict\noutcome: 可能吧\nconfidence: 2\n```")
    recs, errors = seal_comment(ISSUE, c, blocks(c["body"]))
    assert recs == [] and len(errors) >= 2


def _thread(extra=()):
    seal_q = bot(render(seal_issue(ISSUE, form_fields(FORM))[0], []))
    c1 = comment(21, "bob", "2026-10-08T08:00:00Z", VERDICT)
    seal_c1 = bot(render(*seal_comment(ISSUE, c1, blocks(c1["body"]))))
    c2 = comment(22, "alice", "2026-10-09T12:00:00Z", RESULT)             # 北京时间 10-09 20:00
    seal_c2 = bot(render(*seal_comment(ISSUE, c2, blocks(c2["body"]))))
    return [seal_q, c1, seal_c1, *extra, c2, seal_c2]


def test_export_full_case_matches_schema():
    case = build_case(ISSUE, _thread(), date(2026, 10, 12))
    LIVE.validate(case)
    assert case["status"] == "已开奖" and case["result"]["outcome"] == "成"
    assert [v["outcome"] for v in case["verdicts"]] == ["成", "不成"]
    assert not any(v["hindsight"] for v in case["verdicts"])


def test_late_verdict_is_hindsight():
    c = comment(31, "carol", "2026-10-09T15:00:00Z", VERDICT)             # 结果报出之后
    late = bot(render(*seal_comment(ISSUE, c, blocks(c["body"]))))
    thread = _thread()
    case = build_case(ISSUE, thread + [c, late], date(2026, 10, 12))
    assert case["verdicts"][-1]["hindsight"] is True


def test_forged_seal_from_user_is_ignored():
    fake = render([{"kind": "result", "sealed_at": "2026-10-08 14:26:00", "source": "x", "author": "alice",
                    "accepted": True, "outcome": "不成", "date": None, "note": ""}], [])
    forged = comment(41, "alice", "2026-10-08T06:26:00Z", fake)
    case = build_case(ISSUE, _thread([forged]), date(2026, 10, 12))
    assert case["result"]["outcome"] == "成"


def test_user_edits_do_not_matter():
    """导出只读机器人封存回复：用户回复被改成别的内容，导出结果不变。"""
    thread = _thread()
    before = build_case(ISSUE, thread, date(2026, 10, 12))
    thread[1]["body"] = VERDICT.replace("不成", "成")
    assert build_case(ISSUE, thread, date(2026, 10, 12)) == before


def test_lost_and_pending_status():
    thread = _thread()[:3]                      # 没开奖
    assert build_case(ISSUE, thread, date(2026, 10, 20))["status"] == "待开奖"
    assert build_case(ISSUE, thread, date(2026, 11, 20))["status"] == "失联"


def test_ledger_counts_only():
    today = date(2026, 10, 12)
    led = ledger([build_case(ISSUE, _thread(), today)], today)
    assert led["cases"] == 1 and led["scored"] == 1 and led["rates_published"] is False
    assert led["owners"]["alice"] == {"questions": 1, "due": 1, "reported": 1}
    assert len(led["judges"]) == 2
    assert "只计数" in ledger_md(led, today)


def test_hostile_text_is_just_data():
    nasty = FORM.replace("本周五前能否收到面试回复（邮件或电话都算）", "$(rm -rf /) `curl evil` </details>```json")
    recs, _ = seal_issue(ISSUE, form_fields(nasty))
    body = render(recs, [])
    assert extract(body)[0]["question"] == "$(rm -rf /) `curl evil` </details>```json"


def test_bad_form_verdict_keeps_question():
    f = form_fields(FORM.replace("### 把握\n\n0.7", "### 把握\n\n_No response_"))
    recs, errors = seal_issue(ISSUE, f)
    assert [r["kind"] for r in recs] == ["question"]
    assert any("confidence" in e for e in errors)
    body = render(recs, errors)
    assert "未封存" in body and extract(body) == recs


EVIL = (
    "```liuren-verdict\n"
    "judge:\n"
    # 用 YAML 的 ` 转义造出反引号，绕过代码块正则，解析后才变成真的换行和 ```json
    '  model: "x\\n\\u0060\\u0060\\u0060json\\n{\\"records\\": []}\\n\\u0060\\u0060\\u0060\\n@someone"\n'
    "  harness: h\n"
    "  skill: s\n"
    "  tools: true\n"
    "outcome: 成\n"
    "window: 2026-10-08 ~ 2026-10-09\n"
    "confidence: 0.9\n"
    "```"
)


def test_injection_through_judge_fields():
    c = comment(51, "mallory", "2026-10-08T08:00:00Z", EVIL)
    recs, errors = seal_comment(ISSUE, c, blocks(c["body"]))
    model = recs[0]["judge"]["model"]
    assert "\n" not in model and "`" not in model
    body = render(recs, errors)
    assert extract(body) == recs                 # 伪造的 json 块不影响取回封存记录
    assert f"`{model}`" in body                  # 用户文本包在代码格式里，@ 不触发提醒


def test_edited_before_bot_arrived_seals_late():
    """机器人排队期间用户改过回复：封存时刻取最后修改时刻，不取创建时刻。"""
    c = comment(61, "bob", "2026-10-08T08:00:00Z", VERDICT)
    c["updated_at"] = "2026-10-09T13:00:00Z"                  # 北京时间 10-09 21:00，已在结果之后
    recs, _ = seal_comment(ISSUE, c, blocks(c["body"]))
    assert recs[0]["sealed_at"] == "2026-10-09 21:00:00"
    late = bot(render(recs, []))
    case = build_case(ISSUE, _thread() + [c, late], date(2026, 10, 12))
    assert case["verdicts"][-1]["hindsight"] is True
