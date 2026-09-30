"""命令行：python -m liuren_core cast [--time "2026-10-08 14:20"] [--json]

不给 --time 即取现在（北京时间）。默认输出课盘文字，--json 输出 liuren-chart/1。
"""

import argparse
import json
from datetime import datetime, timedelta, timezone

from . import cast_at
from .text import chart_text

BJT = timezone(timedelta(hours=8))


def main():
    ap = argparse.ArgumentParser(prog="python -m liuren_core")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cast", help="按公历时间起课")
    c.add_argument("--time", help='北京时间，如 "2026-10-08 14:20"；不给即现在')
    c.add_argument("--json", action="store_true", help="输出 liuren-chart/1 JSON")
    a = ap.parse_args()
    t = (datetime.strptime(a.time, "%Y-%m-%d %H:%M") if a.time
         else datetime.now(BJT).replace(tzinfo=None, second=0, microsecond=0))
    chart = cast_at(t)
    print(json.dumps(chart, ensure_ascii=False, indent=1) if a.json else chart_text(chart))


if __name__ == "__main__":
    main()
