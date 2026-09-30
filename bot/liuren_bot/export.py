"""导出：从 issue 的封存回复汇总出 liuren-live/1 数据集。

只信 github-actions[bot] 发的封存回复；issue 原帖、用户回复的现状一概不读，
所以原帖事后被改、回复被删，都不影响导出结果。
"""

from datetime import date, datetime, timedelta

from .seal import extract

FORMAT = "liuren-live/1"
BOT = "github-actions[bot]"
LOST_AFTER = timedelta(days=30)


def _judge_key(v: dict) -> str:
    j = v["judge"]
    if j.get("human"):
        return f"human:{v['author']}"
    return f"{j['model']} | {j['harness']} | {j['skill']} | tools={j['tools']}"


def build_case(issue: dict, comments: list[dict], today: date) -> dict | None:
    records = []
    for c in comments:
        if c["user"]["login"] == BOT:
            recs = extract(c["body"])
            if recs:
                records.extend(recs)
    questions = [r for r in records if r["kind"] == "question"]
    if not questions:
        return None
    q = questions[0]
    results = [r for r in records if r["kind"] == "result" and r["accepted"]]
    result = results[-1] if results else None
    deadline = date.fromisoformat(q["deadline"])

    verdicts = []
    for r in records:
        if r["kind"] != "verdict":
            continue
        sealed = datetime.strptime(r["sealed_at"], "%Y-%m-%d %H:%M:%S")
        late = sealed.date() > deadline
        if result:
            late = late or r["sealed_at"] > result["sealed_at"]
            if result["date"]:
                late = late or sealed.date() > date.fromisoformat(result["date"])
        verdicts.append({**{k: v for k, v in r.items() if k != "kind"},
                         "judge_key": _judge_key(r), "self_reported": True, "hindsight": late,
                         "falsifiable": True})

    if result:
        status = "已开奖"
    elif today > deadline + LOST_AFTER:
        status = "失联"
    else:
        status = "待开奖"

    return {
        "format": FORMAT,
        "id": issue["number"],
        "url": issue["html_url"],
        "owner": q["owner"],
        "question": q["question"],
        "category": q["category"],
        "deadline": q["deadline"],
        "sealed_at": q["sealed_at"],
        "cast": q["cast"],
        "flags": q["flags"],
        "verdicts": verdicts,
        "result": {k: v for k, v in result.items() if k not in ("kind", "accepted")} if result else None,
        "status": status,
    }


def ledger(cases: list[dict], today: date) -> dict:
    """账本 v0：只计数，不算命中率（回填满 30 条前不出比率）。"""
    judges, owners = {}, {}
    for c in cases:
        o = owners.setdefault(c["owner"], {"questions": 0, "due": 0, "reported": 0})
        o["questions"] += 1
        if today > date.fromisoformat(c["deadline"]):
            o["due"] += 1
            o["reported"] += c["result"] is not None
        for v in c["verdicts"]:
            if not v["complete"] or v["hindsight"]:
                continue
            j = judges.setdefault(v["judge_key"], {"calls": 0, "scored": 0})
            j["calls"] += 1
            j["scored"] += c["result"] is not None
    scored = sum(c["result"] is not None for c in cases)
    return {"cases": len(cases), "scored": scored, "judges": judges, "owners": owners,
            "rates_published": scored >= 30}


def ledger_md(led: dict, today: date) -> str:
    lines = [f"# 实占账本（{today.isoformat()} 导出）", "",
             f"案例 {led['cases']} 个，已开奖 {led['scored']} 个。"
             + ("" if led["rates_published"] else "回填满 30 条之前只计数，不算命中率。"), "",
             "AI 断者的信息全部自报，未经验证。", "", "## 断者", "", "| 断者 | 下注 | 已开奖 |", "|---|---|---|"]
    for k, v in sorted(led["judges"].items(), key=lambda x: -x[1]["calls"]):
        lines.append(f"| {k} | {v['calls']} | {v['scored']} |")
    lines += ["", "## 提问人", "", "| 提问人 | 问题 | 已过截止日 | 已开奖 |", "|---|---|---|---|"]
    for k, v in sorted(led["owners"].items(), key=lambda x: -x[1]["questions"]):
        lines.append(f"| @{k} | {v['questions']} | {v['due']} | {v['reported']} |")
    return "\n".join(lines) + "\n"
