"""课盘成文：给人和 AI 读的文字版。与 web/ui.js 的 chartText 逐字一致（CI 比对）。"""

from .base import ZHI

GENERAL_NAMES = {"贵": "贵人", "蛇": "螣蛇", "雀": "朱雀", "合": "六合", "勾": "勾陈", "龙": "青龙",
                 "空": "天空", "虎": "白虎", "常": "太常", "玄": "玄武", "阴": "太阴", "后": "天后"}
KIN_NAMES = {"父": "父母", "兄": "兄弟", "子": "子孙", "财": "妻财", "官": "官鬼"}
SHEN_NAMES = {"子": "神后", "丑": "大吉", "寅": "功曹", "卯": "太冲", "辰": "天罡", "巳": "太乙",
              "午": "胜光", "未": "小吉", "申": "传送", "酉": "从魁", "戌": "河魁", "亥": "登明"}


def chart_text(c: dict) -> str:
    """须带 time 字段（即按公历时间起的课）。"""
    t = c["time"]
    g = GENERAL_NAMES
    order = [(c["plate"][z], z, c["generals"][z]) for z in ZHI]
    rows = ["  " + "　".join(f"{u}→{d} {g[j]}" for u, d, j in order[i:i + 4]) for i in range(0, 12, 4)]
    names, tn = ["一课", "二课", "三课", "四课"], ["初传", "中传", "末传"]
    return "\n".join([
        f"起课时间：{t['local'][:16]}（北京时间）",
        f"四柱：{t['year']}年 {t['month']}月 {t['day']}日 {t['hour']}时；月将{t['month_general']}（{t['solar_term']['name']}后）",
        f"流派：以《六壬大全》为准，贵人用\"甲戊庚牛羊\"版；{c['noble']['period']}占，贵人{c['noble']['direction']}布",
        "天盘所临与所乘天将（天盘支→临地盘支，乘将）：",
        *rows,
        "四课：" + "　".join(f"{names[i]} {k['up']}加{k['down']}（{g[k['general']]}）" for i, k in enumerate(c["lessons"])),
        f"课体：{c['method']['gate']}·{c['method']['name']}",
        "三传：" + "　".join(
            f"{tn[i]} {n['branch']}（{g[n['general']]}，{KIN_NAMES[n['kin']]}{'，旬空' if n['void'] else ''}）"
            for i, n in enumerate(c["transmissions"])),
        f"旬空：{'、'.join(c['void'])}",
    ])
