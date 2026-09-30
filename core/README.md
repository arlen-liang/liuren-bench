# liuren-core

大六壬起课引擎：日干支 + 月将 + 占时 → 天地盘、四课、三传、天将、旬空。纯标准库，没有依赖。

```python
from liuren_core import cast, School

c = cast("己未", "亥", "午")
c["课体"]   # {'宗门': '比用', '课名': '知一'}
[n["支"] for n in c["三传"]]   # ['巳', '戌', '卯']

cast("己未", "亥", "午", School(guiren="甲羊"))   # 换成《星历考原》的贵人口诀
```

还不会从公历时间直接起课，要自己先换算出日干支、月将和占时。这一层在做。

以《六壬大全》为准，流派开关见 `liuren_core/school.py`。每条规则的核对状态和书证见 [docs/rules.md](../docs/rules.md)，古籍校验集在 `tests/test_daquan.py`。

```bash
cd core && uv run --group dev pytest -q
```
