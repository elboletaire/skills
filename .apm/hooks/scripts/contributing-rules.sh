#!/usr/bin/env bash
# SessionStart hook: injects the contributing skill body (frontmatter stripped) so its
# rules apply even when its description never matches. Never blocks: exits 0 silently
# on any problem. Plain bash 3.2 for macOS.

skill=""
for f in "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/contributing/SKILL.md" "$HOME/.agents/skills/contributing/SKILL.md"; do
  if [ -r "$f" ]; then
    skill="$f"
    break
  fi
done
[ -n "$skill" ] || exit 0

# Drop control chars but tab/newline (keeps the fallback's JSON valid), the frontmatter
# (BOM or trailing spaces allowed on its fences) and leading blank lines.
bom=$(printf '\357\273\277')
body=$(tr -d '\000-\010\013-\037' < "$skill" 2>/dev/null | awk -v bom="$bom" 'NR == 1 && index($0, bom) == 1 { $0 = substr($0, length(bom) + 1) } NR == 1 && /^---[ \t]*$/ { fm = 1; next } fm && /^---[ \t]*$/ { fm = 0; next } !fm' | sed '/./,$!d')
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
