#!/usr/bin/env python3
"""Import a Git subtree, merge an editable skill pack, and install project links."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = '''\n## T3 Code runtime\n\nRead [T3 Code runtime guidance](../poteto-mode/references/t3-runtime.md) before\nfollowing the workflow below. That guidance replaces Cursor-specific tool, model,\nconfiguration, and history instructions in this skill and its references.\n\n'''


def run(*args, cwd=None, check=True):
    return subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=check,
                          env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def source(root, name):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        raise ValueError("Source names must contain lowercase letters, digits, or hyphens")
    return read_json(root / "sources.json")[name]


def fetch(config, destination, ref=None):
    """Download Git metadata and only the selected subtree's file contents."""
    subtree = config["path"]
    if not subtree or (subtree != "." and any(p in ("", ".", "..") for p in subtree.split("/"))):
        raise ValueError("Invalid upstream subtree")
    included = config.get("include")
    if included is not None:
        if not included or any(not p or p.startswith("/") or any(x in ("", ".", "..") for x in p.split("/")) for p in included):
            raise ValueError("Invalid import include paths")
    with tempfile.TemporaryDirectory() as temporary:
        checkout = Path(temporary)
        run("git", "init", "--quiet", str(checkout))
        run("git", "remote", "add", "origin", config["url"], cwd=checkout)
        run("git", "fetch", "--quiet", "--depth=1", "--filter=blob:none",
            "origin", ref or config["branch"], cwd=checkout)
        commit = run("git", "rev-parse", "FETCH_HEAD", cwd=checkout).stdout.decode().strip()
        selected = commit if subtree == "." else f"{commit}:{subtree}"
        if included is None:
            tree = run("git", "rev-parse", f"{commit}^{{tree}}" if subtree == "." else selected, cwd=checkout).stdout.decode().strip()
        else:
            entries = run("git", "ls-tree", selected, "--", *included, cwd=checkout).stdout
            if len(entries.splitlines()) != len(included):
                raise ValueError("Every include path must exist and be a distinct Git tree entry")
            tree = hashlib.sha256(entries).hexdigest()
        archive = run("git", "archive", selected, *(included or []), cwd=checkout).stdout
        destination.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            members = tar.getmembers()
            for member in members:
                parts = Path(member.name).parts
                if member.name.startswith("/") or ".." in parts or not (member.isfile() or member.isdir()):
                    raise ValueError(f"Unsupported archive entry: {member.name}")
            tar.extractall(destination, members=members)
    license_path = Path(config.get("license", "LICENSE"))
    if license_path.is_absolute() or ".." in license_path.parts or not (destination / license_path).is_file():
        raise ValueError("Imported packs must include their configured license file")
    return {"commit": commit, "tree": tree}


def files(path):
    result = {}
    if path.exists():
        for entry in path.rglob("*"):
            if entry.is_symlink():
                raise ValueError(f"Symlink is not supported in a pack: {entry}")
            if entry.is_file():
                result[entry.relative_to(path).as_posix()] = entry.read_bytes()
    return result


def replace_files(path, contents):
    modes = {name: (path / name).stat().st_mode & 0o777 for name in files(path)}
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    for name, data in contents.items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if name in modes:
            target.chmod(modes[name])


def transform(contents, pack="pstack"):
    """The same small, repeatable port is applied to both sides of a merge."""
    result = dict(contents)
    for name, data in contents.items():
        if not name.endswith("/SKILL.md"):
            continue
        text = data.decode()
        parts = text.split("---", 2)
        if len(parts) != 3 or parts[0].strip():
            raise ValueError(f"Invalid frontmatter: {name}")
        folder = Path(name).parent.name
        front = re.sub(r"(?m)^name:.*$", f"name: {folder}", parts[1])
        # Cursor UI metadata has no equivalent in Codex or Claude skill files.
        front = re.sub(r"(?m)^(mode|icon|color|reminder):.*\n?", "", front)
        bridge = BRIDGE if pack == "pstack" else "\n"
        result[name] = ("---" + front + "---\n" + bridge + parts[2].lstrip()).encode()
    return result


def snapshot(root, name):
    config = source(root, name)
    lock_path = root / "sources.lock.json"
    lock = read_json(lock_path) if lock_path.exists() else {}
    with tempfile.TemporaryDirectory() as temporary:
        incoming = Path(temporary) / "incoming"
        revision = fetch(config, incoming)
        if lock.get(name, {}).get("tree") == revision["tree"]:
            print(f"{name}: upstream subtree is unchanged")
            return False
        destination = root / "upstream" / name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(incoming, destination)
        lock[name] = revision
        write_json(lock_path, lock)
    print(f"{name}: imported {revision['commit']} ({revision['tree']})")
    return True


