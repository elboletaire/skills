# skills

My generic agent skills, Claude Code subagents, Pi subagents and a Bash hook, packaged for [APM](https://github.com/microsoft/apm) (Agent Package Manager).

## What's inside

| Source | Installed as |
|---|---|
| `skills/review/` | Skill `review`: plan-based diff review, two-model cross-review, or the latest GitHub PR review (mode chosen from the arguments) |
| `skills/version/` | Skill `version`: SemVer bump, changelog, local commit and tag, nothing pushed |
| `skills/init-agents/` | Skill `init-agents`: generates an AGENTS.md contributor guide |
| `skills/dream/` | Skill `dream`: sorts agent memories into skills, instructions or nothing |
| `skills/herdr-orchestrator/` | Skill `herdr-orchestrator`: turns a herdr main-branch agent into an orchestrator of worktree agents |
| `.apm/agents/*.agent.md` | Claude Code subagents `worker`, `reviewer`, `integrator` in `~/.claude/agents/` |
| `.apm/hooks/gh-hygiene.json` | PreToolUse hook on Bash, merged into `~/.claude/settings.json`. Blocks `gh` commands that would publish local paths, environment details or secrets. `GH_HYGIENE=off` disables it for one shell. |
| `.apm/hooks/contributing-rules.json` | SessionStart hook, merged into `~/.claude/settings.json`. Injects the body of the `contributing` skill (installed separately from vocdoni/skills) into every session, so its rules apply even when the skill's description doesn't match. Silent when the skill is absent. |
| `pi/agents/*.md` | Pi subagents, not installed by APM (see below) |

The hooks' regression suites live in `tests/`, outside the APM deployment: run `python3 -I tests/test-gh-hygiene.py` for the PreToolUse hook and `python3 tests/test-contributing-rules.py` for the SessionStart hook.

## Install

Add the package to your global APM manifest, `~/.apm/apm.yml`:

```yaml
name: global
version: 1.0.0
targets: [agent-skills, claude]
dependencies:
  apm:
    - elboletaire/skills
```

Then install it globally:

```bash
apm install -g
```

Skills are deployed to `~/.agents/skills/` and `~/.claude/skills/`, the subagents to `~/.claude/agents/`, and the hook to `~/.claude/settings.json`. Run apm with `uvx --from apm-cli apm` if it isn't installed.

## Pi agents

APM has no Pi target, so the Pi subagents are only copied into APM's module cache, under `~/.apm/apm_modules/<owner>/skills/pi/agents/` (`_local/skills` for a local path install). Link that folder to `~/.pi/agent/agents` to use them. To find the exact path on your machine, run `find ~/.apm/apm_modules -path '*pi/agents' -type d`.

## License

Apache License 2.0, see [LICENSE](LICENSE).
