"""断法 v0 的原文库：从维基文库《六壬大全》标点本切出九宗门课体（卷七）与十二神、十二将（卷二）条目。

    uv run python tools/gen_duanfa.py

输出 skill/duanfa/daquan.json。原文据维基文库录文（CC BY-SA 4.0），该文件单独按 CC BY-SA 4.0 授权。
课体条目里的示例课盘图（只有干支、将名与空格的行）去掉；每条截到 MAX 字以内，控制提示词长度。
"""

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "skill" / "duanfa" / "daquan.json"
UA = "liuren-bench (github.com/arlen-liang/liuren-bench)"
MAX = {"gate": 1800, "shen": 1000, "jiang": 1000}

SHEN = ["登明亥", "河魁戍", "从魁酉", "传送申", "小吉未", "胜光午", "太乙巳", "天罡辰", "太冲卯", "功曹寅", "大吉丑", "神后子"]
JIANG = {"贵人论": "贵", "螣蛇论": "蛇", "朱雀论": "雀", "六合论": "合", "勾陈论": "勾", "青龙论": "龙",
         "天空论": "空", "白虎论": "虎", "太常论": "常", "玄武论": "玄", "太阴论": "阴", "天后论": "后"}
GATES = {"元首课": "贼克·元首", "重审课": "贼克·重审", "知一课": "比用", "遥克课": "遥克", "昴星课": "昴星",
         "别责课": "别责", "八专课": "八专", "伏吟课": "伏吟", "返吟课": "返吟"}
DIAGRAM = re.compile(r"^[\s子丑寅卯辰巳午未申酉戌亥甲乙丙丁戊己庚辛壬癸贵蛇雀朱合六勾龙青空虎白常玄元阴后天]*$")


def fetch(title: str) -> str:
    q = urllib.parse.urlencode({"title": title, "action": "raw"})
    req = urllib.request.Request(f"https://zh.wikisource.org/w/index.php?{q}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        text = r.read().decode("utf-8")
    time.sleep(2)
    return text


def clean(text: str) -> str:
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r"</?onlyinclude>|<[^>]+>", "", text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", text)
    return text


def lines_of(text: str) -> list[str]:
    return [l.strip() for l in clean(text).splitlines()]


def cut(lines: list[str], heads: list[str], stop: set[str]) -> dict:
    """按标题行切段：从某标题行起，到下一个标题行或停止行止。"""
    out, key, buf = {}, None, []
    for l in lines:
        if l in heads or l in stop:
            if key:
                out[key] = buf
            key, buf = (l if l in heads else None), []
        elif key and l:
            buf.append(l)
    if key:
        out[key] = buf
    return out


def body(buf: list[str], limit: int) -> str:
    kept = [l for l in buf if not DIAGRAM.match(l)]
    text = "\n".join(kept)
    return text if len(text) <= limit else text[:limit].rstrip() + "……（下略）"


def main():
    v2, v7 = lines_of(fetch("六壬大全/2")), lines_of(fetch("六壬大全/7"))

    shen = cut(v2, SHEN, {"天将总论"})
    jiang = cut(v2, list(JIANG), {"六壬大全卷二终"})
    gates = cut(v7, list(GATES), {"三光课"})

    # 涉害无独立标题，夹在知一课之后：从"凡课有二上克下或二下克上"起，到"遥克课"止
    full7 = "\n".join(v7)
    i = full7.find("凡课有二上克下或二下克上")
    j = full7.find("\n遥克课\n", i)
    shehai = full7[i:j].splitlines() if i >= 0 and j > i else []
    if "知一课" in gates and shehai:
        k = "\n".join(gates["知一课"]).find("凡课有二上克下或二下克上")
        if k >= 0:
            gates["知一课"] = "\n".join(gates["知一课"])[:k].splitlines()

    data = {
        "source": "《六壬大全》四库全书本，据维基文库标点录文（https://zh.wikisource.org/wiki/六壬大全），CC BY-SA 4.0",
        "gate": {GATES[h]: body(b, MAX["gate"]) for h, b in gates.items()},
        "shen": {h[-1].replace("戍", "戌"): body(b, MAX["shen"]) for h, b in shen.items()},
        "jiang": {JIANG[h]: body(b, MAX["jiang"]) for h, b in jiang.items()},
    }
    data["gate"]["涉害"] = body(shehai, MAX["gate"])
    missing = ([g for g in list(GATES.values()) + ["涉害"] if not data["gate"].get(g)]
               + [s for s in "子丑寅卯辰巳午未申酉戌亥" if not data["shen"].get(s)]
               + [j for j in JIANG.values() if not data["jiang"].get(j)])
    if missing:
        raise SystemExit(f"切分失败，缺：{missing}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(f"{OUT}  {len(OUT.read_bytes()) // 1024} KB")


if __name__ == "__main__":
    main()
