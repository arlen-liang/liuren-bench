"""GitHub Action 入口。

    python -m liuren_bot seal            # issues.opened / issue_comment.created
    python -m liuren_bot export OUT_DIR  # 定时导出

事件内容一律从 $GITHUB_EVENT_PATH 读 JSON，不经 shell。
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .export import build_case, ledger, ledger_md
from .parse import Invalid, blocks, form_fields
from .seal import render, seal_comment, seal_issue

API = "https://api.github.com"
BJT = timezone(timedelta(hours=8))


def _req(method: str, path: str, body=None):
    req = urllib.request.Request(
        API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                 "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or "null"), r.headers


def _paged(path: str):
    page = 1
    while True:
        sep = "&" if "?" in path else "?"
        data, _ = _req("GET", f"{path}{sep}per_page=100&page={page}")
        if not data:
            return
        yield from data
        page += 1


def seal():
    repo = os.environ["GITHUB_REPOSITORY"]
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text("utf-8"))
    n = event["issue"]["number"]
    # 事件里的内容可能已过时（机器人排队期间用户可能改过），一律重新拉取
    issue, _ = _req("GET", f"/repos/{repo}/issues/{n}")
    labels = {l["name"] for l in issue.get("labels", [])}
    if "live-case" not in labels or issue.get("pull_request"):
        return

    if os.environ["GITHUB_EVENT_NAME"] == "issues":
        if labels & {"sealed", "invalid"}:          # opened 与 labeled 可能各触发一次，只封一次
            return
        try:
            records, errors = seal_issue(issue, form_fields(issue["body"]))
            text, add = render(records, errors), ["sealed"]
        except Invalid as e:
            text = render([], e.reasons).replace("改好后请重新回复一条（改原帖不会被读取）", "改好后请重新开一个 issue")
            add = ["invalid"]
    else:
        if event["comment"]["user"].get("type") == "Bot":
            return
        try:
            comment, _ = _req("GET", f"/repos/{repo}/issues/comments/{event['comment']['id']}")
        except urllib.error.HTTPError as e:
            if e.code == 404:                        # 机器人到之前回复已被删掉
                return
            raise
        parsed = blocks(comment["body"])
        if not parsed:
            return
        if "sealed" not in labels:
            text, add = render([], ["这个 issue 的问题本身没有封存成功，请重新开一个 issue"]), []
        else:
            records, errors = seal_comment(issue, comment, parsed)
            text, add = render(records, errors), []

    _req("POST", f"/repos/{repo}/issues/{n}/comments", {"body": text})
    if add:
        _req("POST", f"/repos/{repo}/issues/{n}/labels", {"labels": add})


def export(out_dir: str):
    repo = os.environ["GITHUB_REPOSITORY"]
    today = datetime.now(BJT).date()
    out = Path(out_dir)
    (out / "cases").mkdir(parents=True, exist_ok=True)
    cases = []
    for issue in _paged(f"/repos/{repo}/issues?labels=live-case&state=all"):
        if issue.get("pull_request"):
            continue
        comments = list(_paged(f"/repos/{repo}/issues/{issue['number']}/comments"))
        case = build_case(issue, comments, today)
        if case:
            cases.append(case)
            (out / "cases" / f"{case['id']}.json").write_text(
                json.dumps(case, ensure_ascii=False, indent=1), "utf-8")
    cases.sort(key=lambda c: c["id"])
    led = ledger(cases, today)
    (out / "live.json").write_text(json.dumps(cases, ensure_ascii=False), "utf-8")
    (out / "ledger.json").write_text(json.dumps(led, ensure_ascii=False, indent=1), "utf-8")
    (out / "LEDGER.md").write_text(ledger_md(led, today), "utf-8")
    (out / "README.md").write_text(
        "# liuren-bench 实占数据集\n\n由 main 分支的导出 Action 每日生成，本分支不留历史。"
        "格式 liuren-live/1，见 main 分支 docs/format.md。数据以 CC-BY-4.0 发布。\n", "utf-8")
    print(f"导出 {len(cases)} 个案例")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "seal":
        seal()
    elif cmd == "export":
        export(sys.argv[2])
    else:
        sys.exit("用法：python -m liuren_bot seal | export OUT_DIR")
