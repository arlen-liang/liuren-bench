"""解析实占 issue：表单正文、回复里的 liuren-verdict / liuren-result 代码块。

所有输入都是不可信的用户文本：只做解析与校验，出错收集成人能读的中文原因，不抛给调用方。
"""

import re
from datetime import date, datetime

import yaml

# 表单标题 → 字段名（与 .github/ISSUE_TEMPLATE/live.yml 的 id 一致）
LABELS = {
    "确认": "consent",
    "起课时间": "time",
    "占事": "question",
    "类别": "category",
    "截止日": "deadline",
    "谁断的": "judge_type",
    "模型（AI 断的必填）": "model",
    "harness（AI 断的必填）": "harness",
    "skill 或提示词（AI 断的必填）": "skill",
    "能否调用工具（AI 断的必填）": "tools",
    "断：成还是不成": "outcome",
    "应期（断\"成\"时填）": "window",
    "把握": "confidence",
    "依据（可选）": "basis",
}
CATEGORIES = ["求职", "工作", "财运", "感情", "健康（仅限本人）", "出行", "失物", "考试", "其他"]
NO_RESPONSE = {"", "_No response_", "不在这里填", "不适用"}
MAX_TEXT = 4000


def oneline(x, limit: int = 200) -> str:
    """用户填的短字段：压成单行、去掉反引号，防止混进 markdown 结构。"""
    return " ".join(str(x or "").replace("`", "'").split())[:limit]


class Invalid(Exception):
    """带一组中文原因的校验失败。"""

    def __init__(self, reasons):
        super().__init__("；".join(reasons))
        self.reasons = reasons


def looks_like_live(body: str) -> bool:
    """没带标签的 issue 是否为实占表单：普通用户用 API / gh 开 issue 时，标签会被 GitHub 悄悄丢掉。"""
    return all(f"### {h}" in (body or "") for h in ("起课时间", "占事", "截止日"))


def form_fields(body: str) -> dict:
    """把 issue 表单渲染出的 markdown 拆回字段。未识别的标题忽略。"""
    fields, key, buf = {}, None, []
    for line in (body or "").splitlines():
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            if key:
                fields[key] = "\n".join(buf).strip()
            key, buf = LABELS.get(m.group(1)), []
        elif key:
            buf.append(line)
    if key:
        fields[key] = "\n".join(buf).strip()
    return {k: ("" if v in NO_RESPONSE else v) for k, v in fields.items()}


def _parse_time(s: str) -> datetime:
    return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M")


def _parse_date(s) -> date:
    if isinstance(s, date):
        return s
    return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()


def _parse_window(s):
    if s in (None, ""):
        return None
    if isinstance(s, dict):
        a, b = s.get("from"), s.get("to")
    else:
        parts = re.split(r"\s*[~～至到]\s*", str(s).strip())
        if len(parts) != 2:
            raise ValueError
        a, b = parts
    a, b = _parse_date(a), _parse_date(b)
    if b < a:
        raise ValueError
    return {"from": a.isoformat(), "to": b.isoformat()}


def _parse_confidence(x):
    c = float(x)
    if not 0.5 <= c <= 1.0:
        raise ValueError
    return round(c, 2)


def question_from_form(f: dict) -> dict:
    """校验下注表单的问题部分。"""
    reasons = []
    if f.get("consent", "").count("[X]") + f.get("consent", "").count("[x]") < 4:
        reasons.append("四项确认没有全部勾选")
    try:
        t = _parse_time(f.get("time", ""))
    except ValueError:
        reasons.append("起课时间格式不对，应为 2026-10-08 14:20")
        t = None
    q = f.get("question", "").strip()
    if not q:
        reasons.append("占事是空的")
    cat = f.get("category", "")
    if cat not in CATEGORIES:
        reasons.append(f"类别不在列表里：{cat}")
    try:
        dl = _parse_date(f.get("deadline", ""))
    except ValueError:
        reasons.append("截止日格式不对，应为 2026-10-10")
        dl = None
    if t and dl and dl < t.date():
        reasons.append("截止日早于起课时间")
    if reasons:
        raise Invalid(reasons)
    return {"time": t.strftime("%Y-%m-%d %H:%M"), "question": q[:MAX_TEXT],
            "category": cat, "deadline": dl.isoformat()}


