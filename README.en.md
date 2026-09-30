# liuren-bench

[中文](README.md) | **English**

liuren-bench tests LLMs on Da Liu Ren (大六壬), a classical Chinese divination system: give the model a moment in time, have it cast the chart (Heaven–Earth plates, Four Lessons, Three Transmissions), and grade it item by item against a deterministic engine. It also doubles as a public scorebook for divination calls.

Status: pre-alpha. A draft casting engine is in `core/` and passes the 720-lesson consistency checks, but its rules have not yet been verified against classical sources (see [docs/rules.md](docs/rules.md), in Chinese). The benchmark itself hasn't started.

## Why Da Liu Ren

Forget whether it "works" for a moment. Casting a chart is a long, fully specified rule chain: calendar conversion, stem-branch arithmetic, table lookups, then an ordered cascade of rules to derive the Three Transmissions. One wrong step breaks everything downstream, and per-item grading shows exactly where the model went off the rails.

Same moment, same school, same chart, so there is a ground truth. Any moment is a fresh question, so the pool is unlimited and can't be memorised. The rules and sources are all Chinese, much of it Classical Chinese.

## Four tracks

**Casting.** Given a moment, cast the chart. Closed-book (moment only) or open-book (full rule text supplied).

**Classical text.** Reading questions on source texts such as 課經 and 畢法賦, graded against cited passages.

**Judgement.** Classical cases with the original verdict hidden; the model gives its own. This measures agreement with the historical practitioner, not predictive accuracy.

**Live cases: call it first, score it later.** Anyone can submit their own reading in two steps: a PR with the chart, the question and a falsifiable call (yes/no, time window, confidence) *before* the outcome is known, then a second PR filling in what actually happened. Calls can't be edited after merge; CI enforces it. Late submissions are accepted but flagged as hindsight and excluded from stats. Humans and models can both attach calls to the same case. Because calls are sealed before the outcome exists, no model can have seen the answer in training.

The project takes no position on whether Da Liu Ren works. It just keeps score.

## Layout

```
core/           casting engine: time → chart (MIT)
bench/          question generation, scoring, leaderboard (MIT)
cases/
  classical/    classical cases: chart + original verdict + source (CC-BY-4.0)
  live/         live cases, one file each, called then scored (CC-BY-4.0)
docs/           methodology
```

## Roadmap

M1 engine → live cases open → M2 casting track v0 → M3 classical cases and text track → M4 judgement track. Currently at M1. Live cases open early because outcomes take months to arrive. See [ROADMAP.md](ROADMAP.md) (in Chinese).

## Contributing

The maintainer can't read a Da Liu Ren chart, so engine correctness depends on charts recorded in classical texts. Most wanted: classical cases with complete charts, documented differences between schools, your own live calls, and bug reports. Live cases have strict privacy rules: your own affairs only, nothing that identifies a third party. See [CONTRIBUTING.md](CONTRIBUTING.md) (in Chinese).

## Known risks

"Ground truth" is only true within one school. The default follows 《大六壬指南》 with known disagreements configurable; an unflagged disagreement will mark another school's correct answer as wrong.

Classical cases are survivor-biased (books recorded the hits) and famous ones may be in training data. Live cases fix the first problem but bring their own: people who bother to submit probably already lean towards believing in it.

One-person side project, no schedule guarantees.

## License

Code: MIT, see [LICENSE](LICENSE). Case data: CC-BY-4.0. Maintainers: [MAINTAINERS.md](MAINTAINERS.md).
