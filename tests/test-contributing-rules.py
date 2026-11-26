#!/usr/bin/env python3
"""Regression suite for contributing-rules.sh. Run: python3 tests/test-contributing-rules.py"""
import json, os, shutil, subprocess, sys, tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".apm", "hooks", "scripts", "contributing-rules.sh")

FRONTMATTER = '---\nname: contributing\ndescription: "Use when "quoting" works"\n---\n\n'
BODY = ('# Contributing\n\n'
        'Say "hi" and write C:\\path\\to\\file, not a \\n escape.\n'
        '\tIndented with a tab.\n'
        'Unicode stays: café, 東京.\n'
        '\n'
        'Last line.')
SKILL = FRONTMATTER + BODY + "\n"


def run(home, env_extra=None, path=None):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CONFIG_DIR",)}
    env["HOME"] = home
    if path is not None:
        env["PATH"] = path
    env.update(env_extra or {})
    p = subprocess.run(["/bin/bash", HOOK], input="{}", text=True,
                       capture_output=True, env=env)
    return p.returncode, p.stdout, p.stderr


def write_skill(root, text=SKILL):
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, "SKILL.md"), "w", encoding="utf-8") as fh:
        fh.write(text)


def fallback_path(bindir):
    # A PATH with only the tools the hook needs, so python3 is not found.
    os.makedirs(bindir, exist_ok=True)
    for tool in ("tr", "awk", "sed"):
        src = shutil.which(tool)
        os.symlink(src, os.path.join(bindir, tool))
    return bindir


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    if not ok and detail:
        print("         " + detail.strip().splitlines()[0])
    return 0 if ok else 1


def main():
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        home = os.path.join(tmp, "home")
        os.makedirs(home)
        expected = BODY

        print("contributing-rules.sh")

        # Primary location: $HOME/.claude/skills.
        write_skill(os.path.join(home, ".claude", "skills", "contributing"))
        code, out, err = run(home)
        failed += check("exit 0 with a skill", code == 0, err)
        try:
            data = json.loads(out)
            ctx = data["hookSpecificOutput"]["additionalContext"]
            failed += check("stdout is valid JSON", True)
            failed += check("hookEventName is SessionStart",
                            data["hookSpecificOutput"]["hookEventName"] == "SessionStart")
            failed += check("additionalContext is the body without frontmatter",
                            ctx == expected, f"got {ctx!r}")
        except (ValueError, KeyError) as exc:
            failed += check("stdout is valid JSON", False, f"{exc}: {out!r}")

        # Fallback: no python3 on PATH, the sed/awk escape must give the same JSON.
        bindir = fallback_path(os.path.join(tmp, "bin"))
        code, out, err = run(home, path=bindir)
        try:
            ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
            failed += check("sed/awk fallback gives identical context",
                            ctx == expected, f"got {ctx!r}")
        except (ValueError, KeyError) as exc:
            failed += check("sed/awk fallback gives valid JSON", False, f"{exc}: {out!r}")

        # Other location: $HOME/.agents/skills, used when .claude has no copy.
        agents_home = os.path.join(tmp, "agents_home")
        write_skill(os.path.join(agents_home, ".agents", "skills", "contributing"))
        code, out, err = run(agents_home)
        try:
            ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
            failed += check("falls back to ~/.agents/skills", ctx == expected, f"got {ctx!r}")
        except (ValueError, KeyError) as exc:
            failed += check("falls back to ~/.agents/skills", False, f"{exc}: {out!r}")

        # CLAUDE_CONFIG_DIR wins over $HOME/.claude.
        cfg = os.path.join(tmp, "cfg")
        write_skill(os.path.join(cfg, "skills", "contributing"), SKILL.replace("Last line.", "From CLAUDE_CONFIG_DIR."))
        code, out, err = run(home, {"CLAUDE_CONFIG_DIR": cfg})
        try:
            ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
            failed += check("CLAUDE_CONFIG_DIR takes precedence",
                            ctx.endswith("From CLAUDE_CONFIG_DIR."), f"got {ctx!r}")
        except (ValueError, KeyError) as exc:
            failed += check("CLAUDE_CONFIG_DIR takes precedence", False, f"{exc}: {out!r}")

        # No skill anywhere: silent, exit 0.
        empty_home = os.path.join(tmp, "empty_home")
        os.makedirs(empty_home)
        code, out, err = run(empty_home)
        failed += check("no skill: empty stdout and exit 0", code == 0 and out == "", out + err)

        # Empty body after frontmatter: silent, exit 0.
        blank_home = os.path.join(tmp, "blank_home")
        write_skill(os.path.join(blank_home, ".claude", "skills", "contributing"), FRONTMATTER)
        code, out, err = run(blank_home)
        failed += check("empty body: empty stdout and exit 0", code == 0 and out == "", out + err)

    print(f"\n{'FAILED' if failed else 'OK'}: {failed} failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
