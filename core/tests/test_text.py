"""课盘成文与命令行。"""

import subprocess
import sys
from datetime import datetime

from liuren_core import cast_at
from liuren_core.text import chart_text

# issue #2 的课盘文字（已交给第二位断者），与 web/test/ui.test.mjs 里的同一份
ISSUE2 = """起课时间：2026-09-30 22:52（北京时间）
四柱：丙午年 丁酉月 丁未日 亥时；月将辰（秋分后）
流派：以《六壬大全》为准，贵人用"甲戊庚牛羊"版；夜占，贵人顺布
天盘所临与所乘天将（天盘支→临地盘支，乘将）：
  巳→子 太常　午→丑 玄武　未→寅 太阴　申→卯 天后
  酉→辰 贵人　戌→巳 螣蛇　亥→午 朱雀　子→未 六合
  丑→申 勾陈　寅→酉 青龙　卯→戌 天空　辰→亥 白虎
四课：一课 子加丁（六合）　二课 巳加子（太常）　三课 子加未（六合）　四课 巳加子（太常）
课体：比用·知一
三传：初传 巳（太常，兄弟）　中传 戌（螣蛇，子孙）　末传 卯（天空，父母，旬空）
旬空：寅、卯"""


def test_issue2_text():
    assert chart_text(cast_at(datetime(2026, 9, 30, 22, 52))) == ISSUE2


def test_cli():
    out = subprocess.run([sys.executable, "-m", "liuren_core", "cast", "--time", "2026-09-30 22:52"],
                         capture_output=True, text=True, check=True).stdout
    assert out.strip() == ISSUE2
    js = subprocess.run([sys.executable, "-m", "liuren_core", "cast", "--json"], capture_output=True, text=True, check=True)
    assert '"format": "liuren-chart/1"' in js.stdout
