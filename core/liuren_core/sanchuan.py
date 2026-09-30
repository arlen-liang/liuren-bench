"""九宗门取三传。

判定顺序：伏吟、返吟按天地盘结构先判；其余依 贼克 → 比用 → 涉害 → 八专 → 遥克 → 别责 → 昴星。
每条规则都按通行口诀实现，出处与细节待 M1 古籍校验集逐条核定，核定前视为草案。
"""

from dataclasses import dataclass

from .base import (GAN_HE, GAN_ON_ZHI, JIGONG, MENG, SANHE, SELF_XING, XING, YIMA, ZHONG,
                   chong, is_yang, ke, shift, zi)
from .school import School


@dataclass(frozen=True)
class Ke:
    up: str     # 上神（天盘）
    down: str   # 下：一课为日干，其余为地支
    seat: str   # 下所在地盘位：一课为日干寄宫，其余同 down


@dataclass(frozen=True)
class Result:
    method: str        # 九宗门之一
    sub: str           # 课名细分，如 重审、元首、知一、见机
    chuan: tuple       # (初, 中, 末)


class Pan:
    """天地盘。offset = 月将 − 占时，天盘某支临于地盘 (该支 − offset)。"""

    def __init__(self, yuejiang: str, hour: str):
        self.offset = (zi(yuejiang) - zi(hour)) % 12

    def up(self, z: str) -> str:
        """地盘 z 之上神。"""
        return shift(z, self.offset)

    def down(self, z: str) -> str:
        """天盘 z 所临之地盘。"""
        return shift(z, -self.offset)


def sike(day: str, pan: Pan) -> list[Ke]:
    gan, zhi = day
    j = JIGONG[gan]
    k1 = Ke(pan.up(j), gan, j)
    k2 = Ke(pan.up(k1.up), k1.up, k1.up)
    k3 = Ke(pan.up(zhi), zhi, zhi)
    k4 = Ke(pan.up(k3.up), k3.up, k3.up)
    return [k1, k2, k3, k4]


def _uniq(xs):
    return list(dict.fromkeys(xs))


def _chain(pan: Pan, chu: str) -> tuple:
    zhong = pan.up(chu)
    return chu, zhong, pan.up(zhong)


# ---- 涉害 ----

def _shehai_depth(c: str, pan: Pan, being_ke: bool, school: School) -> int:
    """从所临地盘顺数至本家（不含本家），数历经之克。

    being_ke=True：候选被下所克（贼），数克它的；False：候选克下，数它所克的。
    """
    n = 0
    p = pan.down(c)
    for k in range(pan.offset):
        q = shift(p, k)
        items = [q] + (GAN_ON_ZHI[q] if school.shehai_count_gan else [])
        n += sum(ke(x, c) if being_ke else ke(c, x) for x in items)
    return n


def _shehai(cands, pan: Pan, ks, day, being_ke: bool, school: School):
    if school.shehai == "count":
        depth = {c: _shehai_depth(c, pan, being_ke, school) for c in cands}
        top = max(depth.values())
        tied = [c for c in cands if depth[c] == top]
        if len(tied) == 1:
            return tied[0], "涉害"
    else:
        tied = list(cands)
    meng = [c for c in tied if pan.down(c) in MENG]
    if len(meng) == 1:
        return meng[0], "见机"
    if not meng:
        zhong = [c for c in tied if pan.down(c) in ZHONG]
        if len(zhong) == 1:
            return zhong[0], "察微"
    # 复等：阳日取干上神，阴日取支上神
    return (ks[0].up if is_yang(day[0]) else ks[2].up), "复等"


def _pick(cands, pan, ks, day, being_ke, school, single_sub):
    """一个直取；多个先比用，比不出再涉害。返回 (初传, method, sub)。"""
    if len(cands) == 1:
        return cands[0], None, single_sub
    bi = [c for c in cands if is_yang(c) == is_yang(day[0])]
    if len(bi) == 1:
        return bi[0], "比用", "知一"
    chu, sub = _shehai(bi or cands, pan, ks, day, being_ke, school)
    return chu, "涉害", sub


# ---- 伏吟、返吟 ----

def _fuyin(day, pan, ks) -> Result:
    """伏吟：有克取克；无克阳日取干上神、阴日取支上神。中传取初之刑，末传取中之刑；
    初传自刑则中传取干支上神中的另一个；中传自刑则末传取中之冲（杜传）。"""
    gan, zhi = day
    j = JIGONG[gan]
    if ke(gan, j) or ke(j, gan):
        chu, sub = j, "有克"
    else:
        chu = j if is_yang(gan) else zhi
        sub = "自任" if is_yang(gan) else "自信"
    if chu in SELF_XING:
        zhong = zhi if chu == j else j
    else:
        zhong = XING[chu]
    if zhong in SELF_XING:
        mo, sub = chong(zhong), "杜传"
    else:
        mo = XING[zhong]
    return Result("伏吟", sub, (chu, zhong, mo))


def _jinglan(day, pan) -> Result:
    """返吟无克（井栏射）：初取支之驿马，中取支上神，末取干上神。"""
    gan, zhi = day
    return Result("返吟", "井栏射", (YIMA[zhi], pan.up(zhi), pan.up(JIGONG[gan])))


# ---- 主入口 ----

def derive(day: str, pan: Pan, school: School) -> Result:
    gan, zhi = day
    ks = sike(day, pan)
    if pan.offset == 0:
        return _fuyin(day, pan, ks)

    zei = _uniq(k.up for k in ks if ke(k.down, k.up))
    kes = _uniq(k.up for k in ks if ke(k.up, k.down))
    if zei or kes:
        cands, being_ke = (zei, True) if zei else (kes, False)
        chu, method, sub = _pick(cands, pan, ks, day, being_ke, school,
                                 "重审" if zei else "元首")
        method = method or "贼克"
        if pan.offset == 6:
            sub = f"{method}·{sub}"
            method = "返吟"
        return Result(method, sub, _chain(pan, chu))

    if pan.offset == 6:
        return _jinglan(day, pan)

    j = JIGONG[gan]
    ganshang = pan.up(j)

    # 八专：干支同位，两课无克
    if j == zhi:
        if is_yang(gan):
            chu = shift(ganshang, 2)
        else:
            chu = shift(ks[3].up, -2)
        return Result("八专", "独足" if chu == ganshang else "八专", (chu, ganshang, ganshang))

    # 遥克：先取神克日（蒿矢），无则日克神（弹射）
    ups = _uniq(k.up for k in ks[1:])
    shen_ke_ri = [u for u in ups if ke(u, gan)]
    ri_ke_shen = [u for u in ups if ke(gan, u)]
    if shen_ke_ri or ri_ke_shen:
        cands, sub, being_ke = ((shen_ke_ri, "蒿矢", False) if shen_ke_ri
                                else (ri_ke_shen, "弹射", True))
        chu, _, _ = _pick(cands, pan, ks, day, being_ke, school, sub)
        return Result("遥克", sub, _chain(pan, chu))

    # 别责：四课不备
    if len({(k.up, k.seat) for k in ks}) < 4:
        if is_yang(gan):
            chu = pan.up(JIGONG[GAN_HE[gan]])
        else:
            group = next(g for g in SANHE if zhi in g)
            chu = group[(group.index(zhi) + 1) % 3]
        return Result("别责", "别责", (chu, ganshang, ganshang))

    # 昴星
    if is_yang(gan):
        return Result("昴星", "虎视", (pan.up("酉"), pan.up(zhi), ganshang))
    return Result("昴星", "冬蛇掩目", (pan.down("酉"), ganshang, pan.up(zhi)))
