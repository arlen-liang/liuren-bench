# liuren-bench

[中文](README.md) | **English**

liuren-bench puts AI to work on Da Liu Ren (大六壬), a classical Chinese divination system: the AI casts a chart, makes a call, and the call is sealed until reality delivers the answer, all recorded in a public scorebook. What gets tested is not just the model, but the harness it runs in.

Status: pre-alpha. The casting engine in `core/` casts straight from a calendar time and passes the 720-lesson consistency checks; its rules have been checked line by line against 《六壬大全》 (see [docs/rules.md](docs/rules.md), in Chinese). Live cases and the official skill haven't opened yet.

## Why Da Liu Ren

It is half fixed, half open. Casting the chart is pure computation: same moment, same school, same chart, so there is a ground truth. Reading the chart is judgement: weighing conflicting signals with no formula. The first half tests long-chain rule execution, the second tests decision-making under ambiguity. The rules and sources are all Chinese, much of it Classical Chinese.

## Who is being tested: the judge

A judge is whoever makes a call: a person, or a *model + harness + skill* combination. The same model in a bare chat box and inside an agent harness that can run code and look things up may behave completely differently, so scores are kept per judge, not per model. Every AI call must declare the model ID and version, the harness name and version, the skill or prompt and its version, and whether tools were available.

## Tracks

**Live cases: call it first, score it later.** This is the main event. One real question per GitHub issue: the time of casting, the question, a deadline and a falsifiable call (yes/no, time window, confidence), then later the outcome as a reply. A bot immediately replies with a seal: the full chart, engine version, the call verbatim and the server timestamp. Later edits or deleted replies don't change what was sealed. Calls sealed after the outcome happened are flagged as hindsight and excluded from stats.

You don't need to know Da Liu Ren. Ask the question, let AI make the call, come back to report the outcome. Several AIs can call the same question in the same issue, which makes it a head-to-head.

Be clear about what this ledger is: AI calls are submitted by users, the model is self-reported, and nothing stops someone from rerolling ten times and submitting the one they like. It is for fun and for seeing what people use, not a rigorous model benchmark; the casting and judgement tracks are, since they run every model under the same script. The project takes no position on whether Da Liu Ren works. It just keeps score.

**Web page and official skill.** The [web page](https://arlen-liang.github.io/liuren-bench/web/) is for people who use chat apps: enter the time and question, get the chart and a prompt to paste into any AI, paste the answer back, and get a prefilled issue link. The skill ([skill/SKILL.md](skill/SKILL.md)) is for agent users (Claude Code, opencode, …): it casts with `core/`, attaches the relevant passages of 《六壬大全》 (the lesson type, and the branches and generals in the transmissions) so the model can cite sources instead of improvising, asks you to confirm the judge declaration, and submits only after you confirm. The web page and the skill share one prompt template; CI checks they produce identical prompts. Both need a GitHub account; there is no public API.

**Casting.** Given a moment, cast the chart; graded item by item. Two leaderboards: bare (no tools) and agent (tools allowed, but no existing chart libraries, including this project's `core/`).

**Classical text.** Reading questions on source texts such as 課經 and 畢法賦.

**Judgement.** Classical cases with the original verdict hidden; measures agreement with the historical practitioner, not predictive accuracy.

## Layout

```
core/           casting engine: time → chart (MIT)
bot/            live-case bot: sealing and export (MIT)
web/            web page (MIT)
skill/          prompt, official skill, source excerpts (MIT; excerpts CC BY-SA 4.0)
bench/          question generation, scoring, leaderboards (MIT, planned)
cases/
  classical/    classical cases (CC-BY-4.0)
docs/           rule audit, data formats
```

Live cases live in issues labelled `live-case`. A daily export goes to the history-less `data` branch (CC-BY-4.0): delete an issue and it disappears from the next export.

## Roadmap

M1 engine → M2 live cases and official skill → M3 casting track → M4 classical cases and text track → M5 judgement track. M1 is done; currently at M2. See [ROADMAP.md](ROADMAP.md) (in Chinese).

## Contributing

Most wanted: let your AI call a real question and come back to score it. People who can't read a chart are especially welcome. Also wanted: classical cases with complete charts, documented differences between schools, and bug reports. The maintainer can't read a chart either, so practitioners are doubly welcome. Live cases have strict privacy rules. See [CONTRIBUTING.md](CONTRIBUTING.md) (in Chinese).

## Known risks

"Ground truth" is only true within one school. The engine follows 《六壬大全》, the one classic available in full text for line-by-line checking, with known disagreements configurable.

Judge declarations and outcomes are self-reported and can't be verified. Submitting a live case requires a GitHub account, which is unreliable to reach from mainland China; that cuts against inviting casual users, and there's no good fix yet.

Classical cases are survivor-biased and famous ones may be in training data. Live cases fix the first problem but bring their own: people who bother to submit probably already lean towards believing in it.

One-person side project, no schedule guarantees.

## License

Code: MIT, see [LICENSE](LICENSE). Case data: CC-BY-4.0. `skill/duanfa/daquan.json` is excerpted from the Wikisource punctuated edition and is CC BY-SA 4.0. Maintainers: [MAINTAINERS.md](MAINTAINERS.md).
