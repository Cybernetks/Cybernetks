"""Keep the command used by CI connected to every site regression suite."""

from pathlib import Path
import unittest


class TestDiscoveryTest(unittest.TestCase):
    def test_standard_discovery_includes_page_and_migration_regressions(self) -> None:
        # A non-package site directory plus a partial bridge silently skipped these suites.
        root = Path(__file__).resolve().parents[1]
        suite = unittest.TestLoader().discover(str(root / "tests"), pattern="test_*.py")

        def cases(items):
            for item in items:
                if isinstance(item, unittest.TestSuite):
                    yield from cases(item)
                else:
                    yield item.id()

        discovered = list(cases(suite))
        for name in (
            "test_snapshot_has_aligned_numbered_sections",
            "test_launching_project_links_to_latest_update",
            "test_homepage_places_projects_before_latest_publications",
            "test_project_owned_page_links_back_to_its_project",
            "test_pages_workflow_builds_before_deploying",
            "test_40_noncanonical_identity_routes_cannot_bypass_route_coverage",
        ):
            with self.subTest(name=name):
                self.assertEqual(sum(case.endswith("." + name) for case in discovered), 1)
