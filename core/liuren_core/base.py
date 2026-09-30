"""干支、五行、生克、刑冲等基础表。只放无流派争议的东西。"""

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

WUXING = {
    **dict.fromkeys("甲乙寅卯", "木"),
    **dict.fromkeys("丙丁巳午", "火"),
    **dict.fromkeys("戊己辰戌丑未", "土"),
    **dict.fromkeys("庚辛申酉", "金"),
    **dict.fromkeys("壬癸亥子", "水"),
}
_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

# 十干寄宫
JIGONG = dict(zip(GAN, "寅辰巳未巳未申戌亥丑"))
# 地支上所寄之干（涉害数克时要算）
GAN_ON_ZHI = {z: [g for g in GAN if JIGONG[g] == z] for z in ZHI}

# 三刑：子卯互刑，寅巳申、丑戌未相刑，辰午酉亥自刑
XING = dict(zip("子卯寅巳申丑戌未辰午酉亥", "卯子巳申寅戌未丑辰午酉亥"))
SELF_XING = set("辰午酉亥")

# 驿马
YIMA = {**dict.fromkeys("申子辰", "寅"), **dict.fromkeys("寅午戌", "申"),
        **dict.fromkeys("巳酉丑", "亥"), **dict.fromkeys("亥卯未", "巳")}

# 天干五合
GAN_HE = dict(zip("甲乙丙丁戊己庚辛壬癸", "己庚辛壬癸甲乙丙丁戊"))

# 三合局，按生旺墓顺序
SANHE = ["申子辰", "亥卯未", "寅午戌", "巳酉丑"]

MENG, ZHONG = set("寅申巳亥"), set("子午卯酉")

GENERALS = "贵蛇雀合勾龙空虎常玄阴后"

JIAZI = [GAN[i % 10] + ZHI[i % 12] for i in range(60)]


def zi(z: str) -> int:
    return ZHI.index(z)


def shift(z: str, n: int) -> str:
    return ZHI[(zi(z) + n) % 12]


def chong(z: str) -> str:
    return shift(z, 6)


def is_yang(c: str) -> bool:
    """干、支的阴阳：甲丙戊庚壬、子寅辰午申戌为阳。"""
    return (GAN.index(c) if c in GAN else ZHI.index(c)) % 2 == 0


def ke(a: str, b: str) -> bool:
    """a 克 b（按五行）。"""
    return _KE[WUXING[a]] == WUXING[b]


def sheng(a: str, b: str) -> bool:
    return _SHENG[WUXING[a]] == WUXING[b]


def liuqin(day_gan: str, z: str) -> str:
    """以日干为我，论六亲。"""
    if WUXING[day_gan] == WUXING[z]:
        return "兄"
    if sheng(day_gan, z):
        return "子"
    if sheng(z, day_gan):
        return "父"
    if ke(day_gan, z):
        return "财"
    return "官"


def xunkong(day: str) -> tuple[str, str]:
    """旬空：本旬十干轮完后余下的两支。"""
    i = JIAZI.index(day)
    start = ZHI.index(JIAZI[i - i % 10][1])
    return ZHI[(start + 10) % 12], ZHI[(start + 11) % 12]
