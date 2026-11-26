#!/usr/bin/env python3
"""Regression suite for skill-rules.sh. Run: python3 tests/test-skill-rules.py"""
import json, os, shutil, subprocess, sys, tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".apm", "hooks", "scripts", "skill-rules.sh")
NAMES = ("contributing", "comments")
# Claude Code caps additionalContext at 10,000 characters per hook.
CONTEXT_CAP = 10000

BODY = ('# Skill\n\n'
        'Say "hi" and write C:\\path\\to\\file, not a \\n escape.\n'
        '\tIndented with a tab.\n'
        'Unicode stays: café, 東京.\n'
        '\n'
        'Last line.')


def skill_text(name):
    return f'---\nname: {name}\ndescription: "Use when "quoting" works"\n---\n\n' + BODY + "\n"


def run(home, args=("contributing",), env_extra=None, path=None):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CONFIG_DIR",)}
    env["HOME"] = home
    if path is not None:
        env["PATH"] = path
    env.update(env_extra or {})
    p = subprocess.run(["/bin/bash", HOOK, *args], input="{}", text=True,
                       capture_output=True, env=env)
    return p.returncode, p.stdout, p.stderr


def write_skill(root, text):
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


def context_of(out):
    return json.loads(out)["hookSpecificOutput"]["additionalContext"]


def main():
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name in NAMES:
            failed += run_cases(tmp, name)

        print("invalid names")
        home = os.path.join(tmp, "invalid_home")
        for name in ("contributing", "comments"):
            write_skill(os.path.join(home, ".claude", "skills", name), skill_text(name))
        for bad in ("", "../contributing", "Comments", "comments.md", "co mments", "comments/x"):
            code, out, err = run(home, args=(bad,))
            failed += check(f"{bad!r}: empty stdout and exit 0", code == 0 and out == "", out + err)
        code, out, err = run(home, args=())
        failed += check("no argument: empty stdout and exit 0", code == 0 and out == "", out + err)

    print("installed skills")
    real_home = os.path.expanduser("~")
    for name in NAMES:
        if not os.path.isfile(os.path.join(real_home, ".claude", "skills", name, "SKILL.md")):
            print(f"  [SKIP] {name}: not installed under ~/.claude/skills")
            continue
        code, out, err = run(real_home, args=(name,))
        try:
            ctx = context_of(out)
            failed += check(f"{name}: additionalContext under {CONTEXT_CAP} characters",
                            code == 0 and len(ctx) < CONTEXT_CAP, f"{len(ctx)} characters")
        except (ValueError, KeyError) as exc:
            failed += check(f"{name}: stdout is valid JSON", False, f"{exc}: {out!r}")

    print(f"\n{'FAILED' if failed else 'OK'}: {failed} failure(s)")
    return 1 if failed else 0


def run_cases(tmp, name):
    failed = 0
    home = os.path.join(tmp, f"{name}_home")
    os.makedirs(home)
    expected = BODY
    text = skill_text(name)

    print(name)

    # Primary location: $HOME/.claude/skills.
    write_skill(os.path.join(home, ".claude", "skills", name), text)
    code, out, err = run(home, args=(name,))
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
    bindir = fallback_path(os.path.join(tmp, f"{name}_bin"))
    code, out, err = run(home, args=(name,), path=bindir)
    try:
        ctx = context_of(out)
        failed += check("sed/awk fallback gives identical context", ctx == expected, f"got {ctx!r}")
    except (ValueError, KeyError) as exc:
        failed += check("sed/awk fallback gives valid JSON", False, f"{exc}: {out!r}")

    # Other location: $HOME/.agents/skills, used when .claude has no copy.
    agents_home = os.path.join(tmp, f"{name}_agents_home")
    write_skill(os.path.join(agents_home, ".agents", "skills", name), text)
    code, out, err = run(agents_home, args=(name,))
    try:
        ctx = context_of(out)
        failed += check("falls back to ~/.agents/skills", ctx == expected, f"got {ctx!r}")
    except (ValueError, KeyError) as exc:
        failed += check("falls back to ~/.agents/skills", False, f"{exc}: {out!r}")

    # CLAUDE_CONFIG_DIR wins over $HOME/.claude.
    cfg = os.path.join(tmp, f"{name}_cfg")
    write_skill(os.path.join(cfg, "skills", name), text.replace("Last line.", "From CLAUDE_CONFIG_DIR."))
    code, out, err = run(home, args=(name,), env_extra={"CLAUDE_CONFIG_DIR": cfg})
    try:
        ctx = context_of(out)
        failed += check("CLAUDE_CONFIG_DIR takes precedence",
                        ctx.endswith("From CLAUDE_CONFIG_DIR."), f"got {ctx!r}")
    except (ValueError, KeyError) as exc:
        failed += check("CLAUDE_CONFIG_DIR takes precedence", False, f"{exc}: {out!r}")

    # Only the requested skill is read: another name's copy must not leak in.
    other = "contributing" if name == "comments" else "comments"
    other_home = os.path.join(tmp, f"{name}_other_home")
    write_skill(os.path.join(other_home, ".claude", "skills", other), skill_text(other))
    code, out, err = run(other_home, args=(name,))
    failed += check("no skill for this name: empty stdout and exit 0",
                    code == 0 and out == "", out + err)

    # No skill anywhere: silent, exit 0.
    empty_home = os.path.join(tmp, f"{name}_empty_home")
    os.makedirs(empty_home)
    code, out, err = run(empty_home, args=(name,))
    failed += check("no skill: empty stdout and exit 0", code == 0 and out == "", out + err)

    # Empty body after frontmatter: silent, exit 0.
    blank_home = os.path.join(tmp, f"{name}_blank_home")
    write_skill(os.path.join(blank_home, ".claude", "skills", name), f"---\nname: {name}\n---\n\n")
    code, out, err = run(blank_home, args=(name,))
    failed += check("empty body: empty stdout and exit 0", code == 0 and out == "", out + err)

    return failed


if __name__ == "__main__":
    sys.exit(main())
