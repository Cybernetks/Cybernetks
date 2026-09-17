from pathlib import Path
import shutil
import tempfile
import unittest

import yaml

from tests.site.build import ROOT, build_site
from tests.site.html_contract import check_public_tree


class LegacyRouteContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.public = build_site()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.public)

    def test_every_ghost_path_has_a_page_or_redirect(self) -> None:
        # Removing a generated legacy alias would break a public Ghost URL.
        errors = check_public_tree(self.public, ROOT / "data/migration/ghost.yaml")

        self.assertEqual(errors, [])

    def manifest_entries(self) -> list[dict[str, str]]:
        return [
            dict(entry)
            for entry in yaml.safe_load(
                (ROOT / "data/migration/ghost.yaml").read_text(encoding="utf-8")
            )
        ]

    def test_valid_40_route_manifest_passes_without_normalization(self) -> None:
        entries = self.manifest_entries()
        self.assertEqual(len(entries), 40)
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "ghost.yaml"
            manifest.write_text(yaml.safe_dump(entries, sort_keys=False), encoding="utf-8")

            errors = check_public_tree(self.public, manifest)

        self.assertEqual(errors, [])

    def test_noncanonical_route_spellings_are_rejected_before_output_lookup(self) -> None:
        variants = (
            "/./",
            "/././",
            "//",
            "/foo//bar/",
            "/foo/../bar/",
            "/foo\\bar/",
            "/%2e/",
            "/foo%2Fbar/",
            "/foo?bar/",
            "/foo#bar/",
        )
        for field in ("path", "replacement"):
            for route in variants:
                entries = self.manifest_entries()
                entries[0][field] = route
                with tempfile.TemporaryDirectory() as directory:
                    manifest = Path(directory) / "ghost.yaml"
                    manifest.write_text(
                        yaml.safe_dump(entries, sort_keys=False), encoding="utf-8"
                    )

                    errors = check_public_tree(self.public, manifest)

                self.assertIn(
                    f"invalid migration entry 1: invalid {field} route: {route}",
                    errors,
                )

    def test_40_noncanonical_identity_routes_cannot_bypass_route_coverage(self) -> None:
        entries = self.manifest_entries()
        collapsing_routes = ["//"] + ["/" + "./" * depth for depth in range(1, 35)]
        for index, route in enumerate(collapsing_routes):
            entries[index]["path"] = route
            entries[index]["replacement"] = route
        for entry in entries[35:]:
            entry["replacement"] = entry["path"]

        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "ghost.yaml"
            manifest.write_text(yaml.safe_dump(entries, sort_keys=False), encoding="utf-8")

            errors = check_public_tree(self.public, manifest)

        self.assertIn("invalid migration entry 1: invalid path route: //", errors)
        self.assertIn("invalid migration entry 2: invalid path route: /./", errors)
        self.assertIn("invalid migration entry 3: invalid path route: /././", errors)

    def test_legacy_path_cannot_claim_the_root_output(self) -> None:
        entries = self.manifest_entries()
        entries[0]["path"] = "/"
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "ghost.yaml"
            manifest.write_text(yaml.safe_dump(entries, sort_keys=False), encoding="utf-8")

            errors = check_public_tree(self.public, manifest)

        self.assertIn("invalid migration entry 1: invalid path route: /", errors)

    def test_missing_legacy_route_names_the_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            broken_public = Path(directory) / "public"
            shutil.copytree(self.public, broken_public)
            shutil.rmtree(broken_public / "operator-support")

            errors = check_public_tree(
                broken_public, ROOT / "data/migration/ghost.yaml"
            )

        self.assertIn("missing legacy route: /operator-support/", errors)

    def test_incomplete_manifest_entry_is_not_silently_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "ghost.yaml"
            manifest.write_text(
                "- path: /operator-support/\n  kind: page\n",
                encoding="utf-8",
            )

            errors = check_public_tree(self.public, manifest)

        self.assertIn(
            "invalid migration entry 1: expected fields kind, path, replacement, status",
            errors,
        )

    def test_quoted_reordered_manifest_entries_still_cover_legacy_routes(self) -> None:
        entries = yaml.safe_load(
            (ROOT / "data/migration/ghost.yaml").read_text(encoding="utf-8")
        )
        manifest_text = "\n".join(
            "\n".join(
                (
                    f"- replacement: \"{entry['replacement']}\"",
                    f"  status: \"{entry['status']}\"",
                    f"  kind: \"{entry['kind']}\"",
                    f"  path: \"{entry['path']}\"",
                )
            )
            for entry in entries
        )
        with tempfile.TemporaryDirectory() as directory:
            broken_public = Path(directory) / "public"
            manifest = Path(directory) / "ghost.yaml"
            shutil.copytree(self.public, broken_public)
            shutil.rmtree(broken_public / "operator-support")
            manifest.write_text(manifest_text, encoding="utf-8")

            errors = check_public_tree(broken_public, manifest)

        self.assertIn("missing legacy route: /operator-support/", errors)

    def test_empty_manifest_cannot_bypass_the_route_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "ghost.yaml"
            manifest.write_text("[]\n", encoding="utf-8")

            errors = check_public_tree(self.public, manifest)

        self.assertIn("migration route count: expected 40, got 0", errors)

    def test_malformed_manifest_reports_a_parse_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "ghost.yaml"
            manifest.write_text("- path: [\n", encoding="utf-8")

            errors = check_public_tree(self.public, manifest)

        self.assertTrue(
            any(error.startswith("invalid migration manifest:") for error in errors)
        )

    def test_legacy_redirect_must_point_to_its_declared_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            broken_public = Path(directory) / "public"
            shutil.copytree(self.public, broken_public)
            redirect = broken_public / "operator-support/index.html"
            redirect.write_text(
                redirect.read_text(encoding="utf-8").replace(
                    "https://cybernetks.be/projects/operator/support/",
                    "https://cybernetks.be/projects/operator/privacy/",
                ),
                encoding="utf-8",
            )

            errors = check_public_tree(
                broken_public, ROOT / "data/migration/ghost.yaml"
            )

        self.assertIn(
            "wrong legacy redirect: /operator-support/ -> "
            "https://cybernetks.be/projects/operator/privacy/",
            errors,
        )
        self.assertIn("missing h1: /operator-support/index.html", errors)

    def test_legacy_redirect_cannot_send_visitors_to_another_domain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            broken_public = Path(directory) / "public"
            shutil.copytree(self.public, broken_public)
            redirect = broken_public / "operator-support/index.html"
            redirect.write_text(
                redirect.read_text(encoding="utf-8").replace(
                    "https://cybernetks.be/projects/operator/support/",
                    "https://other.example/projects/operator/support/",
                ),
                encoding="utf-8",
            )

            errors = check_public_tree(
                broken_public, ROOT / "data/migration/ghost.yaml"
            )

        self.assertIn(
            "wrong legacy redirect: /operator-support/ -> "
            "https://other.example/projects/operator/support/",
            errors,
        )

    def test_missing_legacy_redirect_target_names_the_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            broken_public = Path(directory) / "public"
            shutil.copytree(self.public, broken_public)
            shutil.rmtree(broken_public / "projects/operator/support")

            errors = check_public_tree(
                broken_public, ROOT / "data/migration/ghost.yaml"
            )

        self.assertIn(
            "missing redirect target: /operator-support/ -> /projects/operator/support/",
            errors,
        )


class HtmlContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.public = build_site()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.public)

    def assert_error_after_adding(self, markup: str, expected: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            broken_public = Path(directory) / "public"
            shutil.copytree(self.public, broken_public)
            homepage = broken_public / "index.html"
            homepage.write_text(
                homepage.read_text(encoding="utf-8") + markup,
                encoding="utf-8",
            )

            errors = check_public_tree(
                broken_public, ROOT / "data/migration/ghost.yaml"
            )

        self.assertIn(expected, errors)

    def test_missing_internal_href_names_the_source_and_target(self) -> None:
        # A navigation link to a non-generated page must fail before deployment.
        self.assert_error_after_adding(
            '<a href="/not-a-page/">Broken</a>',
            "missing local href: /index.html -> /not-a-page/",
        )

    def test_missing_local_media_source_names_the_source_and_target(self) -> None:
        # A typo in a media file must not become a deployed broken image.
        self.assert_error_after_adding(
            '<img src="/images/not-an-image.png" alt="">',
            "missing local src: /index.html -> /images/not-an-image.png",
        )

    def test_missing_local_open_graph_image_names_the_page_and_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            broken_public = Path(directory) / "public"
            shutil.copytree(self.public, broken_public)
            homepage = broken_public / "index.html"
            homepage.write_text(
                homepage.read_text(encoding="utf-8").replace(
                    "https://cybernetks.be/images/og-default.png",
                    "https://cybernetks.be/images/missing-open-graph.png",
                    1,
                ),
                encoding="utf-8",
            )

            errors = check_public_tree(
                broken_public, ROOT / "data/migration/ghost.yaml"
            )

        self.assertIn(
            "missing local og:image: /index.html -> "
            "https://cybernetks.be/images/missing-open-graph.png",
            errors,
        )

    def test_content_page_requires_its_metadata_and_landmarks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            broken_public = Path(directory) / "public"
            shutil.copytree(self.public, broken_public)
            homepage = broken_public / "index.html"
            html = homepage.read_text(encoding="utf-8")
            html = html.replace('property="og:description" content="Cybernetks"', "", 1)
            html = html.replace('<main id="main">', "<div>", 1)
            html = html.replace("</main>", "</div>", 1)
            html = html.replace("<h1>", "<h2>", 1).replace("</h1>", "</h2>", 1)
            homepage.write_text(html, encoding="utf-8")

            errors = check_public_tree(
                broken_public, ROOT / "data/migration/ghost.yaml"
            )

        self.assertIn("missing og:description: /index.html", errors)
        self.assertIn("missing main landmark: /index.html", errors)
        self.assertIn("missing h1: /index.html", errors)

    def test_normal_page_refresh_cannot_bypass_content_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            broken_public = Path(directory) / "public"
            shutil.copytree(self.public, broken_public)
            homepage = broken_public / "index.html"
            html = homepage.read_text(encoding="utf-8")
            html = html.replace("<h1>", "<h2>", 1).replace("</h1>", "</h2>", 1)
            homepage.write_text(
                html
                + '<meta http-equiv="refresh" '
                'content="0; url=https://cybernetks.be/">',
                encoding="utf-8",
            )

            errors = check_public_tree(
                broken_public, ROOT / "data/migration/ghost.yaml"
            )

        self.assertIn("unexpected redirect: /index.html -> https://cybernetks.be/", errors)
        self.assertIn("missing h1: /index.html", errors)

    def test_canonical_must_use_the_apex_domain_and_match_the_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            broken_public = Path(directory) / "public"
            shutil.copytree(self.public, broken_public)
            homepage = broken_public / "index.html"
            homepage.write_text(
                homepage.read_text(encoding="utf-8").replace(
                    "https://cybernetks.be/", "https://www.cybernetks.be/", 1
                ),
                encoding="utf-8",
            )

            errors = check_public_tree(
                broken_public, ROOT / "data/migration/ghost.yaml"
            )

        self.assertIn(
            "invalid canonical: /index.html -> https://www.cybernetks.be/", errors
        )

    def test_forbidden_portal_and_analytics_markup_are_reported(self) -> None:
        self.assert_error_after_adding(
            '<a href="/portal/">Portal</a><script src="/analytics.js"></script>',
            "forbidden Portal: /index.html",
        )
        self.assert_error_after_adding(
            '<a href="/portal/">Portal</a><script src="/analytics.js"></script>',
            "analytics script: /index.html -> /analytics.js",
        )
