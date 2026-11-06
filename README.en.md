# Product Adoption Review

A cross-project skill that checks whether an external release has a clear promise,
demonstration, verifiable installation path, discoverability, distribution plan, and
honest evidence.

Completed reviews are logged locally with pseudonymized project identifiers and minimal
metadata. The script rejects known path, secret (`sk-`, `ghp_`, `AKIA`…) and email
formats; this filter is not exhaustive, so the agent remains responsible for never logging
prompts, responses, or personal data.
Every ten completed uses produce a local review report. Official skill changes always
require human approval, tests, and a pull request.

Version 0.2.0 records the target release stage, evidence status, and version scope.
Equivalent findings share a stable issue identifier, so wording or language differences
do not prevent grouping. Every promoted candidate includes a minimal change and a
regression test. A verdict always applies to one explicit stage, from assisted pilot to
stable release.

No telemetry or network service is included.

## Pilot installation

Requires Python 3.10 or later (CI: 3.13 on Ubuntu and Windows), standard library only.

1. Copy `skills/product-adoption-review/` into the agent's personal skills directory:
   `~/.agents/skills/product-adoption-review/` for Codex, or
   `~/.claude/skills/product-adoption-review/` for Claude Code.
2. Verify: `python <skill-dir>/scripts/usage_log.py status` prints `"ok": true` and the
   state directory.
3. Update: replace the copied folder with the new version; the local log is kept.
4. Uninstall: delete the copied folder, then the state directory if the log is no longer
   needed.

State directory: `%LOCALAPPDATA%\Codex\product-adoption-review\` on Windows,
`$XDG_DATA_HOME/product-adoption-review/` (default `~/.local/share/product-adoption-review/`)
on Linux and macOS, or the path set in `PRODUCT_ADOPTION_REVIEW_STATE_DIR`.
