from dataclasses import replace
from datetime import date
from pathlib import Path
import tempfile
import unittest

import yaml

from tools.publish.models import ContentKind, SourceDocument, SourceValidationError
from tools.publish.render import (
    SectionDocument,
    apply_migration_aliases,
    bundle_path,
    render_bundle,
    serialize_document,
)


NUMBERED_LOG = SourceDocument(
    source_path=Path("3. Businesses/Cybernetks/Logs/005 - Who Stops Scope Creep When You Work Alone?.md"),
    kind=ContentKind.LOG,
    title="#005 - Who Stops Scope Creep When You Work Alone?",
    publication_status="published",
    publish_date=date(2026, 8, 5),
    summary="A Log about keeping a solo project focused.",
    url_path="/005-who-stops-scope-creep-when-you-work-alone/",
    params={"topics": ["indie development"], "projects": ["operator"]},
    body="The public Log body.",
)
SNAPSHOT = SourceDocument(
    source_path=Path("Snapshots/August.md"),
    kind=ContentKind.SNAPSHOT,
    title="August Snapshot",
    publication_status="published",
    publish_date=date(2026, 8, 31),
    summary="A monthly review.",
    url_path="/snapshots/august-2026/",
    params={"review_month": "2026-08"},
    body="A public monthly review.",
)
PROJECT = SourceDocument(
    source_path=Path("Projects/Operator/Operator.md"),
    kind=ContentKind.PROJECT,
    title="Operator",
    publication_status="published",
    publish_date=date(2026, 9, 15),
    summary="A deliberate work companion.",
    url_path="/projects/operator/",
    params={"status": "launching", "promise": "Focus on the next move.", "project_kind": "native_app"},
    body="Project body.",
)


