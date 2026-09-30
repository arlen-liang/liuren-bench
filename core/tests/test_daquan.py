"""古籍校验集：《六壬大全》（四库全书本，据 zh.wikisource 录文）。

每条注明卷次与原文要点。原文多为"如某日某加某发用"式注例，只写明初传（有的兼及三传、天将），
中末传与其余部分由引擎推出，不在此处断言。书中常把"巳"刻作"己"，已按上下文校正并注明。
"""

import pytest

from liuren_core import cast
from liuren_core.base import GAN, JIAZI, JIGONG, ZHI


def cast_by(day, a, b, night=False):
    """按"a 加 b"（天盘 a 临地盘 b，b 为干时取其寄宫）起课；night 取夜时，否则取昼时。"""
    seat = JIGONG[b] if b in GAN else b
    off = (ZHI.index(a) - ZHI.index(seat)) % 12
    hour = "子" if night else "午"
    return cast(day, ZHI[(ZHI.index(hour) + off) % 12], hour)


def chuan(c):
    return "".join(n["branch"] for n in c["transmissions"])


def jiang(c):
    return "".join(n["general"] for n in c["transmissions"])


# ---- 注例：初传 ----

FAYONG = [
    # 卷, 日, a, b, 原文要点
    ("卷一", "乙未", "申", "午", "乙未日申加午发用 申为乙德"),
    ("卷一", "庚辰", "午", "巳", "庚辰日午加巳发用"),
    ("卷一", "辛巳", "午", "辛", "辛巳日午加辛发用 三传火局"),
    ("卷一", "壬子", "未", "卯", "壬子日未加卯发用 三传木局"),
    ("卷一", "己巳", "寅", "巳", "己巳日寅加己发用作官星 顺贵朱临寅（己为巳之讹，作寅加己则寅非克神、不能发用）"),
    ("卷九", "庚戌", "戌", "卯", "庚戌日戌加卯发用 是地烦杜传"),
    ("卷十", "辛酉", "寅", "辛", "辛酉日寅加辛为用"),
    ("卷十一", "癸丑", "卯", "申", "癸丑日卯加申发用"),
    ("卷十一", "癸亥", "辰", "癸", "癸亥日辰加癸为用 三传辰未戌"),
    ("卷十一", "乙丑", "亥", "丑", "乙丑日亥加丑 初传亥 末传未"),
    ("卷十一", "丙寅", "戌", "寅", "丙寅日戌加寅 初传戌 末传寅"),
    ("卷十二", "丙子", "巳", "子", "丙子日巳加子为用"),
    ("卷十二", "壬子", "巳", "子", "壬子日巳加子为用"),
    ("卷十二", "丁丑", "卯", "申", "丁丑日卯加申为用 夜占"),
]


@pytest.mark.parametrize("vol,day,a,b,note", FAYONG)
def test_fayong(vol, day, a, b, note):
    assert cast_by(day, a, b)["transmissions"][0]["branch"] == a


def test_chuan_given_in_text():
    assert chuan(cast_by("辛巳", "午", "辛")) == "午寅戌"       # 三传火局
    assert chuan(cast_by("壬子", "未", "卯")) == "未亥卯"       # 三传木局
    assert chuan(cast_by("癸亥", "辰", "癸")) == "辰未戌"       # 卷十一 三传辰未戌
    assert chuan(cast_by("乙丑", "亥", "丑"))[::2] == "亥未"     # 卷十一 初传亥 末传未
    assert chuan(cast_by("丙寅", "戌", "寅"))[::2] == "戌寅"     # 卷十一 初传戌 末传寅


# ---- 注例：天将（据此定贵人口诀版本） ----

