# 课盘数据格式 liuren-chart/1

引擎的输出、实占库封存的课盘、起课轨的标准答案，用的都是这一份格式。JSON，键名英文，值用中文（干支、将名、课名）。机读校验用 [schema/chart-1.json](schema/chart-1.json)。

## 长什么样

```json
{
  "format": "liuren-chart/1",
  "engine": "liuren-core 0.1.0",
  "input": {"day": "乙卯", "month_general": "辰", "hour": "未"},
  "school": {"guiren": "甲牛", "daynight": "卯酉", "shehai": "count",
             "shehai_count_gan": true, "zishi": "子初", "true_solar": false},
  "plate": {"子": "酉", "丑": "戌", "…": "…"},
  "generals": {"子": "玄", "丑": "阴", "…": "…"},
  "noble": {"period": "昼", "direction": "顺"},
  "lessons": [{"up": "丑", "down": "乙", "general": "蛇"}, "…共四课"],
  "method": {"gate": "贼克", "name": "重审"},
  "transmissions": [{"branch": "丑", "general": "蛇", "kin": "财", "void": true}, "…共三传"],
  "void": ["子", "丑"],
  "time": {"beijing": "2026-10-08 14:20:00", "…": "…"}
}
```

## 字段

| 键 | 含义 |
|---|---|
| `format` | 格式版本，恒为 `liuren-chart/1` |
| `engine` | 排出这张盘的引擎及版本 |
| `input` | 起课三要素：日干支 `day`、月将 `month_general`、占时 `hour` |
| `school` | 全部流派开关的取值，见 [rules.md](rules.md) |
| `plate` | 天地盘：地盘支 → 其上所临的天盘支 |
| `generals` | 地盘支 → 其上天盘所乘的天将 |
| `noble` | 贵人：`period` 昼或夜，`direction` 顺布或逆布 |
| `lessons` | 四课，依次为一课至四课。`up` 上神，`down` 下（一课为日干，其余为地支），`general` 上神所乘之将 |
| `method` | 课体：`gate` 九宗门之一，`name` 细分课名（如重审、元首、知一、见机） |
| `transmissions` | 三传，依次为初、中、末。`branch` 地支，`general` 所乘之将，`kin` 以日干论六亲（父兄子财官），`void` 是否旬空 |
| `void` | 本旬旬空的两支 |
| `time` | 只有按公历时间起课时才有：北京时间 `beijing`、定占时用的本地时间 `local`、是否真太阳时 `true_solar`、经度 `longitude`、年月日干支、占时、月将，以及所依中气 `solar_term`（名称与时刻） |

天将用单字简称：贵（天乙贵人）、蛇（螣蛇）、雀（朱雀）、合（六合）、勾（勾陈）、龙（青龙）、空（天空）、虎（白虎）、常（太常）、玄（玄武）、阴（太阴）、后（天后）。

## 版本规则

- 字段只增不改。要删字段、改字段含义，就升到 `liuren-chart/2`
- 引擎修了规则（比如按古籍校正了涉害取法），同一时刻排出的盘可能会变。`engine` 字段记下是哪一版排的
- **实占库里的课盘，以下注那一刻排出的为准，事后不重排。** 断者是对着当时那张盘下的断语，盘要是事后变了，账就对不上了。CI 在下注时把整张盘和引擎版本写进案例文件封存；日后引擎升级，只在旁边提示"按现行引擎重排结果不同"，不改原盘
