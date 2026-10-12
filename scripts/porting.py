"""Audit native T3 instructions and explain which upstream changes need review."""
import hashlib
from pathlib import Path
import re

from skills import files, read_json, write_json

LEGACY = re.compile(
    r"subagent_type|\.cursor/|agent-transcripts|\bAskQuestion\b|\bTask tool\b|/loop\b|"
    r"scripts/(?:watch-pr|orch)/|worktree-audit\.sh|\bp3-(?:mode|help|agent|models)\b|"
    r"poteto-models\.md|That guidance replaces Cursor-specific|\bSkill tool\b|/compact\b|/clear\b|claude --bg",
    re.IGNORECASE,
)
TOOL = re.compile(
    r"`((?:t3_|preview_|device_|html_)[a-z0-9_]+|delegate_task|task_status|task_cancel|"
    r"orchestrator_capabilities|watch_pull_request|unwatch_pull_request|"
    r"schedule_task|list_scheduled_tasks|update_scheduled_task|delete_scheduled_task|"
    r"run_scheduled_task_now|create_threads|link_pull_request|unlink_pull_request|"
    r"list_thread_pull_requests|request_secret|read_pull_request_guide|write_pull_request_guides)`"
)
HOTSPOTS = re.compile(
    r"Task|delegate|model|provider|worktree|branch|watch|schedule|poll|transcript|"
    r"agent-transcripts|\.cursor|AskQuestion|/loop|control-ui|control-cli|preview|device|"
    r"autonomy|merge|secret|permission|approval|resume|context",
    re.IGNORECASE,
)
STRATEGIES = ("native-rewrite", "upstream-retained", "excluded", "support", "p3-rewrite", "p3-addition")


def manifest(root, name):
    path = root / "ports" / f"{name}.json"
    return read_json(path) if path.exists() else None


def excluded(policy, path):
    entry = policy["files"].get(path, {})
    return entry.get("strategy") == "excluded" or any(
        path.startswith(prefix) for prefix in policy.get("excluded_prefixes", {}))


def mapped_path(policy, path):
    for old, new in (policy or {}).get("path_aliases", {}).items():
        if path.startswith(old):
            target = new + path[len(old):]
            if Path(target).is_absolute() or ".." in Path(target).parts:
                raise ValueError("Port aliases must remain inside the editable pack")
            return target
    return path


def original_path(policy, path):
    for old, new in (policy or {}).get("path_aliases", {}).items():
        if path.startswith(new):
            return old + path[len(new):]
    return path


def map_contents(contents, policy):
    """Apply explicit name migrations to both merge sides without changing transform."""
    result = {}
    for path, data in contents.items():
        target = mapped_path(policy, path)
        if target in result:
            raise ValueError(f"Port path aliases collide at {target}")
        if path.endswith((".md", ".yaml")):
            text = data.decode()
            for old, new in (policy or {}).get("skill_aliases", {}).items():
                for marker in ("`", '"', "'", "**"):
                    text = text.replace(f"{marker}{old}{marker}", f"{marker}{new}{marker}")
                text = re.sub(rf"(?<![\w./:-])[/\$]{re.escape(old)}\b(?!/)",
                              lambda m: m[0][0] + new, text)
                text = text.replace(f"../{old}/", f"../{new}/")
                text = text.replace(f"./{old}/", f"./{new}/")
                text = text.replace(f"[{old}]", f"[{new}]")
            if target.endswith("/SKILL.md"):
                text = re.sub(r"(?m)^name:.*$", f"name: {Path(target).parent.name}", text, count=1)
            data = text.encode()
        result[target] = data
    return result


def prose(text):
    """Ignore fenced examples when checking Markdown links, not runtime remnants."""
    return re.sub(r"(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$", "", text)


def audit(root, name):
    policy = manifest(root, name)
    if policy is None:
        return []
    pack = root / "skills" / name
    known_tools = read_json(root / "ports/t3-tools.json")["tools"]
    problems = []
    for path, entry in policy["files"].items():
        if entry.get("strategy") not in STRATEGIES:
            problems.append(f"Invalid mapping strategy: {path}")
    state = read_json(root / "adaptations.lock.json")[name]
    imported = read_json(root / "sources.lock.json")[name]
    from package_skills import bundle_sources
    bundled = {path.resolve() for path in bundle_sources(root)}
    bundled_guides = {path for path in bundled if path.name == "t3-runtime.md"}
    # Raw-only updates may be intentionally deferred; audit their coverage on adoption.
    if state["tree"] == imported["tree"] or state.get("pending_port"):
        for path in files(root / "upstream" / name / "skills"):
            if path not in policy["files"] and not excluded(policy, path):
                problems.append(f"Unmapped upstream file: {path}; classify it before accepting the port")
            elif not excluded(policy, path) and not (pack / mapped_path(policy, path)).is_file():
                problems.append(f"Mapped upstream file missing from installed pack: {path}; restore or exclude it")
    for path, data in files(pack).items():
        # Explicit, byte-checked native bundles may occupy an excluded references directory.
        if excluded(policy, original_path(policy, path)) and (pack / path).resolve() not in bundled:
            problems.append(f"Excluded upstream file reintroduced: {path}")
        if not path.endswith(".md"):
            continue
        text = data.decode()
        # The runtime guide documents the historical mapping itself.
        if (pack / path).resolve() not in bundled_guides and path != "poteto-mode/references/t3-runtime.md" and path not in policy.get("runtime_guides", []):
            for match in LEGACY.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                problems.append(f"{path}:{line}: legacy runtime instruction {match[0]!r}")
        for tool in TOOL.findall(text):
            if tool not in known_tools:
                problems.append(f"{path}: {tool} is absent from the pinned T3 tool inventory")
        for target in re.findall(r"\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", prose(text)):
            target = target.split("#", 1)[0]
            if not target or "://" in target or target.startswith(("mailto:", "/")):
                continue
            if any(symbol in target for symbol in ("<", ">", "{", "}", "*")):
                continue
            if not ((pack / path).parent / target).exists():
                problems.append(f"{path}: broken local link {target}")
    return sorted(set(problems))


