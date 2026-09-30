# 数据格式

本项目有两种数据格式：课盘 liuren-chart/1，实占案例 liuren-live/1。

## 课盘 liuren-chart/1

引擎的输出、实占库封存的课盘、起课轨的标准答案，用的都是这一份格式。JSON，键名英文，值用中文（干支、将名、课名）。机读校验用 [schema/chart-1.json](schema/chart-1.json)。

### 长什么样

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

### 字段

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

### 版本规则

- 字段只增不改。要删字段、改字段含义，就升到 `liuren-chart/2`
- 引擎修了规则（比如按古籍校正了涉害取法），同一时刻排出的盘可能会变。`engine` 字段记下是哪一版排的
- **实占库里的课盘，以下注那一刻排出的为准，事后不重排。** 断者是对着当时那张盘下的断语，盘要是事后变了，账就对不上了。CI 在下注时把整张盘和引擎版本写进案例文件封存；日后引擎升级，只在旁边提示"按现行引擎重排结果不同"，不改原盘

## 实占案例 liuren-live/1

实占库的原件是 issue，这份格式是从 issue 里导出的数据集，每天导出一次，放在 `data` 分支：`live.json` 是全部案例，`cases/<issue 编号>.json` 是单个案例，`LEDGER.md` 是账本。机读校验用 [schema/live-1.json](schema/live-1.json)。

导出只读机器人（`github-actions[bot]`）发的封存回复。issue 原帖、用户回复事后怎么改、删不删，都不影响导出结果。

### 字段

| 键 | 含义 |
|---|---|
| `format` | 恒为 `liuren-live/1` |
| `id`、`url` | issue 编号与链接 |
| `owner` | 提问人，只有他报的结果算数 |
| `question`、`category` | 占事与类别 |
| `deadline` | 截止日：到这天还没发生，就算"不成" |
| `sealed_at` | 问题的封存时刻（北京时间），取 issue 创建与最后修改中较晚者 |
| `cast` | 起课时间 `time`，以及封存时排出的整张课盘 `chart`（liuren-chart/1），事后不重排 |
| `flags` | 提示，如"起课时间早于开 issue 24 小时以上" |
| `verdicts` | 断语列表，见下 |
| `result` | 提问人报的结果：`outcome` 成或不成、`date` 成的日期、`note` 说明；未开奖为 null |
| `status` | 待开奖、已开奖，或失联（过截止日 30 天未开奖） |

每条断语：

| 键 | 含义 |
|---|---|
| `judge` | 人断为 `{"human": true}`；AI 断为 `model`、`harness`、`skill`、`tools` 四项 |
| `complete` | AI 断者四项是否齐全，不齐的不进断者的账 |
| `outcome`、`window`、`confidence` | 断成还是不成；断成时的应期区间；把握（0.5 到 1.0） |
| `basis` | 依据，自由文本 |
| `author`、`source`、`sealed_at` | 谁交的、来自 issue 还是哪条回复、封存时刻 |
| `judge_key` | 断者标识，账本按它分组 |
| `self_reported` | 恒为 true：断者信息全凭自报 |
| `hindsight` | 马后炮：封存晚于截止日、晚于结果上报，或晚于结果发生日期 |