def merge_file(base, ours, theirs):
    if ours == base:
        return theirs, False
    if theirs == base or ours == theirs:
        return ours, False
    if base is None or ours is None or theirs is None or any(b"\0" in x for x in (base, ours, theirs)):
        return ours, True
    with tempfile.TemporaryDirectory() as temporary:
        paths = [Path(temporary) / label for label in ("ours", "base", "upstream")]
        for path, data in zip(paths, (ours, base, theirs)):
            path.write_bytes(data)
        result = run("git", "merge-file", "-p", "--diff3", "-L", "ours", "-L", "base",
                     "-L", "upstream", *(str(p) for p in paths), check=False)
        if result.returncode < 0 or result.returncode > 127:
            raise RuntimeError(result.stderr.decode())
        return result.stdout, result.returncode != 0


def initialize(root, name):
    pack = root / "skills" / name
    if pack.exists():
        raise ValueError(f"Editable pack already exists: {pack}")
    snapshot(root, name)
    upstream = root / "upstream" / name
    if not list((upstream / "skills").rglob("SKILL.md")):
        raise ValueError("The selected subtree must contain skills/<name>/SKILL.md folders")
    shutil.copytree(upstream / "skills", pack)
    for path, data in transform(files(pack), name).items():
        (pack / path).write_bytes(data)
    shutil.copyfile(upstream / source(root, name).get("license", "LICENSE"), pack / "LICENSE")
    lock_path = root / "adaptations.lock.json"
    lock = read_json(lock_path) if lock_path.exists() else {}
    lock[name] = read_json(root / "sources.lock.json")[name]
    write_json(lock_path, lock)
    print(f"{name}: created editable pack")


def merge(root, name, continuing=False):
    from porting import adopt_hashes, excluded, manifest, report, map_contents, original_path
    config = source(root, name)
    upstream = read_json(root / "sources.lock.json")[name]
    lock_path = root / "adaptations.lock.json"
    lock = read_json(lock_path)
    state = lock[name]
    pack = root / "skills" / name
    conflict_dir = root / ".sync-conflicts" / name
    if continuing:
        if not state.get("conflicts") and not state.get("pending_port"):
            raise ValueError("There is no pending merge")
        if state["tree"] != upstream["tree"]:
            raise ValueError("The raw snapshot advanced during this pending merge; restore the pending snapshot or discard and restart the merge")
        validate(root, allow_pending=True)
        state.pop("conflicts", None)
        state.pop("pending_port", None)
        state.pop("merge_base", None)
        if conflict_dir.exists():
            shutil.rmtree(conflict_dir)
        adopt_hashes(root, name)
        write_json(lock_path, lock)
        print(f"{name}: resolutions accepted; review the diff and commit")
        return
    if state.get("conflicts") or state.get("pending_port"):
        raise ValueError("Resolve the pending merge and run merge --continue first")
    if state["tree"] == upstream["tree"]:
        print(f"{name}: adapted skills are already based on the current snapshot")
        return
    policy = manifest(root, name)
    if policy is not None:
        report(root, name)
    with tempfile.TemporaryDirectory() as temporary:
        old = Path(temporary) / "old"
        fetch(config, old, state["commit"])
        base = map_contents(transform(files(old / "skills"), name), policy)
        base["LICENSE"] = (old / config.get("license", "LICENSE")).read_bytes()
    ours = files(pack)
    theirs = map_contents(transform(files(root / "upstream" / name / "skills"), name), policy)
    theirs["LICENSE"] = (root / "upstream" / name / config.get("license", "LICENSE")).read_bytes()
    output, conflicts = dict(ours), []
    for path in sorted(base.keys() | theirs.keys()):
        if policy is not None and excluded(policy, original_path(policy, path)):
            continue
        data, conflict = merge_file(base.get(path), ours.get(path), theirs.get(path))
        if data is None:
            output.pop(path, None)
        else:
            output[path] = data
        if conflict:
            conflicts.append(path)
            for label, mapping in (("base", base), ("ours", ours), ("upstream", theirs)):
                artifact = conflict_dir / label / path
                if path in mapping:
                    artifact.parent.mkdir(parents=True, exist_ok=True)
                    artifact.write_bytes(mapping[path])
    replace_files(pack, output)
    lock[name] = dict(upstream)
    if policy is not None:
        lock[name]["pending_port"] = True
        lock[name]["merge_base"] = {"commit": state["commit"], "tree": state["tree"]}
    if conflicts:
        lock[name]["conflicts"] = conflicts
    write_json(lock_path, lock)
    print(f"{name}: merged snapshot into editable skills; {len(conflicts)} conflicts")
    if conflicts:
        print("Resolve the listed files, including deletion or binary choices, then run merge --continue:")
        print("\n".join(conflicts))
    if policy is not None:
        print("Review native mappings even after a clean merge, then run merge --continue to accept the port")


