#!/usr/bin/env python3
"""Configure user MCP entries; preserve options and back up original settings."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import tempfile


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "tools/playwright-mcp/start.sh"


def server(args):
    return {"type": "stdio", "command": "/bin/bash", "args": [str(LAUNCHER)] + args}


def update_claude(text):
    data = json.loads(text) if text else {}
    servers = data.setdefault("mcpServers", {})
    if "playwright" in servers:
        entry = servers["playwright"]
        if entry.get("command") not in ("npx", "/bin/bash"):
            raise ValueError("Unrecognized Claude Playwright command; review manually")
        entry.update(server(browser_args(entry.get("args", []))))
    else:
        servers["playwright"] = server(["--browser", "chrome", "--user-data-dir", str(Path.home() / ".claude/playwright-profile")])
    count = 0
    for project in data.get("projects", {}).values():
        entry = project.get("mcpServers", {}).get("playwright")
        if entry:
            if entry.get("command") not in ("npx", "/bin/bash"):
                raise ValueError("Unrecognized project Playwright command; review manually")
            entry.update(server(browser_args(entry.get("args", []))))
            count += 1
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n", count


def browser_args(args):
    if args and args[0] == str(LAUNCHER):
        return args[1:]
    # Accept only the previously inspected npx invocation shape.
    rest = list(args)
    if rest and rest[0] in ("-y", "--yes"):
        rest.pop(0)
    if not rest or not re.fullmatch(r"@playwright/mcp(?:@[^\s]+)?", rest[0]):
        raise ValueError("Unrecognized Playwright arguments; review manually")
    return rest[1:]


def update_codex(text):
    pattern = r"(?ms)^\[mcp_servers\.playwright\][^\n]*\n(.*?)(?=^\[|\Z)"
    match = re.search(pattern, text)
    if not match:
        args = [str(LAUNCHER), "--browser", "chrome", "--user-data-dir", str(Path.home() / ".codex/playwright-profile")]
        return text.rstrip() + '\n\n[mcp_servers.playwright]\ncommand = "/bin/bash"\nargs = ' + json.dumps(args) + "\n"
    block = match.group(1)
    command = re.search(r'^command\s*=\s*("[^"\n]*")\s*$', block, re.M)
    arguments = re.search(r'^args\s*=\s*(\[[^\n]*\])\s*$', block, re.M)
    if not command or not arguments or json.loads(command.group(1)) not in ("npx", "/bin/bash"):
        raise ValueError("Unrecognized Codex Playwright configuration; review manually")
    args = [str(LAUNCHER)] + browser_args(json.loads(arguments.group(1)))
    block = re.sub(r'^command\s*=.*$', 'command = "/bin/bash"', block, flags=re.M)
    block = re.sub(r'^args\s*=.*$', lambda _: "args = " + json.dumps(args), block, flags=re.M)
    return text[:match.start(1)] + block + text[match.end(1):]


def write_atomic(path, content):
    # Existing symlinks remain symlinks, with only their target updated.
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o600
    fd, tmp = tempfile.mkstemp(dir=target.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(content)
        os.chmod(tmp, mode)
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "apply"])
    args = parser.parse_args()
    claude = Path.home() / ".claude.json"
    codex = Path.home() / ".codex/config.toml"
    old_claude = claude.read_text() if claude.exists() else ""
    old_codex = codex.read_text() if codex.exists() else ""
    new_claude, count = update_claude(old_claude)
    new_codex = update_codex(old_codex)
    # Avoid reformatting an otherwise already configured Claude settings file.
    if old_claude and json.loads(new_claude) == json.loads(old_claude):
        new_claude = old_claude
    changes = [(p, old, new) for p, old, new in [(claude, old_claude, new_claude), (codex, old_codex, new_codex)] if old != new]
    print("Claude project entries included:", count)
    for path, _, _ in changes:
        print("Update:", path.name)
    if args.command == "check":
        print("In sync" if not changes else "Configuration update required")
        return 1 if changes else 0
    if changes:
        backup_root = ROOT / ".skill-sync/mcp-config-backups"
        backup_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        backup_dir = Path(tempfile.mkdtemp(dir=backup_root))
        for path, old, _ in changes:
            backup = backup_dir / ("claude.json" if path == claude else "codex-config.toml")
            backup.write_text(old)
            backup.chmod(0o600)
        # Recheck both files before mutating either, in case an app wrote settings.
        for path, old, _ in changes:
            if (path.read_text() if path.exists() else "") != old:
                raise ValueError("Settings changed during configuration; retry")
        for path, _, new in changes:
            write_atomic(path, new)
        print("Saved backups under .skill-sync/mcp-config-backups")
    print("Configured")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        raise SystemExit(str(error))
