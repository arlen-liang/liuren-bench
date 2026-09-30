"""封存：把问题、断语、结果连同服务器时刻、课盘、引擎版本写成封存记录，并渲染成回复。

封存回复以 MARKER 开头，末尾折叠一段 JSON。导出时只认 github-actions[bot] 发的、带 MARKER 的回复。
"""

import json
from datetime import datetime, timedelta, timezone

from liuren_core import cast_at

from .parse import Invalid, question_from_form, verdict_from, verdict_from_form, result_from

MARKER = "<!-- liuren-seal v1 -->"
BJT = timezone(timedelta(hours=8))
CAST_WINDOW = timedelta(hours=24)       # 起课时间须在开 issue 前 24 小时以内
CAST_SLACK = timedelta(minutes=10)      # 允许起课时间比开 issue 略晚（时钟误差）


def gh_time(s: str) -> datetime:
    """GitHub 的 ISO 时间（UTC）→ 带时区 datetime。"""
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def bjt(dt: datetime) -> str:
    return dt.astimezone(BJT).strftime("%Y-%m-%d %H:%M:%S")


def sealed_time(obj: dict) -> datetime:
    """封存时刻取创建与最后更新中较晚者：机器人若排队晚到，而用户在此期间改过内容，
    读到的是改后的内容，时刻也就不能早于那次修改。宁晚勿早。"""
    created = gh_time(obj["created_at"])
    updated = gh_time(obj.get("updated_at") or obj["created_at"])
    return max(created, updated)


def seal_issue(issue: dict, form: dict) -> list[dict]:
    """issue 开立：封存问题，以及表单里附带的断语（若有）。

    问题本身不合格抛 Invalid；断语不合格只作为错误返回，问题照常封存。返回 (记录, 错误)。
    """
    q = question_from_form(form)
    created = gh_time(issue["created_at"])
    cast_time = datetime.strptime(q["time"], "%Y-%m-%d %H:%M").replace(tzinfo=BJT)
    flags = []
    if cast_time < created - CAST_WINDOW:
        flags.append("起课时间早于开 issue 24 小时以上")
    if cast_time > created + CAST_SLACK:
        flags.append("起课时间晚于开 issue")
    chart = cast_at(cast_time.replace(tzinfo=None))
    at = bjt(sealed_time(issue))
    records = [{
        "kind": "question", "sealed_at": at, "source": "issue",
        "owner": issue["user"]["login"], **q,
        "cast": {"time": q["time"], "chart": chart}, "flags": flags,
    }]
    errors = []
    try:
        v = verdict_from_form(form)
    except Invalid as e:
        v, errors = None, [f"表单里的断语：{r}" for r in e.reasons]
    if v:
        records.append({"kind": "verdict", "sealed_at": at, "source": "issue",
                        "author": issue["user"]["login"], **v})
    return records, errors


def seal_comment(issue: dict, comment: dict, parsed) -> tuple[list[dict], list[str]]:
    """回复里的代码块：返回 (封存记录, 未封存原因)。"""
    records, errors = [], []
    at = bjt(sealed_time(comment))
    author = comment["user"]["login"]
    for kind, data in parsed:
        try:
            if isinstance(data, Invalid):
                raise data
            if kind == "liuren-verdict":
                records.append({"kind": "verdict", "sealed_at": at, "source": f"comment:{comment['id']}",
                                "author": author, **verdict_from(data)})
            else:
                r = result_from(data)
                accepted = author == issue["user"]["login"]
                if not accepted:
                    errors.append(f"@{author} 不是提问人，结果只认提问人报的，这条仅作记录")
                records.append({"kind": "result", "sealed_at": at, "source": f"comment:{comment['id']}",
                                "author": author, "accepted": accepted, **r})
        except Invalid as e:
            errors.extend(f"{kind}：{r}" for r in e.reasons)
    return records, errors


# ---- 渲染 ----

def _judge_str(v: dict) -> str:
    j = v["judge"]
    if j.get("human"):
        return f"@{v['author']}（人断）"
    tools = {True: "可用工具", False: "无工具", None: "工具未报"}[j.get("tools")]
    code = lambda x, miss: f"`{x}`" if x else miss      # 用户填的字段一律包进代码格式，@ 不会触发提醒
    s = f"{code(j.get('model'), '模型未报')} @ {code(j.get('harness'), 'harness 未报')} · {code(j.get('skill'), 'skill 未报')} · {tools}"
    return s + ("" if v["complete"] else "（断者信息不全，不进断者的账）")


def _chart_str(chart: dict) -> str:
    t = chart["time"]
    lessons = " ".join(k["up"] + k["down"] for k in chart["lessons"])
    chuan = " ".join(f"{n['branch']}（{n['general']}）" for n in chart["transmissions"])
    m = chart["method"]
    return (f"{t['year']}年 {t['month']}月 {t['day']}日 {t['hour']}时，{t['month_general']}将\n"
            f"四课：{lessons}　课体：{m['gate']}·{m['name']}　三传：{chuan}　旬空：{''.join(chart['void'])}")


def render(records: list[dict], errors: list[str]) -> str:
    lines = [MARKER]
    if records:
        lines.append(f"**已封存** · {records[0]['sealed_at']}（北京时间）")
    for r in records:
        if r["kind"] == "question":
            lines += ["", f"起课：{r['cast']['time']} → {_chart_str(r['cast']['chart'])}",
                      f"截止日：{r['deadline']}　类别：{r['category']}"]
            lines += [f"提示：{f}" for f in r["flags"]]
        elif r["kind"] == "verdict":
            w = f"　应期：{r['window']['from']} ~ {r['window']['to']}" if r["window"] else ""
            lines += ["", f"断语：{_judge_str(r)}", f"　断 **{r['outcome']}**{w}　把握：{r['confidence']}"]
        else:
            d = f"，{r['date']}" if r["date"] else ""
            lines += ["", f"开奖：**{r['outcome']}**{d}" + ("" if r["accepted"] else "（非提问人所报，不计）")]
    if errors:
        lines += ["", "**未封存**：", *[f"- {e}" for e in errors],
                  "", "改好后请重新回复一条（改原帖不会被读取）。格式见 CONTRIBUTING。"]
    if records:
        payload = json.dumps({"records": records}, ensure_ascii=False, indent=1)
        lines += ["", "<details><summary>封存记录（机器读取，勿改）</summary>", "", "```json", payload, "```",
                  "", "</details>"]
    return "\n".join(lines)


def extract(body: str):
    """从封存回复里取回记录。"""
    if not body or not body.startswith(MARKER):
        return None
    # 取最后一个 json 代码块：封存记录总在末尾，JSON 字符串里的换行已被转义，伪造不出这个标记
    i, j = body.rfind("```json\n"), body.rfind("\n```")
    if i < 0 or j <= i:
        return None
    return json.loads(body[i + 8:j])["records"]