def _judge(raw: dict, reasons: list) -> tuple[dict, bool]:
    """返回 (judge, complete)。complete=False 的 AI 断语照收但不进断者的账。"""
    if not isinstance(raw, dict):
        reasons.append("judge 要么写 human: true，要么写 model / harness / skill / tools 四项")
        return {}, False
    if raw.get("human") is True:
        return {"human": True}, True
    judge = {k: oneline(raw.get(k)) for k in ("model", "harness", "skill")}
    tools = raw.get("tools")
    if isinstance(tools, str):
        tools = {"能（可跑代码或查资料）": True, "能": True, "不能": False}.get(tools)
    judge["tools"] = tools if isinstance(tools, bool) else None
    complete = all(judge[k] for k in ("model", "harness", "skill")) and judge["tools"] is not None
    return judge, complete


def verdict_from(raw: dict) -> dict:
    """校验一条断语（来自表单或 liuren-verdict 代码块）。"""
    reasons = []
    judge, complete = _judge(raw.get("judge"), reasons)
    outcome = str(raw.get("outcome", "")).strip()
    if outcome not in ("成", "不成"):
        reasons.append("outcome 只能是 成 或 不成")
    try:
        window = _parse_window(raw.get("window"))
    except ValueError:
        reasons.append("window 格式不对，应为 2026-10-08 ~ 2026-10-09")
        window = None
    try:
        conf = _parse_confidence(raw.get("confidence"))
    except (TypeError, ValueError):
        reasons.append("confidence 应为 0.5 到 1.0 之间的数")
        conf = None
    if reasons:
        raise Invalid(reasons)
    basis = str(raw.get("basis") or "").strip()[:MAX_TEXT]
    return {"judge": judge, "complete": complete, "outcome": outcome,
            "window": window if outcome == "成" else None, "confidence": conf, "basis": basis}


def verdict_from_form(f: dict):
    """表单里没填断语时返回 None。"""
    jt = f.get("judge_type", "")
    if not jt and not f.get("outcome"):
        return None
    if jt == "我自己":
        judge = {"human": True}
    else:
        judge = {"model": f.get("model"), "harness": f.get("harness"), "skill": f.get("skill"),
                 "tools": f.get("tools") or None}
    return verdict_from({"judge": judge, "outcome": f.get("outcome"), "window": f.get("window"),
                         "confidence": f.get("confidence"), "basis": f.get("basis")})


def looks_like_bare_block(body: str) -> str | None:
    """回复里有断语或开奖的字段、却没有代码块标记（从 AI 的回答里复制时，``` 那两行常被丢掉）。
    返回应补的代码块名，不像就返回 None。"""
    text = body or ""
    if BLOCK.search(text) or not re.search(r"^\s*outcome\s*:", text, re.M):
        return None
    return "liuren-verdict" if re.search(r"^\s*(judge|confidence)\s*:", text, re.M) else "liuren-result"


BLOCK = re.compile(r"```(liuren-verdict|liuren-result)[ \t]*\n(.*?)```", re.S)


def blocks(body: str) -> list[tuple[str, dict]]:
    """取出回复里的代码块。YAML 用 safe_load；解析失败的块以 Invalid 形式返回。"""
    out = []
    for kind, text in BLOCK.findall(body or "")[:5]:
        try:
            data = yaml.safe_load(text[:MAX_TEXT * 2])
            if not isinstance(data, dict):
                raise ValueError
            out.append((kind, data))
        except (yaml.YAMLError, ValueError):
            out.append((kind, Invalid([f"{kind} 代码块不是合法的 YAML"])))
    return out


def result_from(raw: dict) -> dict:
    reasons = []
    outcome = str(raw.get("outcome", "")).strip()
    if outcome not in ("成", "不成"):
        reasons.append("outcome 只能是 成 或 不成")
    d = raw.get("date")
    try:
        d = _parse_date(d).isoformat() if d not in (None, "") else None
    except ValueError:
        reasons.append("date 格式不对，应为 2026-10-09")
    if outcome == "成" and not d:
        reasons.append("成的话要写 date：哪天成的")
    if reasons:
        raise Invalid(reasons)
    return {"outcome": outcome, "date": d, "note": str(raw.get("note") or "").strip()[:MAX_TEXT]}
