#!/usr/bin/env python3
"""Generate a review candidate of tool names from a clean T3 source checkout."""
import argparse
from pathlib import Path
import re

from skills import run, write_json


def inventory(reference):
    if run("git", "status", "--porcelain", cwd=reference).stdout:
        raise ValueError("The T3 reference checkout must be clean")
    revision = run("git", "rev-parse", "HEAD", cwd=reference).stdout.decode().strip()
    tools = {}
    for path in sorted((reference / "apps/server/src/mcp").rglob("tools.ts")):
        for name in re.findall(r'Tool\.make\(\s*"([a-z0-9_]+)"', path.read_text()):
            if name in tools:
                raise ValueError(f"Duplicate tool definition: {name}")
            tools[name] = path.relative_to(reference).as_posix()
    if not tools:
        raise ValueError("No T3 tool definitions found; inspect changed source layout before updating")
    return {"repository": "https://github.com/pingdotgg/t3code", "commit": revision,
            "tools": dict(sorted(tools.items()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new candidate output path; review before replacing the pinned inventory")
    try:
        result = inventory(args.reference.resolve())
        write_json(args.output, result)
    except ValueError as error:
        parser.exit(1, str(error) + "\n")
    print(f"Saved {len(result['tools'])} tool names at {result['commit']} to {args.output}")


if __name__ == "__main__":
    main()
