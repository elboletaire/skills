---
name: review
description: Reviews code in one of three modes. `diff` (the default) reviews the work since the last release, plan-based; `cross` runs a two-model cross-review of the branch against its base ("/review cross", "cross-review"); `github` summarises what to fix in the latest review on this branch's GitHub PR ("/review github"). Use when the user asks for any of these.
---

# Review

Pick the mode from the first argument if it is a mode word, or else from the request:

| Mode | Chosen when | Reviews | Details |
|---|---|---|---|
| `diff` (default) | no mode word, or the user asks to review the branch, the work or the diff since the last release | the work since the last release, plan-based | `references/diff-review.md` |
| `cross` | the first argument is `cross`, or the user asks for a cross-review, a peer review or a two-model review | the branch against its base; takes a scope | `references/cross-review.md` |
| `github` | the first argument is `github`, or the user asks what to fix in the latest PR review | the latest review on this branch's PR | `references/github-review.md` |

Strip the mode word from the arguments. Whatever remains is a scope hint: `cross` takes it as the review scope (see its reference), `diff` uses it to narrow which work is reviewed, and `github` ignores it.

Read only the reference for the chosen mode and follow it.

No mode edits files. Fixes wait for the user's go-ahead.
