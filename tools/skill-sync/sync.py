#!/usr/bin/env python3
"""Synchronize explicitly classified Claude skills. Python 3.9+, stdlib only."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile


class SyncError(Exception):
    pass


def digest(path):
    """Hash contents, modes and symlink targets without following directory links."""
    if path.is_symlink():
        return "link:" + os.readlink(path)
    if not path.exists():
        return None
    h = hashlib.sha256()
    paths = [path] if path.is_file() else sorted(path.rglob("*"))
    for item in paths:
        h.update(str(item.relative_to(path) if item != path else ".").encode())
        if item.is_symlink():
            h.update(b"L" + os.readlink(item).encode())
        elif item.is_file():
            h.update(b"F" + str(item.stat().st_mode & 0o777).encode())
            h.update(item.read_bytes())
        else:
            h.update(b"D")
    return h.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def safe_name(name):
    return bool(re.fullmatch(r"cyk-[a-z0-9][a-z0-9-]*", name))


def load(root):
    config = json.loads((root / "tools/skill-sync/config.json").read_text())
    if config.get("version") != 1:
        raise SyncError("Unsupported configuration version")
    state_path = root / ".skill-sync/state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {"version": 1, "outputs": {}}
    if state.get("version") != 1:
        raise SyncError("Unsupported state version")
    for name in set(config["skills"]) | set(state["outputs"]):
        if not safe_name(name):
            raise SyncError("Invalid skill name: " + name)
    return config, state


def desired(root, name, entry, work):
    source = root / ".claude/skills" / name
    if "SKILL.md" not in {p.name for p in source.iterdir()} or not (source / "SKILL.md").is_file():
        raise SyncError(name + ": SKILL.md is missing (case-sensitive)")
    mode = entry["mode"]
    target = work / name
    if mode == "link":
        target.symlink_to(source, target_is_directory=True)
    elif mode == "overlay":
        if entry.get("source_digest") != digest(source):
            raise SyncError(name + ": original changed; review the overlay and update source_digest")
        overlay = root / "tools/skill-sync/overrides" / name
        if not overlay.is_dir() or overlay.is_symlink():
            raise SyncError(name + ": overlay directory is missing or is a link")
        # Materialize resource links so overlay writes never follow them into the original.
        shutil.copytree(source, target, symlinks=False)
        for item in overlay.rglob("*"):
            if item.is_symlink():
                raise SyncError(name + ": links are not allowed in overlays")
        shutil.copytree(overlay, target, dirs_exist_ok=True)
    else:
        raise SyncError(name + ": unsupported mode " + str(mode))
    return target


def plan(root, config, state, work, adopt=False):
    source_dir = root / ".claude/skills"
    output_dir = root / ".agents/skills"
    errors, actions, notes = [], [], []
    sources = {p.name for p in source_dir.iterdir() if p.name.startswith("cyk-") and p.is_dir()}
    entries = config["skills"]
    for name in sorted(sources - entries.keys()):
        errors.append(name + ": unclassified; add link, overlay or exclude to config.json")
    for name in sorted(entries.keys() - sources):
        errors.append(name + ": original removed; remove its config entry too")
    names = sources | set(state["outputs"])
    # Existing unmanaged cyk entries require explicit adoption, including retired copies.
    if output_dir.exists():
        names |= {p.name for p in output_dir.iterdir() if p.name.startswith("cyk-")}
    for name in sorted(names):
        if not safe_name(name):
            errors.append("Invalid output name: " + name)
            continue
        entry = entries.get(name) if name in sources else None
        expected = None
        if entry:
            if not entry.get("reason"):
                errors.append(name + ": classification requires a reason")
                continue
            if entry.get("mode") == "exclude":
                notes.append(name + ": excluded — " + entry["reason"])
            else:
                try:
                    expected = desired(root, name, entry, work)
                except (SyncError, OSError) as error:
                    errors.append(str(error))
                    continue
        current = output_dir / name
        actual = digest(current)
        recorded = state["outputs"].get(name)
        wanted = digest(expected) if expected else None
        if actual is not None and recorded is None:
            if not adopt:
                errors.append(name + ": unmanaged output; inspect it, then use apply --adopt-existing")
                continue
            actions.append(("adopt", name, expected, actual))
        elif actual is not None and actual != recorded:
            errors.append(name + ": output was edited; preserve the change in overrides first")
        elif actual != wanted or (recorded is not None and wanted is None):
            actions.append(("update" if wanted else "remove", name, expected, actual))
    return actions, errors, notes


def validate_paths(root):
    # No redirected parent directories for managed writes.
    for relative in [".agents", ".agents/skills", ".skill-sync", "tools/skill-sync"]:
        path = root / relative
        if path.is_symlink():
            raise SyncError("Managed directory must not be a symlink: " + relative)


def synchronize(root, command, adopt=False):
    root = root.resolve()
    validate_paths(root)
    config, state = load(root)
    with tempfile.TemporaryDirectory(prefix="skill-sync-") as temp:
        actions, errors, notes = plan(root, config, state, Path(temp), adopt)
        for note in notes:
            print("EXCLUDE " + note)
        for action, name, _, _ in actions:
            print(action.upper() + " " + name)
        for error in errors:
            print("ERROR " + error, file=sys.stderr)
        if errors:
            return 2
        if command == "check":
            print("In sync" if not actions else "Synchronization required")
            return 1 if actions else 0
        output = root / ".agents/skills"
        output.mkdir(parents=True, exist_ok=True)
        state_path = root / ".skill-sync/state.json"
        # Back up before replacement and persist ownership after each operation.
        # Backups remain recoverable even if a later operation fails.
        for action, name, expected, before in actions:
            current = output / name
            if digest(current) != before:
                raise SyncError(name + ": output changed during sync; retry")
            if before is not None:
                backup_root = root / ".skill-sync/backups"
                backup_root.mkdir(parents=True, exist_ok=True)
                backup = Path(tempfile.mkdtemp(prefix=name + "-", dir=backup_root)) / name
                current.rename(backup)
                print("BACKUP " + str(backup.relative_to(root)))
            if expected is not None:
                if expected.is_symlink():
                    current.symlink_to(os.readlink(expected), target_is_directory=True)
                else:
                    shutil.copytree(expected, current, symlinks=True)
                state["outputs"][name] = digest(current)
            else:
                state["outputs"].pop(name, None)
            write_json(state_path, state)
        print("Applied " + str(len(actions)) + " change(s)")
        return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "apply"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--adopt-existing", action="store_true", help="back up and adopt existing cyk outputs")
    args = parser.parse_args()
    if args.adopt_existing and args.command != "apply":
        parser.error("--adopt-existing requires apply")
    try:
        # check is read-only. apply is serialized across AI sessions.
        if args.command == "apply":
            validate_paths(args.root.resolve())
            lock_dir = args.root / ".skill-sync"
            lock_dir.mkdir(parents=True, exist_ok=True)
            with (lock_dir / "lock").open("a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                return synchronize(args.root, args.command, args.adopt_existing)
        return synchronize(args.root, args.command)
    except (SyncError, OSError, ValueError, KeyError) as error:
        print("ERROR " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