def test_generals_given_in_text():
    # 卷一、卷十一 壬子日未加卯 夜贵 三传天将皆是勾、（常、贵）
    assert jiang(cast_by("壬子", "未", "卯", night=True)) == "勾常贵"
    # 卷一 辛巳日午加辛 顺逆贵皆贵、勾、常
    assert set(jiang(cast_by("辛巳", "午", "辛"))) == set("贵勾常")
    assert set(jiang(cast_by("辛巳", "午", "辛", night=True))) == set("贵勾常")
    # 卷十一 癸亥日辰加癸 夜天将皆是蛇勾虎
    assert jiang(cast_by("癸亥", "辰", "癸", night=True)) == "蛇勾虎"
    # 卷十二 太阴内战格：壬辰、壬戌日返吟夜占，乃太阴乘巳临亥为用
    for day in ("壬辰", "壬戌"):
        c = cast_by(day, "巳", "亥", night=True)
        assert c["method"]["gate"] == "返吟"
        assert (c["transmissions"][0]["branch"], c["transmissions"][0]["general"]) == ("巳", "阴")
    # 卷十二 天空内战格：丁丑日卯加申为用，夜占
    assert cast_by("丁丑", "卯", "申", night=True)["transmissions"][0]["general"] == "空"
    # 卷一 己巳日寅加巳发用 顺贵朱临寅
    c = cast_by("己巳", "寅", "巳")
    assert c["noble"]["direction"] == "顺" and c["transmissions"][0]["general"] == "雀"
    # 卷十二 庚午日午加庚发用，又午加未暮将，天乙临干（月将午加未时，夜贵）
    c = cast("庚午", "亥", "子")      # 与午加未同一课，取夜时
    assert c["transmissions"][0]["branch"] == "午" and c["lessons"][0]["general"] == "贵"


# ---- 卷七 涉害课例，原书附课盘 ----

def test_shehai_dingmao():
    """正月丁卯日丑时亥将占，二下贼上……亥加丑前行历辰、戊、未、己、戌土位五重，归本家亥位；
    丑加卯前行只历辰中乙木一重。此涉害深者当取亥加丑为用。原书三传：亥朱、酉贵、未阴。"""
    c = cast("丁卯", "亥", "丑")
    assert [k["up"] + k["down"] for k in c["lessons"]] == ["巳丁", "卯巳", "丑卯", "亥丑"]
    assert c["method"]["gate"] == "涉害"
    assert chuan(c) == "亥酉未"
    assert jiang(c) == "雀贵阴"


# ---- 卷一 入手法：课数与名单 ----

def _all720():
    return {(d, off): cast(d, ZHI[off], "子") for d in JIAZI for off in range(12)}


def test_bieze_nine():
    """别责：刚三柔六共九课。戊午戊辰与丙辰，干上皆午；辛丑辛未各二日；丁酉、辛酉各一课。"""
    got = sorted((d, c["lessons"][0]["up"]) for (d, off), c in _all720().items()
                 if c["method"]["gate"] == "别责")
    assert got == sorted([("戊辰", "午"), ("戊午", "午"), ("丙辰", "午"),
                          ("辛丑", "丑"), ("辛丑", "未"), ("辛未", "丑"), ("辛未", "未"),
                          ("丁酉", "巳"), ("辛酉", "酉")])


def test_maoxing_sixteen():
    """补论：凡昴星止十六课。"""
    assert sum(c["method"]["gate"] == "昴星" for c in _all720().values()) == 16


def test_fuyin_gui_day():
    """卷七 伏吟课：以神克日干为初传，取刑为中末传。此六癸日初传丑，中戌，末传未是也。"""
    for d in ("癸丑", "癸卯", "癸巳", "癸未", "癸酉", "癸亥"):
        assert chuan(cast(d, "子", "子")) == "丑戌未", d


def test_fuyin_only_yi_gui_have_ke():
    """伏吟天地皆不动，乙癸有克法不同。"""
    got = sorted({d[0] for d in JIAZI if cast(d, "子", "子")["method"]["name"] == "有克"})
    assert got == ["乙", "癸"]