class BundleRenderTest(unittest.TestCase):
    def test_numbered_log_keeps_url_but_drops_display_number(self) -> None:
        # Removing title normalization would expose the legacy display number.
        rendered = serialize_document(NUMBERED_LOG)

        self.assertIn("title: Who Stops Scope Creep When You Work Alone?", rendered)
        self.assertIn("url: /005-who-stops-scope-creep-when-you-work-alone/", rendered)
        self.assertNotIn("#005 -", rendered)

    def test_snapshot_is_written_below_snapshot_section(self) -> None:
        # A route derived from the source filename would place the snapshot incorrectly.
        self.assertEqual(bundle_path(SNAPSHOT).as_posix(), "snapshots/2026-08/index.md")

    def test_bundle_paths_cover_project_owned_pages_and_top_level_pages(self) -> None:
        privacy = replace(
            PROJECT,
            kind=ContentKind.PAGE,
            source_path=Path("Projects/Operator/Privacy.md"),
            title="Operator privacy",
            url_path="/projects/operator/privacy/",
        )
        about = replace(
            PROJECT,
            kind=ContentKind.PAGE,
            source_path=Path("Pages/About Cybernetks.md"),
            title="About Cybernetks",
            url_path="/about/",
        )

        self.assertEqual(bundle_path(PROJECT).as_posix(), "projects/operator/index.md")
        self.assertEqual(bundle_path(privacy).as_posix(), "projects/operator/privacy/index.md")
        self.assertEqual(bundle_path(about).as_posix(), "about/index.md")

    def test_allowlisted_page_identity_rejects_a_mistyped_canonical_route(self) -> None:
        # Deriving a page bundle from the typo would publish it at the wrong public route.
        privacy = replace(
            PROJECT,
            kind=ContentKind.PAGE,
            source_path=Path("3. Businesses/Cybernetks/Projects/Operator/Privacy.md"),
            title="Operator privacy",
            url_path="/operator-privacy/",
        )

        with self.assertRaisesRegex(
            SourceValidationError,
            r"Privacy\.md: url: must be /projects/operator/privacy/$",
        ):
            bundle_path(privacy)

    def test_about_and_uses_have_fixed_routes_from_their_source_identity(self) -> None:
        # A valid bundle must not be chosen from a route supplied in page front matter.
        for filename, expected in (("About Cybernetks.md", "/about/"), ("Uses.md", "/uses/")):
            with self.subTest(filename=filename), self.assertRaisesRegex(
                SourceValidationError, rf"{expected}$"
            ):
                bundle_path(
                    replace(
                        PROJECT,
                        kind=ContentKind.PAGE,
                        source_path=Path(f"3. Businesses/Cybernetks/Pages/{filename}"),
                        url_path="/mistyped/",
                    )
                )

    def test_serialization_has_stable_shared_metadata_and_project_parameters(self) -> None:
        # Omitting an empty shared collection or reordering parameters breaks template data.
        metadata = yaml.safe_load(serialize_document(PROJECT).split("---", 2)[1])

        self.assertEqual(
            list(metadata),
            [
                "title",
                "date",
                "description",
                "url",
                "topics",
                "projects",
                "aliases",
                "params",
            ],
        )
        self.assertEqual(metadata["topics"], [])
        self.assertEqual(metadata["projects"], [])
        self.assertEqual(metadata["params"]["kind"], "project")
        self.assertEqual(metadata["params"]["status"], "launching")

    def test_structured_snapshot_fields_are_preserved_for_its_template(self) -> None:
        # Dropping the extracted structure would force a later template to reparse Markdown.
        structured = replace(
            SNAPSHOT,
            params={
                "review_month": "2026-08",
                "one_sentence": "A deliberate month.",
                "sections": [{"number": "01", "title": "What changed", "body": "Shipped."}],
            },
        )

        metadata = yaml.safe_load(serialize_document(structured).split("---", 2)[1])

        self.assertEqual(metadata["params"]["one_sentence"], "A deliberate month.")
        self.assertEqual(metadata["params"]["sections"][0]["number"], "01")

    def test_migration_aliases_attach_to_matching_document_and_section(self) -> None:
        # Matching aliases to a source filename would miss section-route replacements.
        logs = SectionDocument(title="Logs", url_path="/logs/")
        document = replace(NUMBERED_LOG, params={})

        apply_migration_aliases(
            [document],
            [logs],
            [
                {"path": "/old-log/", "replacement": document.url_path},
                {"path": "/topics/", "replacement": "/logs/"},
                {"path": document.url_path, "replacement": document.url_path},
            ],
        )

        self.assertEqual(document.params["aliases"], ["/old-log/"])
        self.assertEqual(logs.aliases, ["/topics/"])

    def test_migration_rejects_a_missing_replacement_before_rendering(self) -> None:
        # Silently dropping an old route would make a migration look complete when it is not.
        with self.assertRaisesRegex(
            ValueError, r"replacement target is missing: /does-not-exist/"
        ):
            apply_migration_aliases(
                [NUMBERED_LOG],
                [],
                [{"path": "/old-log/", "replacement": "/does-not-exist/"}],
            )

    def test_migration_rejects_a_legacy_path_that_is_another_canonical_route(self) -> None:
        # An alias cannot steal a route still owned by a live publication.
        with self.assertRaisesRegex(ValueError, r"legacy path collides with canonical route"):
            apply_migration_aliases(
                [NUMBERED_LOG, SNAPSHOT],
                [],
                [{"path": SNAPSHOT.url_path, "replacement": NUMBERED_LOG.url_path}],
            )

    def test_render_bundle_writes_the_bundle_index(self) -> None:
        # Writing directly below the destination would stop Hugo treating resources as a bundle.
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            written = render_bundle(NUMBERED_LOG, destination)

            self.assertEqual(written, destination / "logs/005-who-stops-scope-creep-when-you-work-alone/index.md")
            self.assertEqual(written.read_text(encoding="utf-8"), serialize_document(NUMBERED_LOG))


if __name__ == "__main__":
    unittest.main()
