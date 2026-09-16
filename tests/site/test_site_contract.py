from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tests.site.build import ROOT, build_site, built_html
from tools.publish.transaction import publish


class HugoSmokeTest(unittest.TestCase):
    def test_homepage_builds_with_canonical_origin(self) -> None:
        public = build_site()
        html = (public / "index.html").read_text(encoding="utf-8")
        self.assertIn('<link rel="canonical" href="https://cybernetks.be/">', html)

    def test_shell_contains_official_identity_and_primary_navigation(self) -> None:
        public = build_site()
        html = (public / "index.html").read_text(encoding="utf-8")
        self.assertIn('/brand/logo.svg', html)
        self.assertIn('/brand/wordmark-gold.svg', html)
        for label in ("Projects", "Logs", "Monthly Snapshots", "About"):
            self.assertIn(label, html)

    def test_page_has_canonical_and_open_graph_metadata(self) -> None:
        public = build_site()
        html = (public / "projects/operator/index.html").read_text(encoding="utf-8")
        self.assertIn('property="og:title"', html)
        self.assertIn('property="og:image"', html)
        self.assertIn('rel="canonical"', html)

    def test_page_resource_image_has_responsive_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            content = Path(directory)
            (content / "_index.md").write_text("---\ntitle: Cybernetks\n---\n", encoding="utf-8")
            bundle = content / "article"
            bundle.mkdir()
            (bundle / "index.md").write_text(
                "---\ntitle: Article\n---\n\n![Preview](preview.png)",
                encoding="utf-8",
            )
            (bundle / "preview.png").write_bytes(
                (ROOT / "static/images/og-default.png").read_bytes()
            )
            html = (build_site(content) / "article/index.html").read_text(encoding="utf-8")

        self.assertIn('srcset="', html)
        self.assertIn('480w', html)
        self.assertIn('960w', html)
        self.assertIn('1200w', html)
        self.assertIn('sizes="(max-width: 760px) 100vw, 68ch"', html)
        self.assertIn('loading="lazy"', html)
        self.assertIn('width="1200" height="630"', html)

    def test_open_graph_dimensions_are_limited_to_the_default_image(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            content = Path(directory)
            (content / "_index.md").write_text("---\ntitle: Cybernetks\n---\n", encoding="utf-8")
            bundle = content / "custom-image"
            bundle.mkdir()
            (bundle / "index.md").write_text(
                "---\ntitle: Custom image\nimage: https://example.com/custom.png\n---\n",
                encoding="utf-8",
            )
            public = build_site(content)
            fallback = (public / "index.html").read_text(encoding="utf-8")
            custom = (public / "custom-image/index.html").read_text(encoding="utf-8")

        self.assertIn('property="og:image:width" content="1200"', fallback)
        self.assertIn('property="og:image:height" content="630"', fallback)
        self.assertNotIn('property="og:image:width"', custom)
        self.assertNotIn('property="og:image:height"', custom)

class HugoPreflightTest(unittest.TestCase):
    def assert_build_rejected(self, version: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake_hugo = Path(directory) / "hugo"
            fake_hugo.write_text(
                f'#!/bin/sh\necho "{version}"\n', encoding="utf-8"
            )
            fake_hugo.chmod(0o755)
            with patch.dict(
                os.environ, {"PATH": f"{directory}:{os.environ['PATH']}"}
            ):
                with self.assertRaises(subprocess.CalledProcessError):
                    build_site()

    def test_rejects_non_extended_hugo(self) -> None:
        self.assert_build_rejected("hugo v0.164.0-ce2470 darwin/arm64")

    def test_rejects_wrong_hugo_version(self) -> None:
        self.assert_build_rejected("hugo v0.165.0-ce2470+extended darwin/arm64")


class PublicationTemplateTest(unittest.TestCase):
    def test_log_is_reading_first_and_unnumbered(self) -> None:
        # Replacing the Log view with the generic single template would lose its distinct contract.
        html = built_html("005-who-stops-scope-creep-when-you-work-alone/index.html")

        self.assertIn('data-template="log"', html)
        self.assertIn("Who Stops Scope Creep When You Work Alone?", html)
        self.assertNotIn("#005", html)

    def test_snapshot_has_aligned_numbered_sections(self) -> None:
        # Rendering the Markdown body directly would discard the parsed Snapshot structure.
        html = built_html("monthly-snapshot-august-2026/index.html")

        self.assertIn('data-template="snapshot"', html)
        self.assertIn('data-snapshot-section="00"', html)
        self.assertIn('data-snapshot-section="01"', html)
        self.assertIn('class="snapshot-grid"', html)

    def test_snapshot_sections_render_without_an_in_one_sentence_statement(self) -> None:
        # Using one_sentence as the only structure switch would drop valid parsed sections.
        html = built_html("monthly-snapshot-july-2026/index.html")

        self.assertNotIn('data-snapshot-section="00"', html)
        self.assertIn('data-snapshot-section="01"', html)
        self.assertIn("A completed section without a statement.", html)
        self.assertNotIn("This freeform body must not replace parsed sections.", html)

    def test_snapshot_archive_cards_keep_their_page_context(self) -> None:
        # Passing the archive page to a card would link back to the archive instead of the Snapshot.
        html = built_html("snapshots/index.html")

        self.assertIn('href="/monthly-snapshot-august-2026/"', html)
        self.assertIn("Review month: 2026-08", html)

    def test_freeform_snapshot_keeps_its_authored_body_without_invented_sections(self) -> None:
        # Labeling an older freeform Snapshot as section 00 would fabricate structure the source lacks.
        html = (build_site() / "snapshots/september-2026/index.html").read_text(encoding="utf-8")

        self.assertIn('class="snapshot-grid snapshot-grid--freeform"', html)
        self.assertIn("The month in one sentence.", html)
        self.assertNotIn("data-snapshot-section", html)

    def test_log_renders_only_the_supplied_adaptation_cta(self) -> None:
        # Unconditional adaptation links would imply a counterpart that the source does not provide.
        html = built_html("005-who-stops-scope-creep-when-you-work-alone/index.html")

        self.assertIn('href="https://www.youtube.com/watch?v=scope-creep"', html)
        self.assertIn("Watch on YouTube", html)
        self.assertNotIn("Listen to the podcast", html)

    def test_log_without_adaptations_renders_no_adaptation_cta(self) -> None:
        # Rendering a fallback CTA would imply an adaptation with no supplied destination.
        html = built_html("log-without-adaptations/index.html")

        self.assertNotIn("Watch on YouTube", html)
        self.assertNotIn("Listen to the podcast", html)


class ProjectTemplateTest(unittest.TestCase):
    def test_launching_project_links_to_latest_update(self) -> None:
        # Removing the lifecycle action would leave a work-in-progress project with no real next step.
        html = built_html("projects/operator/index.html")

        self.assertIn('href="/005-who-stops-scope-creep-when-you-work-alone/"', html)
        self.assertIn("Read the latest update", html)

    def test_released_native_project_uses_store_action(self) -> None:
        # Treating native releases as generic project links would hide the genuine store destination.
        html = built_html("projects/released-app/index.html")

        self.assertIn("Download on the App Store", html)
        self.assertIn('href="https://apps.apple.com/app/example"', html)

    def test_archived_project_has_no_primary_action(self) -> None:
        # A forced action on an archived experiment would make a promise the project no longer makes.
        html = built_html("projects/archived-experiment/index.html")

        self.assertIn('data-template="project"', html)
        self.assertNotIn('class="project-primary-action"', html)

    def test_launching_project_without_a_published_update_has_no_primary_action(self) -> None:
        # A stale update path must not advertise a publication that does not exist.
        html = built_html("projects/unlinked-launch/index.html")

        self.assertNotIn('class="project-primary-action"', html)

    def test_launching_project_cannot_use_an_unrelated_page_as_its_update(self) -> None:
        # An existing About page is not a project-related Log or Snapshot update.
        html = built_html("projects/unrelated-update/index.html")

        self.assertNotIn('class="project-primary-action"', html)


class HomepageTest(unittest.TestCase):
    def test_homepage_places_projects_before_latest_publications(self) -> None:
        # Moving publications above projects would reverse the approved product-studio hierarchy.
        html = built_html("index.html")

        self.assertLess(html.index("Projects and experiments"), html.index("Latest from the studio"))
        for project in ("Operator", "Cybernetks Planner", "Alien Miner"):
            self.assertIn(project, html)

    def test_homepage_cards_include_branch_projects_in_the_approved_order(self) -> None:
        # Querying only RegularPages would drop branch-bundle projects from this section.
        html = built_html("index.html")
        projects = html[html.index("Projects and experiments") : html.index("Latest from the studio")]

        self.assertLess(projects.index("Operator"), projects.index("Cybernetks Planner"))
        self.assertLess(projects.index("Cybernetks Planner"), projects.index("Alien Miner"))

    def test_projects_index_includes_all_branch_bundle_projects(self) -> None:
        # A project index must not lose profiles merely because they own nested support pages.
        html = built_html("projects/index.html")

        self.assertIn('data-template="projects-index"', html)
        for project in ("Operator", "Cybernetks Planner", "Alien Miner"):
            self.assertIn(project, html)


class GenericPageTest(unittest.TestCase):
    def test_project_owned_page_links_back_to_its_project(self) -> None:
        # Dropping the owning-project link would strand privacy and support information.
        html = built_html("projects/operator/privacy/index.html")

        self.assertIn('href="/projects/operator/"', html)
        self.assertIn("Back to Operator", html)

    def test_project_page_links_to_its_supporting_pages(self) -> None:
        # Omitting secondary links would make published privacy and support pages undiscoverable.
        html = built_html("projects/operator/index.html")

        self.assertIn('href="/projects/operator/privacy/"', html)
        self.assertIn('href="/projects/operator/support/"', html)

    def test_published_project_branch_keeps_nested_privacy_and_support_routes(self) -> None:
        # Rendering a project as a leaf bundle silently drops its nested legal and support pages.
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repository"
            repository.mkdir()
            publish(ROOT / "tests/fixtures/vault", repository)
            public = build_site(repository / "generated/content")

            self.assertTrue((public / "projects/operator/index.html").is_file())
            self.assertTrue((public / "projects/operator/privacy/index.html").is_file())
            self.assertTrue((public / "projects/operator/support/index.html").is_file())
            self.assertTrue((public / "new-log/index.html").is_file())
            home = (public / "index.html").read_text(encoding="utf-8")
            projects = home[home.index("Projects and experiments") : home.index("Latest from the studio")]
            self.assertLess(projects.index("Operator"), projects.index("Cybernetks Planner"))
            self.assertLess(projects.index("Cybernetks Planner"), projects.index("Alien Miner"))
