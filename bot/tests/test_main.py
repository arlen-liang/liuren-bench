"""Action 入口：用假的 GitHub API 走一遍事件处理，确认发出的请求。"""

import io
import json
import urllib.error

import pytest

import liuren_bot.__main__ as main
from test_bot import FORM, ISSUE, RESULT, VERDICT


class FakeAPI:
    def __init__(self, issue, comments=None):
        self.issue = issue
        self.comments = comments or {}
        self.calls = []

    def __call__(self, method, path, body=None):
        self.calls.append((method, path, body))
        if method == "GET" and path.endswith(f"/issues/{self.issue['number']}"):
            return self.issue, {}
        if method == "GET" and "/issues/comments/" in path:
            cid = int(path.rsplit("/", 1)[1])
            if cid not in self.comments:
                raise urllib.error.HTTPError(path, 404, "Not Found", {}, io.BytesIO(b""))
            return self.comments[cid], {}
        if method == "POST":
            return {}, {}
        raise AssertionError(f"意外的请求 {method} {path}")

    def posted(self):
        return [(p, b) for m, p, b in self.calls if m == "POST"]


def run(monkeypatch, tmp_path, api, event_name, event):
    f = tmp_path / "event.json"
    f.write_text(json.dumps(event), "utf-8")
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(f))
    monkeypatch.setenv("GITHUB_EVENT_NAME", event_name)
    monkeypatch.setattr(main, "_req", api)
    main.seal()


def issue_with(labels, body=FORM):
    return {**ISSUE, "body": body, "updated_at": ISSUE["created_at"],
            "labels": [{"name": l} for l in labels]}


def test_opened_seals_and_labels(monkeypatch, tmp_path):
    api = FakeAPI(issue_with(["live-case"]))
    run(monkeypatch, tmp_path, api, "issues", {"action": "opened", "issue": {"number": 7}})
    (p1, b1), (p2, b2) = api.posted()
    assert p1 == "/repos/o/r/issues/7/comments" and "已封存" in b1["body"]
    assert p2 == "/repos/o/r/issues/7/labels" and b2 == {"labels": ["sealed"]}


def test_second_trigger_does_nothing(monkeypatch, tmp_path):
    api = FakeAPI(issue_with(["live-case", "sealed"]))
    run(monkeypatch, tmp_path, api, "issues", {"action": "labeled", "issue": {"number": 7}})
    assert api.posted() == []


def test_invalid_question_labelled_invalid(monkeypatch, tmp_path):
    api = FakeAPI(issue_with(["live-case"], FORM.replace("2026-10-08 14:20", "明天")))
    run(monkeypatch, tmp_path, api, "issues", {"action": "opened", "issue": {"number": 7}})
    (_, b1), (_, b2) = api.posted()
    assert "重新开一个 issue" in b1["body"] and b2 == {"labels": ["invalid"]}


def test_not_live_case_ignored(monkeypatch, tmp_path):
    api = FakeAPI(issue_with([], "随便聊聊，不是实占"))
    run(monkeypatch, tmp_path, api, "issues", {"action": "opened", "issue": {"number": 7}})
    assert api.posted() == []


def test_unlabelled_form_issue_gets_labelled_and_sealed(monkeypatch, tmp_path):
    """普通用户用 gh 开的 issue 标签会被丢掉：机器人按正文结构认出来，自己打标签再封存。"""
    api = FakeAPI(issue_with([]))
    run(monkeypatch, tmp_path, api, "issues", {"action": "opened", "issue": {"number": 7}})
    (p0, b0), (p1, b1), (p2, b2) = api.posted()
    assert b0 == {"labels": ["live-case"]} and "已封存" in b1["body"] and b2 == {"labels": ["sealed"]}


def test_manual_dispatch(monkeypatch, tmp_path):
    api = FakeAPI(issue_with(["live-case"]))
    run(monkeypatch, tmp_path, api, "workflow_dispatch", {"inputs": {"issue": "7"}})
    assert "已封存" in api.posted()[0][1]["body"]


def test_comment_sealed_from_fresh_copy(monkeypatch, tmp_path):
    fresh = {"id": 5, "user": {"login": "alice", "type": "User"}, "created_at": "2026-10-09T12:00:00Z",
             "updated_at": "2026-10-09T12:00:00Z", "body": RESULT}
    api = FakeAPI(issue_with(["live-case", "sealed"]), {5: fresh})
    stale = {"id": 5, "user": {"login": "alice", "type": "User"}, "body": "旧内容"}
    run(monkeypatch, tmp_path, api, "issue_comment", {"issue": {"number": 7}, "comment": stale})
    [(_, b)] = api.posted()
    assert "开奖：**成**" in b["body"]


def test_deleted_comment_skipped(monkeypatch, tmp_path):
    api = FakeAPI(issue_with(["live-case", "sealed"]))
    run(monkeypatch, tmp_path, api, "issue_comment",
        {"issue": {"number": 7}, "comment": {"id": 9, "user": {"login": "bob", "type": "User"}}})
    assert api.posted() == []


def test_comment_on_unsealed_issue(monkeypatch, tmp_path):
    c = {"id": 6, "user": {"login": "bob", "type": "User"}, "created_at": "2026-10-08T08:00:00Z",
         "updated_at": "2026-10-08T08:00:00Z", "body": VERDICT}
    api = FakeAPI(issue_with(["live-case", "invalid"]), {6: c})
    run(monkeypatch, tmp_path, api, "issue_comment", {"issue": {"number": 7}, "comment": c})
    [(_, b)] = api.posted()
    assert "没有封存成功" in b["body"]


def test_plain_chat_comment_ignored(monkeypatch, tmp_path):
    c = {"id": 8, "user": {"login": "bob", "type": "User"}, "created_at": "2026-10-08T08:00:00Z",
         "updated_at": "2026-10-08T08:00:00Z", "body": "楼主加油"}
    api = FakeAPI(issue_with(["live-case", "sealed"]), {8: c})
    run(monkeypatch, tmp_path, api, "issue_comment", {"issue": {"number": 7}, "comment": c})
    assert api.posted() == []
