"""手工排盘核过的课。注意：这是作者按口诀手算，不是古籍 golden，古籍校验集另建。"""

import pytest

from liuren_core import cast

CASES = [
    # 日, 月将, 占时, 宗门, 课名, 三传
    ("己未", "亥", "午", "比用", "知一", "巳戌卯"),   # 二贼子、巳，阴日取阴神巳
    ("丙寅", "亥", "申", "贼克", "重审", "申亥寅"),   # 一、四课同为申，按上神去重只一贼
    ("乙亥", "亥", "辰", "贼克", "重审", "午丑申"),
    ("庚戌", "亥", "酉", "贼克", "重审", "子寅辰"),
    ("甲子", "亥", "子", "比用", "知一", "子亥戌"),   # 二贼丑、子，阳日取阳神子
]


@pytest.mark.parametrize("day,yj,hour,method,sub,chuan", CASES)
def test_hand(day, yj, hour, method, sub, chuan):
    c = cast(day, yj, hour)
    assert (c["method"]["gate"], c["method"]["name"]) == (method, sub)
    assert "".join(n["branch"] for n in c["transmissions"]) == chuan
