# liuren-bench

[中文](README.md) | **English**

liuren-bench puts AI to work on Da Liu Ren (大六壬), a classical Chinese divination system: the AI casts a chart, makes a call, and the call is sealed until reality delivers the answer, all recorded in a public scorebook. What gets tested is not just the model, but the harness it runs in.

Status: pre-alpha. The casting engine in `core/` casts straight from a calendar time and passes the 720-lesson consistency checks; its rules have been checked line by line against 《六壬大全》 (see [docs/rules.md](docs/rules.md), in Chinese). Live cases and the official skill haven't opened yet.

## Why Da Liu Ren

It is half fixed, half open. Casting the chart is pure computation: same moment, same school, same chart, so there is a ground truth. Reading the chart is judgement: weighing conflicting signals with no formula. The first half tests long-chain rule execution, the second tests decision-making under ambiguity. The rules and sources are all Chinese, much of it Classical Chinese.

## Who is being tested: the judge

A judge is whoever makes a call: a person, or a *model + harness + skill* combination. The same model in a bare chat box and inside an agent harness that can run code and look things up may behave completely differently, so scores are kept per judge, not per model. Every AI call must declare the model ID and version, the harness name and version, the skill or prompt and its version, and whether tools were available.

## Tracks

**Live cases: call it first, score it later.** This is the main event. Anyone can submit a real question in two steps: the time of casting, the question and a falsifiable call (yes/no, time window, confidence) *before* the outcome is known, then what actually happened. Calls can't be edited after submission; CI enforces it. Late submissions are accepted but flagged as hindsight and excluded from stats.

You don't need to know Da Liu Ren. Ask the question, let AI make the call, come back to report the outcome. Several AIs can call the same question, which makes it a head-to-head. Because calls are sealed before the outcome exists, no model can have seen the answer in training. The project takes no position on whether Da Liu Ren works. It just keeps score.

**Official skill.** The repo will ship a skill you install into your own AI. It casts the chart with `core/` so the fixed half isn't guessed, guides the model to a falsifiable call, fills in the judge declaration, and submits only after you confirm: via `gh` if available, otherwise as a prefilled issue link. Submissions go through your own GitHub account; there is no public API.

**Casting.** Given a moment, cast the chart; graded item by item. Two leaderboards: bare (no tools) and agent (tools allowed, but no existing chart libraries, including this project's `core/`).

**Classical text.** Reading questions on source texts such as 課經 and 畢法賦.

**Judgement.** Classical cases with the original verdict hidden; measures agreement with the historical practitioner, not predictive accuracy.

## Layout

```
core/           casting engine: time → chart (MIT)
skill/          official skill: cast, call, submit (MIT, planned)
bench/          question generation, scoring, leaderboards (MIT, planned)
cases/
  classical/    classical cases (CC-BY-4.0)
  live/         live cases, one file each, called then scored (CC-BY-4.0)
docs/           rule audit, chart data format
```

## Roadmap

M1 engine → M2 live cases and official skill → M3 casting track → M4 classical cases and text track → M5 judgement track. M1 is done; currently at M2. See [ROADMAP.md](ROADMAP.md) (in Chinese).

## Contributing

Most wanted: let your AI call a real question and come back to score it. People who can't read a chart are especially welcome. Also wanted: classical cases with complete charts, documented differences between schools, and bug reports. The maintainer can't read a chart either, so practitioners are doubly welcome. Live cases have strict privacy rules. See [CONTRIBUTING.md](CONTRIBUTING.md) (in Chinese).

## Known risks

"Ground truth" is only true within one school. The engine follows 《六壬大全》, the one classic available in full text for line-by-line checking, with known disagreements configurable.

Judge declarations are self-reported and can't be verified. Stats are grouped by declaration and labelled as such.

Classical cases are survivor-biased and famous ones may be in training data. Live cases fix the first problem but bring their own: people who bother to submit probably already lean towards believing in it.

One-person side project, no schedule guarantees.

## License

Code: MIT, see [LICENSE](LICENSE). Case data: CC-BY-4.0. Maintainers: [MAINTAINERS.md](MAINTAINERS.md).
