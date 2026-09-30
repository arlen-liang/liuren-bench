# liuren-core

大六壬起课引擎：公历时间（或日干支 + 月将 + 占时）→ 天地盘、四课、三传、天将、旬空。纯标准库，没有依赖。

```python
from datetime import datetime
from liuren_core import cast, cast_at, School

c = cast_at(datetime(2026, 10, 8, 14, 20))   # 无时区即北京时间
c["time"]            # 年、月、日干支，占时，月将，所依中气及其时刻
c["method"]          # {'gate': '贼克', 'name': '重审'}
c["transmissions"]   # 三传

cast("己未", "亥", "午")                      # 已知日干支、月将、占时时直接起
cast_at(datetime(2026, 10, 8, 14, 20), School(true_solar=True), longitude=87.6)   # 用真太阳时
```

节气时刻查 `liuren_core/data/jieqi.json`（1900–2100，精确到秒），由 `tools/gen_jieqi.py` 用 pyephem 生成；运行时不需要 pyephem。

以《六壬大全》为准，流派开关见 `liuren_core/school.py`，输出格式见 [docs/format.md](../docs/format.md)（liuren-chart/1）。每条规则的核对状态和书证见 [docs/rules.md](../docs/rules.md)，古籍校验集在 `tests/test_daquan.py`。

```bash
cd core && uv run --group dev pytest -q
```
