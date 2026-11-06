# Product Adoption Review

A cross-project skill that keeps a technically sound project from being released without
a clear promise, a demonstration, a verifiable installation path, or a distribution plan.

## Scope

The skill activates for external distribution: a release, a public README, a plugin, a
marketplace listing, an application, user documentation, or a launch. It stays inactive
during ordinary internal development.

## Example

Request (synthetic fixture `tests/fixtures/case-b`): "Review the stable release of
Nettoie-tableau 1.0, which promises to remove every identifier."

Verdict: **NO-GO for `stable-release`**.

- `claim-evidence-mismatch` · `blocker` · `contradictory` evidence: the published 1.0
  example still contains `TEST-001`, despite the promise.
- `artifact-unavailable` · `blocker` · `observed` evidence: the "Download" button leads
  to no archive.
- The 0.8 report is not accepted as evidence: it covers an `earlier` version.

The verdict is the one observed during the 0.2.0 evaluation
([`docs/evaluation-0.2.0.md`](docs/evaluation-0.2.0.md), in French); findings are
summarized.

## Local improvement loop

After each completed review, the skill writes a minimal, pseudonymized entry to:

```text
~/.local/share/product-adoption-review/usage.jsonl
```

The project path is hashed and never stored. The script rejects known path, secret
(`sk-`, `ghp_`, `AKIA`…) and email formats, but this filter is not exhaustive: the agent
remains responsible for never logging prompts, responses, or personal data.
Every batch of ten uses produces a local Markdown report. The report may propose a
change, but never modifies the official skill automatically.

Since version 0.2.0, each review records the target release stage, the evidence status,
and its version scope. Equivalent findings share a stable issue identifier, so the report
can group them despite different wording or languages. Every candidate includes the
proposed minimal change and regression test.

## Governance

- private pilot repository at version `0.x`;
- a rule becomes a candidate after three occurrences in two projects, unless it is a
  reproducible blocker;
- human approval is mandatory;
- branch, regression test, and pull request without automatic merge;
- `1.0.0` is published after the first accepted report.

A verdict always applies to one explicit stage: assisted pilot, closed beta, public beta,
or stable release. Missing adoption evidence alone is not enough to refuse a pilot meant
to collect that evidence.

## Pilot installation

Requirements: Python 3.10 or later (CI: 3.10 and 3.13 on Ubuntu and Windows; macOS untested), standard library
only.

1. Copy the `skills/product-adoption-review/` folder into the agent's personal skills
   directory:
   - Codex: `~/.agents/skills/product-adoption-review/`;
   - Claude Code: `~/.claude/skills/product-adoption-review/`.
2. Verify: `python <skill-dir>/scripts/usage_log.py status` must print `"ok": true` and
   the state directory.
3. Update: replace the copied folder with the new version. The local log is kept.
4. Uninstall: delete the copied folder, then, if the log is no longer needed, the state
   directory below.

The skill is discovered automatically only for external distribution work.

State directory (log and reports):

- every system, Windows included: `~/.local/share/product-adoption-review/`, or
  `$XDG_DATA_HOME/product-adoption-review/` when that variable is set (outside
  `AppData`, which the Microsoft Store Codex app virtualizes);
- override with the `PRODUCT_ADOPTION_REVIEW_STATE_DIR` variable.

## Privacy

No telemetry and no network calls. The scripts use only the Python standard library and
fail explicitly if the local log cannot be written.

The first series of ten uses is described in [`docs/pilot.md`](docs/pilot.md) (in French).
