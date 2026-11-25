#!/usr/bin/env bash
# SessionStart hook: injects the contributing skill body (SKILL.md without its
# frontmatter) into every session, so its git-host rules apply even when the
# skill's description never matches the task.
#
# Prints hookSpecificOutput JSON on stdout. Silent and exit 0 on any problem,
# so a missing or broken skill never blocks a session. Plain bash 3.2 for macOS.

skill=""
for f in "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/contributing/SKILL.md" "$HOME/.agents/skills/contributing/SKILL.md"; do
  if [ -r "$f" ]; then
    skill="$f"
    break
  fi
done
[ -n "$skill" ] || exit 0

# Drop the frontmatter block (first line "---" up to the next "---"), then leading blank lines.
body=$(tr -d '\r' < "$skill" 2>/dev/null | awk 'NR == 1 && /^---$/ { fm = 1; next } fm && /^---$/ { fm = 0; next } !fm' | sed '/./,$!d')
[ -n "$body" ] || exit 0

# python3 -I ignores the working directory and env, so a stray json.py cannot shadow the stdlib.
json=""
if command -v python3 >/dev/null 2>&1; then
  json=$(printf '%s' "$body" | python3 -I -c 'import json, sys; print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": sys.stdin.read()}}))' 2>/dev/null)
fi

if [ -z "$json" ]; then
  tab=$(printf '\t')
  escaped=$(printf '%s' "$body" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e "s/$tab/\\\\t/g" | awk '{ printf "%s%s", (NR > 1 ? "\\n" : ""), $0 }')
  json=$(printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}' "$escaped")
fi

printf '%s\n' "$json"
exit 0
