---
name: review
description: Reviews code in one of three modes. Plan-based review of the work since the last release (the default, or "review the branch"), a two-model cross-review with confirmed-issues synthesis ("/review cross", "cross-review"), or a summary of what to fix from the latest GitHub PR review ("/review github", "is the PR review worth fixing"). Use when the user asks for any of these.
---

# Review

Pick the mode from the arguments given (if any), or else from the request:

| Mode | Chosen when | Details |
|---|---|---|
| `diff` (default) | no mode word, or the user asks to review the branch, the work, or the diff since the last release | `references/diff-review.md` |
| `cross` | the first argument is `cross`, or the user asks for a cross-review, a peer review or a two-model review | `references/cross-review.md` |
| `github` | the first argument is `github`, or the user asks what to fix in the latest PR review | `references/github-review.md` |

Strip the mode word from the arguments, then read only the reference for the chosen mode and follow it.

No mode edits files. Fixes wait for the user's go-ahead.
