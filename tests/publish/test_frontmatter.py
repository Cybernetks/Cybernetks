from datetime import date
from pathlib import Path
import tempfile
import unittest

from tools.publish.frontmatter import normalize_public_path, parse_source
from tools.publish.models import ContentKind, SourceValidationError


FIXTURE_VAULT = Path("tests/fixtures/vault")
INVALID_FIXTURES = Path("tests/fixtures/invalid-source")


class FrontMatterTest(unittest.TestCase):
    def test_normalizes_existing_www_url_to_path(self) -> None:
        self.assertEqual(
            normalize_public_path("https://www.cybernetks.be/005-scope/"),
            "/005-scope/",
        )

    def test_accepts_canonical_host_and_site_relative_paths(self) -> None:
        self.assertEqual(
            normalize_public_path("https://cybernetks.be/a-log/"),
            "/a-log/",
        )
        self.assertEqual(normalize_public_path("/a-log/"), "/a-log/")

    def test_rejects_an_unrelated_host(self) -> None:
        with self.assertRaises(SourceValidationError):
            normalize_public_path("https://example.com/post/")

    def test_rejects_unsafe_log_adaptation_urls_with_their_source_field(self) -> None:
        # Passing a malformed value through to a template can generate an unsafe external CTA.
        for field in ("youtube_url", "podcast_url", "youtube", "podcast"):
            for value in ("javascript:alert(1)", "https://@www.youtube.com/watch?v=scope-creep"):
                with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "unsafe-adaptation.md"
                    path.write_text(
                        "---\n"
                        "title: Unsafe adaptation\n"
                        "publication_status: published\n"
                        "publish_date: 2026-09-15\n"
                        "summary: This Log has an unsafe external destination.\n"
                        "url: /unsafe-adaptation/\n"
                        f"{field}: {value}\n"
                        "---\n"
                        "A public Log body.\n",
                        encoding="utf-8",
                    )

                    with self.assertRaisesRegex(
                        SourceValidationError,
                        rf"^{path.as_posix()}: {field}: must be an absolute HTTPS URL$",
                    ):
                        parse_source(path, ContentKind.LOG)

    def test_rejects_unsafe_project_action_destinations_with_their_source_field(self) -> None:
        # Unvalidated lifecycle fields would become misleading or unsafe primary CTAs.
        external_fields = ("beta_url", "store_url", "app_url", "source_url", "project_url")
        for field in external_fields:
            for value in (
                "javascript:alert(1)",
                "https://example.com/placeholder",
                "https://localhost./",
                "https://example.com./",
            ):
                with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "unsafe-project-action.md"
                    path.write_text(
                        "---\n"
                        "title: Unsafe project action\n"
                        "publication_status: published\n"
                        "publish_date: 2026-09-15\n"
                        "summary: This project has an unsafe action destination.\n"
                        "url: /unsafe-project-action/\n"
                        "status: beta\n"
                        "promise: A safe project action.\n"
                        "project_kind: native_app\n"
                        f"{field}: {value}\n"
                        "---\n",
                        encoding="utf-8",
                    )

                    with self.assertRaisesRegex(
                        SourceValidationError,
                        rf"^{path.as_posix()}: {field}: must be an absolute HTTPS URL to a non-placeholder host$",
                    ):
                        parse_source(path, ContentKind.PROJECT)

    def test_rejects_unsafe_project_latest_update_with_its_source_field(self) -> None:
        # A project update must remain an internal canonical route, not an executable or absolute URL.
        for value in ("javascript:alert(1)", "https://cybernetks.be/a-log/"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "unsafe-project-update.md"
                path.write_text(
                    "---\n"
                    "title: Unsafe project update\n"
                    "publication_status: published\n"
                    "publish_date: 2026-09-15\n"
                    "summary: This project has an unsafe update route.\n"
                    "url: /unsafe-project-update/\n"
                    "status: launching\n"
                    "promise: A safe project update.\n"
                    "project_kind: native_app\n"
                    f"latest_update: {value}\n"
                    "---\n",
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(
                    SourceValidationError,
                    rf"^{path.as_posix()}: latest_update: must be a site-relative Cybernetks URL$",
                ):
                    parse_source(path, ContentKind.PROJECT)

    def test_rejects_query_fragment_and_malformed_paths(self) -> None:
        for value in (
            "https://cybernetks.be/post/?source=feed",
            "https://cybernetks.be/post/#section",
            "post/",
            "/post",
        ):
            with self.subTest(value=value):
                with self.assertRaises(SourceValidationError):
                    normalize_public_path(value)

    def test_parses_a_published_log_with_normalized_url_and_body(self) -> None:
        document = parse_source(
            FIXTURE_VAULT / "3. Businesses/Cybernetks/Logs/Published Log.md",
            ContentKind.LOG,
        )

        self.assertEqual(document.title, "Published Log")
        self.assertEqual(document.publication_status, "published")
        self.assertEqual(document.publish_date, date(2026, 9, 15))
        self.assertEqual(document.url_path, "/published-log/")
        self.assertEqual(document.params["topics"], ["publishing"])
        self.assertEqual(document.body, "# Published Log\nA public Log body.\n")

    def test_project_has_separate_publication_and_lifecycle_status(self) -> None:
        document = parse_source(FIXTURE_VAULT / "project.md", ContentKind.PROJECT)

        self.assertEqual(document.publication_status, "published")
        self.assertEqual(document.params["status"], "launching")

    def test_requires_snapshot_review_month(self) -> None:
        path = INVALID_FIXTURES / "Missing Review Month.md"

        with self.assertRaisesRegex(
            SourceValidationError,
            r"^tests/fixtures/invalid-source/Missing Review Month\.md: review_month: is required$",
        ):
            parse_source(path, ContentKind.SNAPSHOT)

    def test_reports_missing_published_field_with_source_and_field(self) -> None:
        path = INVALID_FIXTURES / "Missing Summary.md"

        with self.assertRaisesRegex(
            SourceValidationError,
            r"^tests/fixtures/invalid-source/Missing Summary\.md: summary: is required$",
        ):
            parse_source(path, ContentKind.LOG)

    def test_reports_invalid_published_url_with_source_and_field(self) -> None:
        path = INVALID_FIXTURES / "Invalid URL.md"

        with self.assertRaisesRegex(
            SourceValidationError,
            r"^tests/fixtures/invalid-source/Invalid URL\.md: url: must not include a query string$",
        ):
            parse_source(path, ContentKind.LOG)

    def test_allows_a_draft_to_omit_public_only_fields(self) -> None:
        document = parse_source(
            FIXTURE_VAULT / "3. Businesses/Cybernetks/Logs/Draft Log.md",
            ContentKind.LOG,
        )

        self.assertEqual(document.publication_status, "draft")
        self.assertEqual(document.title, "")
        self.assertEqual(document.url_path, "")

    def test_rejects_duplicate_yaml_keys(self) -> None:
        path = INVALID_FIXTURES / "Duplicate Key.md"

        with self.assertRaisesRegex(
            SourceValidationError,
            r"^tests/fixtures/invalid-source/Duplicate Key\.md: publication_status: must not be duplicated$",
        ):
            parse_source(path, ContentKind.LOG)

    def test_rejects_an_unknown_content_kind(self) -> None:
        path = FIXTURE_VAULT / "3. Businesses/Cybernetks/Logs/Published Log.md"

        with self.assertRaisesRegex(
            SourceValidationError,
            r"^tests/fixtures/vault/3\. Businesses/Cybernetks/Logs/Published Log\.md: kind: must be one of log, snapshot, project, page$",
        ):
            parse_source(path, "unknown")  # type: ignore[arg-type]

    def test_rejects_project_only_fields_on_a_log(self) -> None:
        for field in ("status", "promise", "project_kind"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "project-field-on-log.md"
                path.write_text(
                    "---\n"
                    "title: Log with project metadata\n"
                    "publication_status: published\n"
                    "publish_date: 2026-09-15\n"
                    "summary: This field belongs only to a Project.\n"
                    "url: /project-field-on-log/\n"
                    f"{field}: example\n"
                    "---\n",
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(
                    SourceValidationError,
                    rf"^{path.as_posix()}: {field}: is only allowed for projects$",
                ):
                    parse_source(path, ContentKind.LOG)


if __name__ == "__main__":
    unittest.main()
