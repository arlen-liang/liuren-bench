# liuren-core

大六壬起课引擎：日干支 + 月将 + 占时 → 天地盘、四课、三传、天将、旬空。纯标准库，没有依赖。

```python
from liuren_core import cast, School

c = cast("己未", "亥", "午")
c["课体"]   # {'宗门': '比用', '课名': '知一'}
[n["支"] for n in c["三传"]]   # ['巳', '戌', '卯']

cast("己未", "亥", "午", School(guiren="甲牛"))   # 换贵人口诀
```

还不会从公历时间直接起课，要自己先换算出日干支、月将和占时。这一层在做。

流派开关见 `liuren_core/school.py`。每条规则的实现选择和待核点见 [docs/rules.md](../docs/rules.md)。在古籍校验集建好之前，除结构性检验外，规则都算草案。

```bash
cd core && uv run --group dev pytest -q
```
