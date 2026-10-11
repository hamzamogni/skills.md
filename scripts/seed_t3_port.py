#!/usr/bin/env python3
"""Build a p3-derived candidate in a new directory. Never overwrite a live pack."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil

from skills import ROOT, files, run, transform, write_json

ALIASES = {"p3-mode": "poteto-mode", "p3-help": "poteto-help", "setup-p3": "setup-pstack"}
EXCLUDED = {
    "poteto-mode/scripts/": "Replaced by native T3 delegation, PR watches, scheduling, and thread/worktree tools",
    "poteto-help/references/": "Replaced by the rewritten help skill and maintained T3 runtime guide",
}


def mapped_path(path):
    first, *remaining = path.split("/")
    return "/".join((ALIASES.get(first, first), *remaining))


def rewrite(data, path, original=None):
    text = data.decode()
    text = text.replace("p3 agent style", "poteto agent style").replace("Use for p3,", "Use for poteto,")
    text = text.replace("configure p3 models", "configure pstack models").replace("p3 budget", "pstack budget")
    text = text.replace("https://github.com/uzairansaruzi/p3-stack/blob/main/",
                        "https://github.com/hamzamogni/skills.md/blob/main/skills/pstack/")
    text = text.replace("p3-models.md", ".pstack-models.md")
    for old, new in ALIASES.items():
        text = text.replace(old, new)
    text = text.replace("p3-stack", "pstack").replace("P3 mode", "Poteto mode")
    text = text.replace("P3 help", "Poteto help").replace("Setup p3", "Setup pstack")
    text = text.replace("P3 delegated worker", "Poteto delegated worker")
    text = text.replace("name: p3-agent", "name: poteto-agent")
    text = text.replace("# p3 model configuration", "# pstack model configuration")
    # Resolve bundled briefs from the file that mentions them, including playbooks.
    for old, new in (("agents/p3-agent.md", "poteto-agent.md"), ("agents/comment-sicko.md", "comment-sicko.md")):
        target = Path("poteto-mode/references/agents") / new
        import os
        relative = os.path.relpath(target, Path(path).parent).replace(os.sep, "/")
        text = text.replace(old, relative)
    if path.startswith("poteto-mode/references/agents/"):
        text = text.replace("skills/poteto-mode/SKILL.md", "../../SKILL.md")
    text = text.replace("[README](../../README.md)",
                        "[runtime and installation guide](../poteto-mode/references/t3-runtime.md)")
    if path.endswith("/SKILL.md"):
        parts = text.split("---", 2)
        front = re.sub(r"(?m)^name:.*$", f"name: {Path(path).parent.name}", parts[1])
        if original is not None:
            original_front = original.decode().split("---", 2)[1]
            invocation = re.search(r"(?m)^disable-model-invocation:.*$", original_front)
            front = re.sub(r"(?m)^disable-model-invocation:.*\n?", "", front)
            if invocation:
                front = front.rstrip() + "\n" + invocation[0] + "\n"
        runtime = "references/t3-runtime.md"
        text = "---" + front + "---\n\n" + f"Read the [T3 runtime contract]({runtime}) before executing this skill.\n\n" + parts[2].lstrip()
    return text.encode()


def build(reference, destination, root=ROOT):
    if destination.exists():
        raise ValueError("Use a new candidate directory; the generator never resets your editable skills")
    tracked = run("git", "rev-parse", "HEAD", cwd=reference).stdout.decode().strip()
    if run("git", "status", "--porcelain", cwd=reference).stdout:
        raise ValueError("The p3 reference checkout must be clean")
    source_files = files(root / "upstream/pstack/skills")
    reference_files = files(reference / "skills")
    policy = {}
    output = {}
    mapped = {mapped_path(path): path for path in reference_files}
    for path, data in source_files.items():
        excluded = next((reason for prefix, reason in EXCLUDED.items() if path.startswith(prefix)), None)
        if excluded:
            policy[path] = {"strategy": "excluded", "reason": excluded,
                            "upstream_sha256": hashlib.sha256(data).hexdigest()}
            continue
        if path in mapped:
            ref_path = mapped[path]
            output[path] = rewrite(reference_files[ref_path], path, original=data)
            policy[path] = {"strategy": "p3-rewrite", "reference_path": f"skills/{ref_path}"}
        else:
            output[path] = transform({path: data})[path]
            # The upstream-only ketchup skill is vendor neutral; replace the old bridge.
            from skills import BRIDGE
            text = output[path].decode().replace(BRIDGE, "\n\nRead the [T3 runtime contract](references/t3-runtime.md) before executing this skill.\n\n")
            output[path] = text.encode()
            policy[path] = {"strategy": "upstream-retained"}
        policy[path]["upstream_sha256"] = hashlib.sha256(data).hexdigest()
    # Carry p3 additions explicitly, so a future reference update is visible in the candidate.
    for path, ref_path in mapped.items():
        if path not in source_files:
            output[path] = rewrite(reference_files[ref_path], path)
            policy[path] = {"strategy": "p3-addition", "reference_path": f"skills/{ref_path}"}
    for ref_path in (reference / "agents").glob("*.md"):
        name = "poteto-agent.md" if ref_path.name == "p3-agent.md" else ref_path.name
        path = f"poteto-mode/references/agents/{name}"
        output[path] = rewrite(ref_path.read_bytes(), path)
        policy[path] = {"strategy": "support", "reference_path": f"agents/{ref_path.name}"}
    from porting import manifest, map_contents
    current_policy = manifest(root, "pstack") or {}
    output = map_contents(output, current_policy)
    destination.mkdir(parents=True)
    for path, data in output.items():
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        original = root / "upstream/pstack/skills" / path
        if original.exists():
            target.chmod(original.stat().st_mode & 0o777)
    shutil.copyfile(reference / "LICENSE", destination / "LICENSE")
    result = {
        "schema_version": 1,
        "reference": {"repository": "https://github.com/uzairansaruzi/p3-stack", "commit": tracked},
        "aliases": ALIASES,
        "excluded_prefixes": EXCLUDED,
        "files": policy,
    }
    for key in ("path_aliases", "skill_aliases"):
        if key in current_policy:
            result[key] = current_policy[key]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    if args.manifest.exists():
        parser.error("Use a new manifest path to avoid overwriting provenance")
    manifest = build(args.reference.resolve(), args.destination.resolve())
    write_json(args.manifest, manifest)
    print(f"Built candidate at {args.destination}; compare it with skills/pstack before accepting any changes")


if __name__ == "__main__":
    main()
