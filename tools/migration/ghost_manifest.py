"""Extract public routes without copying Ghost content or account metadata."""

import argparse
import json
from pathlib import Path

import yaml


PAGE_REPLACEMENTS = {
    "/about/": "/about/",
    "/topics/": "/logs/",
    "/uses/": "/uses/",
    "/support/": "/projects/operator/support/",
    "/cybernetks-planner/": "/projects/cybernetks-planner/",
    "/projects/": "/projects/",
    "/operator-privacy/": "/projects/operator/privacy/",
    "/operator-support/": "/projects/operator/support/",
}


def build_manifest(export: dict) -> list[dict[str, str]]:
    """Select only the public route fields from published Ghost posts/pages."""
    entries = []
    for post in export["db"][0]["data"]["posts"]:
        if post["status"] != "published":
            continue
        path = f"/{post['slug']}/"
        kind = post["type"]
        entries.append({
            "path": path,
            "kind": kind,
            "status": "published",
            "replacement": PAGE_REPLACEMENTS.get(path, path) if kind == "page" else path,
        })
    return sorted(entries, key=lambda entry: entry["path"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    manifest = build_manifest(json.loads(arguments.input.read_text(encoding="utf-8")))
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    print(f"Extracted {len(manifest)} public routes")


if __name__ == "__main__":
    main()