def validate(root, allow_pending=False):
    lock_path = root / "adaptations.lock.json"
    if lock_path.exists() and not allow_pending:
        for name, state in read_json(lock_path).items():
            if state.get("conflicts") or state.get("pending_port"):
                raise ValueError(f"{name}: unresolved upstream merge")
    seen_names = {}
    for path in (root / "skills").rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes()
        if re.search(rb"(?m)^(<<<<<<< |\|\|\|\|\|\|\| |=======\r?$|>>>>>>> )", data):
            raise ValueError(f"Unresolved merge marker: {path}")
        if path.name != "SKILL.md":
            continue
        text = data.decode()
        parts = text.split("---", 2)
        if len(parts) != 3 or parts[0].strip():
            raise ValueError(f"Invalid frontmatter: {path}")
        name = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", parts[1])
        if not name or name[1] != path.parent.name or not re.search(r"(?m)^description:\s*\S", parts[1]):
            raise ValueError(f"Invalid name or description: {path}")
        if name[1] in seen_names:
            raise ValueError(f"Duplicate skill names: {name[1]} in {seen_names[name[1]]} and {path}")
        seen_names[name[1]] = path
    print("Skill names, descriptions, and merge state are valid")
    from package_skills import check
    check(root)
    from porting import audit
    for policy in sorted((root / "ports").glob("*.json")):
        if policy.name == "t3-tools.json":
            continue
        problems = audit(root, policy.stem)
        if problems:
            raise ValueError("T3 port audit failed:\n" + "\n".join(problems))


def install(root, project, provider):
    validate(root)
    project = project.resolve()
    if not project.is_dir():
        raise ValueError(f"Project directory does not exist: {project}")
    destination = project / (".agents/skills" if provider == "codex" else ".claude/skills")
    candidates = []
    for entry in sorted((root / "skills").iterdir()):
        if (entry / "SKILL.md").is_file():
            candidates.append(entry)
        else:
            candidates.extend(p.parent for p in sorted(entry.rglob("SKILL.md")))
    names = [p.name for p in candidates]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate skill names across personal and imported skills")
    # Only declared, collection-owned alias links can be migrated automatically.
    legacy_targets = set()
    for policy_path in (root / "ports").glob("*.json"):
        policy = read_json(policy_path)
        for old in policy.get("path_aliases", {}):
            legacy_targets.add((Path(old).name, (root / "skills" / policy_path.stem / old).resolve()))
    migrations = []
    # Preflight the whole plan before creating a link.
    for entry in candidates:
        target = destination / entry.name
        if target.exists() or target.is_symlink():
            if target.is_symlink() and (target.name, target.resolve()) in legacy_targets:
                migrations.append(target)
            elif not target.is_symlink() or target.resolve() != entry.resolve():
                raise ValueError(f"Refusing to replace an existing skill: {target}")
    if destination.exists():
        migrations.extend(target for target in destination.iterdir()
                          if target.is_symlink() and (target.name, target.resolve()) in legacy_targets and target not in migrations)
    for target in migrations:
        target.unlink()
    destination.mkdir(parents=True, exist_ok=True)
    for entry in candidates:
        target = destination / entry.name
        if not target.is_symlink():
            target.symlink_to(entry.resolve(), target_is_directory=True)
    print(f"Linked {len(candidates)} skills into {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "sync", "merge", "report"):
        child = sub.add_parser(command)
        child.add_argument("source", choices=read_json(ROOT / "sources.json"))
        if command == "merge":
            child.add_argument("--continue", dest="continuing", action="store_true")
        elif command == "report":
            child.add_argument("--diff", action="store_true", help="Save the full upstream diff since the adaptation base")
    sub.add_parser("validate")
    child = sub.add_parser("classify")
    child.add_argument("source", choices=read_json(ROOT / "sources.json"))
    child.add_argument("path")
    child.add_argument("--strategy", choices=("native-rewrite", "upstream-retained", "excluded"), required=True)
    child.add_argument("--reason", required=True)
    child = sub.add_parser("install")
    child.add_argument("--project", type=Path, required=True)
    child.add_argument("--provider", choices=("codex", "claude"), required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            initialize(ROOT, args.source)
        elif args.command == "sync":
            snapshot(ROOT, args.source)
        elif args.command == "merge":
            merge(ROOT, args.source, args.continuing)
        elif args.command == "report":
            from porting import report
            report(ROOT, args.source, save_diff=args.diff)
        elif args.command == "classify":
            from porting import classify
            classify(ROOT, args.source, args.path, args.strategy, args.reason)
        elif args.command == "validate":
            validate(ROOT)
        else:
            install(ROOT, args.project, args.provider)
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        detail = error.stderr.decode() if isinstance(error, subprocess.CalledProcessError) else str(error)
        parser.exit(1, detail + "\n")


if __name__ == "__main__":
    main()
