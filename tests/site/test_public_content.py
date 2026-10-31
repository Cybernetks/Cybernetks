from pathlib import Path
import re
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "generated/content"
REVIEW_MONTH = re.compile(r"^\d{4}-\d{2}$")


def public_pages():
    for path in sorted(CONTENT.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if len(parts) != 3:
            continue
        metadata = yaml.safe_load(parts[1])
        if isinstance(metadata, dict) and "url" in metadata:
            yield path, text, metadata


class PublicContentBoundaryTest(unittest.TestCase):
    def test_public_content_contains_no_bear_wikilinks(self) -> None:
        offenders = [path for path in CONTENT.rglob("*.md") if "[[" in path.read_text(encoding="utf-8")]

        self.assertEqual(offenders, [], "Bear wikilinks must not cross the public boundary")

    def test_public_routes_are_unique_and_canonical(self) -> None:
        routes: dict[str, Path] = {}
        for path, _, metadata in public_pages():
            route = metadata["url"]
            with self.subTest(path=path):
                self.assertIsInstance(route, str)
                self.assertTrue(route.startswith("/"))
                self.assertTrue(route.endswith("/"))
                self.assertNotIn(route, routes, f"also declared by {routes.get(route)}")
            routes[route] = path

    def test_snapshot_metadata_matches_its_bundle(self) -> None:
        for path in sorted((CONTENT / "snapshots").glob("*/index.md")):
            text = path.read_text(encoding="utf-8")
            metadata = yaml.safe_load(text.split("---", 2)[1])
            params = metadata.get("params", {})
            with self.subTest(path=path):
                review_month = params.get("review_month")
                self.assertIsInstance(review_month, str)
                self.assertRegex(review_month, REVIEW_MONTH)
                self.assertEqual(review_month, path.parent.name)
                self.assertEqual(params.get("kind"), "snapshot")


if __name__ == "__main__":
    unittest.main()
