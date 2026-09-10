# Roadbook

> Chinese is the primary language of this project. The docs, the skill and the demo app
> are all in Chinese — [README.md](README.md) is the full version. This page is a summary
> for people deciding whether the idea is worth translating for.

**UI main-flow regression as a Claude Code skill.** An agent drives your app through a
real browser by replaying a recorded *playbook*; when the UI has changed it surveys the
new route and rewrites the playbook. The verdict never comes from the agent that did the
driving — a separate **judge** agent walks an ordered acceptance route, quotes the page
text it read, and a small scorer turns that into an exit code.

Expectations are written in plain language, once, in `expect.yaml`: an ordered list of
steps, each with just two keys — `go` (where to navigate) and `check` (what must be true
there). No selectors, no assertion code, no second copy of the expected values to keep in
sync.

## This is a specification, not a tool

The code is a hundred-line scorer and three index scripts. What the repo actually ships is
a set of conventions — where files live, what they look like, who reads what, how a verdict
is scored — so that any implementation following them (a different browser tool, a
different model, a headless program) produces runs that can be compared and re-checked
against each other. Six conventions, one file each: the **scenario** directory (three files,
no steps in `intent.md`), the **expectation** format (`goal` + ordered `steps`, each with
only `go` and `check`), the **judge** protocol (independent agent, every screen self-loaded,
evidence quoted verbatim, mirrored `judgment.yaml`), the **scorer** (exit 0/1/2,
completeness only), the **playbook** format (five fields per step, agent-written, in git),
and **atoms** (agent-written product memory, status derived from PASS runs). A data-flow
wall runs through all six: the runner never reads `expect.yaml`, the judge never reads the
playbook or atoms. `tests/` is the machine-readable form of the spec. It is `v0.1` and will
change as it meets more products.

## Why not let the model look at the screen and say "pass"?

Because the screen lies. Two measured examples from the product this was built against,
one afternoon apart: a save dialog said *saved* while the backend held the old value; and
a quantity changed from 4 to 2 rendered as 2 in both the card **and** the summary panel
while the backend still held 4 — the real number only surfaced in the final payment
dialog. A screenshot-based assertion calls both PASS.

So the design separates three things people usually conflate:

| | who | how |
|---|---|---|
| Understanding the expectation | the model | reads a sentence of plain language |
| Reaching a verdict | the model, under protocol | every `pass`/`fail` quotes the page text it read |
| Scoring the verdict | code | completeness only, never meaning |

## Four rules that make a verdict worth something

1. **The judge is not the driver** — a freshly spawned agent with no operating history and
   no access to the playbook, enforced by the data flow rather than by asking politely.
2. **Every screen is loaded by the judge itself** — it never adjudicates a page it merely
   found open, which might be the runner's optimistically rendered one. Statuses, counts
   and amounts are therefore always read from a clean load. An invariant in the protocol,
   not a per-step flag a human has to remember.
3. **Evidence must be quoted verbatim** — page text or a raw API value. A `pass` with no
   evidence is scored BLOCK, not PASS.
4. **BLOCK is a first-class outcome** — environment broken ≠ product broken.

## Adopting it

One scenario is one directory with three files — two written by you, one by the agent:
`intent.md` (a `name`/`description` frontmatter for picking, then goal, fixed parameters,
red lines, seeding and cleanup — no steps), `expect.yaml` (the judge's ordered route), and
`playbook.md` (generated on the first exploratory run, replayed and rewritten afterwards —
its git diff *is* your UI change log). Variants of the same route with different values are
separate scenario directories, not parameters. `scripts/scenarios.py` lists scenarios one
line each so the agent can pick without loading every file.

The repo ships four demo scenarios against a single-file demo app, one of which has a
deliberate `?bug=optimistic` mode that renders but never persists — a screenshot assertion
passes it, the judge fails it. A real run's artifacts are in [docs/example-run/](docs/example-run/).

## Honest limitations

No CI path yet (everything runs in an interactive agent session); thin evidence base (one
real product, two scenarios, about a week, plus four demo scenarios run once each); real
token cost (~70–90k tokens for the judge alone on a five-step flow); coupled to Claude
Code's browser tool names (see [docs/porting.md](docs/porting.md)); it answers "does the
flow still work", never "why did it break"; and the progressive disclosure of scenarios and
atoms is discipline enforced by prompt and lint, not a harness mechanism.

Not a replacement for Midscene, Browser Use or Playwright — a discipline layer that can
sit on top of any of them. Midscene solves cheap deterministic replay and offers a
natural-language assertion returning a boolean; this project's contribution is what comes
after: *who* may decide, and what a decision has to be backed by.

MIT licensed. Contributions of scenarios from other products are the most useful thing
right now — the design needs contact with UIs it was not developed against.
