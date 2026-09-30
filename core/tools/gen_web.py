"""为网页版生成数据：web/data/lessons.json（720 课的课体与三传）、web/data/jieqi.json（节气时刻）。

    uv run python tools/gen_web.py            # 生成
    uv run python tools/gen_web.py --check    # 只检查已提交的文件是否与引擎一致（CI 用）

网页只查这两张表，九宗门不在 JS 里重写，免得两套实现分叉。
表按默认流派生成；涉害开关不同，三传会变，网页只支持默认流派。
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from liuren_core import cast
from liuren_core.base import JIAZI, ZHI
from liuren_core.timing import _table

WEB = Path(__file__).resolve().parents[2] / "web" / "data"


def lessons() -> dict:
    """{日干支: [[宗门, 课名, 三传], … 相对位 0–11]}，相对位 = 月将 − 占时。"""
    out = {}
    for d in JIAZI:
        row = []
        for off in range(12):
            c = cast(d, ZHI[off], "子")
            row.append([c["method"]["gate"], c["method"]["name"], "".join(n["branch"] for n in c["transmissions"])])
        out[d] = row
    return out


def jieqi() -> dict:
    """{first: 首个节气名, t: [UTC 秒, …]}：节气按固定顺序循环，只存时刻。"""
    ts, ns = _table()
    return {"first": ns[0], "t": [int(t.replace(tzinfo=timezone.utc).timestamp()) for t in ts]}


def main():
    files = {"lessons.json": lessons(), "jieqi.json": jieqi()}
    check = "--check" in sys.argv
    bad = []
    for name, data in files.items():
        text = json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
        p = WEB / name
        if check:
            if not p.exists() or p.read_text("utf-8") != text:
                bad.append(name)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, "utf-8")
            print(f"{p}  {len(text.encode()) // 1024} KB")
    if bad:
        sys.exit(f"web/data 与引擎不一致，请运行 core/tools/gen_web.py：{bad}")


if __name__ == "__main__":
    main()
