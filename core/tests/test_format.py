"""引擎输出须符合 docs/schema/chart-1.json（liuren-chart/1）。"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import jsonschema

from liuren_core import FORMAT, School, cast, cast_at
from liuren_core.base import JIAZI, ZHI

SCHEMA = json.loads((Path(__file__).resolve().parents[2] / "docs/schema/chart-1.json").read_text("utf-8"))
validator = jsonschema.Draft202012Validator(SCHEMA)


def test_schema_itself_valid():
    jsonschema.Draft202012Validator.check_schema(SCHEMA)


def test_all_720_match_schema():
    for d in JIAZI:
        for off in range(12):
            validator.validate(cast(d, ZHI[off], "子"))


def test_cast_at_matches_schema():
    for k in range(0, 24 * 40, 7):
        validator.validate(cast_at(datetime(2026, 1, 1) + timedelta(hours=k)))
    validator.validate(cast_at(datetime(2026, 10, 8, 14, 20), School(true_solar=True, guiren="甲羊"), longitude=87.6))


def test_format_tag():
    c = cast("甲子", "亥", "午")
    assert c["format"] == FORMAT == "liuren-chart/1"
    assert c["engine"].startswith("liuren-core ")
    json.dumps(c, ensure_ascii=False)     # 可序列化
