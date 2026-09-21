from dataclasses import replace
from datetime import date
from pathlib import Path
import tempfile
import unittest

from tools.publish.assets import collect_assets, rewrite_embeds
from tools.publish.models import ContentKind, SourceDocument, SourceValidationError


FIXTURE_VAULT = Path("tests/fixtures/vault")
LOG_WITH_IMAGE = SourceDocument(
    source_path=Path("3. Businesses/Cybernetks/Logs/Published Log.md"),
    kind=ContentKind.LOG,
    title="Published Log",
    publication_status="published",
    publish_date=date(2026, 9, 15),
    summary="A public publishing update.",
    url_path="/published-log/",
    body="![[operator screen.png|Operator screen]]",
)
LOG_WITH_MISSING_IMAGE = replace(LOG_WITH_IMAGE, body="![[missing-image.png]]")


class PageAssetCollectionTest(unittest.TestCase):
    def test_project_icon_is_copied_into_its_page_bundle(self) -> None:
        # Ignoring an icon declared in front matter leaves project cards with a broken resource.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "Projects/Operator"
            project.mkdir(parents=True)
            (project / "operator-logo.svg").write_text("<svg/>", encoding="utf-8")
            document = SourceDocument(
                source_path=project / "Operator.md",
                kind=ContentKind.PROJECT,
                title="Operator",
                publication_status="published",
                publish_date=date(2026, 7, 1),
                summary="A calm place to focus.",
                url_path="/projects/operator/",
                params={"icon": "operator-logo.svg"},
                body="Operator.",
            )

            copies = collect_assets(document, root)

        self.assertEqual([copy.bundle_name for copy in copies], ["operator-logo.svg"])

    def test_embed_is_copied_into_owning_page_bundle(self) -> None:
        copies = collect_assets(LOG_WITH_IMAGE, FIXTURE_VAULT)

        self.assertEqual(copies[0].bundle_name, "operator-screen.png")

    def test_image_embed_is_rewritten_to_the_page_resource(self) -> None:
        self.assertEqual(
            rewrite_embeds(LOG_WITH_IMAGE, FIXTURE_VAULT),
            "![Operator screen](operator-screen.png)",
        )

    def test_missing_embed_is_an_error(self) -> None:
        with self.assertRaisesRegex(SourceValidationError, r"^.*: missing asset: missing-image\.png$"):
            collect_assets(LOG_WITH_MISSING_IMAGE, FIXTURE_VAULT)

    def test_unsupported_embed_type_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "private.pdf").write_text("private", encoding="utf-8")

            with self.assertRaisesRegex(
                SourceValidationError, r"unsupported asset type: \.pdf$"
            ):
                collect_assets(replace(LOG_WITH_IMAGE, body="![[private.pdf]]"), root)

    def test_duplicate_sanitized_names_receive_source_digest_suffixes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one").mkdir()
            (root / "two").mkdir()
            (root / "one/operator screen.png").write_bytes(b"first image")
            (root / "two/operator-screen.png").write_bytes(b"second image")
            document = replace(
                LOG_WITH_IMAGE,
                body="![[one/operator screen.png]]\n![[two/operator-screen.png]]",
            )

            copies = collect_assets(document, root)

        self.assertEqual(
            [copy.bundle_name for copy in copies],
            ["operator-screen-fb4516b5.png", "operator-screen-cd2c3f6b.png"],
        )

    def test_path_traversal_embed_is_rejected(self) -> None:
        with self.assertRaisesRegex(SourceValidationError, r"asset path traversal"):
            collect_assets(replace(LOG_WITH_IMAGE, body="![[../private.png]]"), FIXTURE_VAULT)

    def test_ambiguous_asset_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one").mkdir()
            (root / "two").mkdir()
            (root / "one/screenshot.png").write_bytes(b"one")
            (root / "two/screenshot.png").write_bytes(b"two")

            with self.assertRaisesRegex(SourceValidationError, r"ambiguous asset: screenshot\.png$"):
                collect_assets(replace(LOG_WITH_IMAGE, body="![[screenshot.png]]"), root)


if __name__ == "__main__":
    unittest.main()
