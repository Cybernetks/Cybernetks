"""Migration output must expose routes only, never Ghost account data."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

from tools.migration.ghost_manifest import build_manifest


GHOST_FIXTURE = {"db": [{"data": {
    "posts": [
        {"slug": "z-log", "type": "post", "status": "published", "id": "private-id",
         "html": "private-body", "email": "private@example.invalid", "lexical": "private-lexical"},
        {"slug": "about", "type": "page", "status": "published"},
        {"slug": "draft-log", "type": "post", "status": "draft"},
        {"slug": "scheduled-log", "type": "post", "status": "scheduled"},
        {"slug": "topics", "type": "page", "status": "published"},
        {"slug": "support", "type": "page", "status": "published"},
        {"slug": "uses", "type": "page", "status": "published"},
        {"slug": "cybernetks-planner", "type": "page", "status": "published"},
        {"slug": "projects", "type": "page", "status": "published"},
        {"slug": "operator-privacy", "type": "page", "status": "published"},
        {"slug": "operator-support", "type": "page", "status": "published"},
    ],
    "settings": [{"email": "private@example.invalid", "stripe": "private-payment"}],
    "members": [{"email": "member@example.invalid"}],
    "newsletters": [{"name": "private-newsletter"}],
}}]}


class GhostManifestTests(unittest.TestCase):
    def test_manifest_contains_only_public_route_fields(self):
        manifest = build_manifest(GHOST_FIXTURE)
        for entry in manifest:
            self.assertEqual(set(entry), {"path", "kind", "status", "replacement"})
        serialized = yaml.safe_dump(manifest)
        for private in ("email", "newsletter", "stripe", "private-", "member@", "lexical"):
            self.assertNotIn(private, serialized)

    def test_published_routes_are_sorted_with_explicit_page_replacements(self):
        manifest = build_manifest(GHOST_FIXTURE)
        self.assertEqual(manifest, [
            {"path": "/about/", "kind": "page", "status": "published", "replacement": "/about/"},
            {"path": "/cybernetks-planner/", "kind": "page", "status": "published", "replacement": "/projects/cybernetks-planner/"},
            {"path": "/operator-privacy/", "kind": "page", "status": "published", "replacement": "/projects/operator/privacy/"},
            {"path": "/operator-support/", "kind": "page", "status": "published", "replacement": "/projects/operator/support/"},
            {"path": "/projects/", "kind": "page", "status": "published", "replacement": "/projects/"},
            {"path": "/support/", "kind": "page", "status": "published", "replacement": "/support/"},
            {"path": "/topics/", "kind": "page", "status": "published", "replacement": "/logs/"},
            {"path": "/uses/", "kind": "page", "status": "published", "replacement": "/uses/"},
            {"path": "/z-log/", "kind": "post", "status": "published", "replacement": "/z-log/"},
        ])

    def test_cli_writes_only_the_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "private.json"
            target = root / "data" / "ghost.yaml"
            source.write_text(json.dumps(GHOST_FIXTURE))
            result = subprocess.run([sys.executable, "-m", "tools.migration.ghost_manifest",
                                     "--input", str(source), "--output", str(target)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(yaml.safe_load(target.read_text())), 9)
            self.assertNotIn("private", target.read_text())
            self.assertEqual(sorted(p.name for p in target.parent.iterdir()), ["ghost.yaml"])


if __name__ == "__main__":
    unittest.main()