def report(root, name, save_diff=False):
    policy = manifest(root, name)
    if policy is None:
        raise ValueError(f"No port map for {name}")
    incoming = files(root / "upstream" / name / "skills")
    rows = []
    for path in sorted(incoming.keys() | policy["files"].keys()):
        entry = policy["files"].get(path, {})
        if "upstream_sha256" not in entry and path not in incoming:
            continue
        data = incoming.get(path)
        digest = hashlib.sha256(data).hexdigest() if data is not None else None
        if digest == entry.get("upstream_sha256"):
            continue
        status = "deleted" if data is None else "added" if "upstream_sha256" not in entry else "changed"
        if excluded(policy, path):
            action = "Excluded runtime file; inspect upstream intent and keep it out of the installed pack"
        elif path not in policy["files"]:
            action = "NEW: port the file and classify its mapping"
        else:
            hits = sorted({m[0].lower() for m in HOTSPOTS.finditer(data.decode(errors="replace"))}) if data else []
            action = "Review native workflow and tool arguments" if hits else "Review meaning and local edits"
            if hits:
                action += "; terms: " + ", ".join(hits[:10])
        target = mapped_path(policy, path)
        if target != path:
            action += f"; adapted path: `{target}`"
        rows.append(f"| `{path}` | {status} | {action} |")
    text = "# Upstream update review\n\n"
    text += "This compares the imported snapshot with the last adopted file hashes in the port map.\n"
    text += "A clean text merge does not prove that a T3 workflow remains correct.\n\n"
    text += "| File | Change | What to review |\n| --- | --- | --- |\n"
    text += "\n".join(rows) if rows else "| None | unchanged | The port map matches the imported skill files |"
    text += "\n\nRun `merge` only after reviewing this list, then run `validate` and exercise changed workflows in T3.\n"
    target = root / ".work" / f"{name}-update.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    print(text)
    print(f"\nSaved {target}")
    if save_diff:
        import tempfile
        from skills import fetch, run, source
        state = read_json(root / "adaptations.lock.json")[name]
        base = state.get("merge_base", state)
        with tempfile.TemporaryDirectory() as temporary:
            old = Path(temporary) / "base"
            fetch(source(root, name), old, base["commit"])
            result = run("git", "diff", "--no-index", "--", str(old / "skills"),
                         str(root / "upstream" / name / "skills"), check=False)
            if result.returncode not in (0, 1):
                raise RuntimeError(result.stderr.decode())
            diff_path = root / ".work" / f"{name}-upstream.diff"
            diff_path.write_bytes(result.stdout)
            print(f"Full upstream diff since {base['commit']}: {diff_path}")
    return rows


def adopt_hashes(root, name):
    policy = manifest(root, name)
    if policy is None:
        return
    incoming = files(root / "upstream" / name / "skills")
    for path in incoming:
        if path not in policy["files"] and excluded(policy, path):
            policy["files"][path] = {"strategy": "excluded", "reason": "Covered by an excluded prefix"}
    for path, entry in policy["files"].items():
        if path in incoming:
            entry["upstream_sha256"] = hashlib.sha256(incoming[path]).hexdigest()
        else:
            entry.pop("upstream_sha256", None)
    write_json(root / "ports" / f"{name}.json", policy)


def classify(root, name, path, strategy, reason):
    policy = manifest(root, name)
    if policy is None:
        raise ValueError(f"No port map for {name}")
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Use a path relative to the upstream skills directory")
    data = (root / "upstream" / name / "skills" / relative).read_bytes()
    policy["files"][relative.as_posix()] = {
        "strategy": strategy, "reason": reason,
        "upstream_sha256": hashlib.sha256(data).hexdigest(),
    }
    write_json(root / "ports" / f"{name}.json", policy)
    print(f"Classified {path} as {strategy}; review and commit the port map with the skill")
