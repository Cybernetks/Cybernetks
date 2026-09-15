from pathlib import Path
import unittest

from tools.publish.body import extract_public_body, extract_snapshot_structure
from tools.publish.models import ContentKind, SourceValidationError


SOURCE_PATH = Path("tests/fixtures/vault/source.md")


class BodyExtractionTest(unittest.TestCase):
    def test_new_log_uses_blog_post_section_only(self) -> None:
        markdown = "# Title\n# Blog post\nPublic body\n# Podcast description\nPrivate package"

        self.assertEqual(
            extract_public_body(markdown, ContentKind.LOG, SOURCE_PATH), "Public body"
        )

    def test_legacy_post_uses_everything_after_published_content(self) -> None:
        markdown = "# Title\n## Summary\nTeaser\n## Published Content\nIntro\n## Next up\nBody"

        self.assertEqual(
            extract_public_body(markdown, ContentKind.LOG, SOURCE_PATH),
            "Intro\n## Next up\nBody",
        )

    def test_snapshot_without_marker_uses_body_after_first_title(self) -> None:
        markdown = "# Monthly Snapshot\nIntro\n## The month in one sentence\nMoved forward."

        self.assertEqual(
            extract_public_body(markdown, ContentKind.SNAPSHOT, SOURCE_PATH),
            "Intro\n## The month in one sentence\nMoved forward.",
        )

    def test_project_uses_explicit_website_content_section(self) -> None:
        markdown = "# Operator\n## Internal roadmap\nPrivate\n## Website Content\nPublic"

        self.assertEqual(
            extract_public_body(markdown, ContentKind.PROJECT, SOURCE_PATH), "Public"
        )

    def test_blog_post_marker_takes_precedence_over_other_markers(self) -> None:
        markdown = (
            "# Title\n"
            "# Blog post\n"
            "Public\n"
            "# Podcast description\n"
            "Private\n"
            "## Published Content\n"
            "Also private"
        )

        self.assertEqual(
            extract_public_body(markdown, ContentKind.LOG, SOURCE_PATH), "Public"
        )

    def test_blog_post_keeps_heading_like_text_inside_a_fenced_code_block(self) -> None:
        markdown = (
            "# Title\n"
            "# Blog post\n"
            "```markdown\n"
            "# Podcast description\n"
            "```\n"
            "Public explanation.\n"
            "# Podcast description\n"
            "Private package"
        )

        self.assertEqual(
            extract_public_body(markdown, ContentKind.LOG, SOURCE_PATH),
            "```markdown\n# Podcast description\n```\nPublic explanation.",
        )

    def test_empty_selected_section_is_rejected_without_falling_back(self) -> None:
        markdown = "# Title\n# Blog post\n# Podcast description\nPrivate"

        with self.assertRaisesRegex(
            SourceValidationError,
            r"^tests/fixtures/vault/source\.md: public body: is empty$",
        ):
            extract_public_body(markdown, ContentKind.LOG, SOURCE_PATH)

    def test_website_content_is_rejected_for_logs_and_snapshots(self) -> None:
        markdown = "# Title\n## Website Content\nPublic"

        for kind in (ContentKind.LOG, ContentKind.SNAPSHOT):
            with self.subTest(kind=kind), self.assertRaisesRegex(
                SourceValidationError,
                r"^tests/fixtures/vault/source\.md: public body: Website Content is only allowed for project and page notes$",
            ):
                extract_public_body(markdown, kind, SOURCE_PATH)

    def test_structured_snapshot_assigns_one_sentence_to_section_zero(self) -> None:
        body = "## The month in one sentence\nMoved forward.\n## What comes next\nShip."

        structure = extract_snapshot_structure(body)

        self.assertIsNotNone(structure)
        assert structure is not None
        self.assertEqual(structure.one_sentence, "Moved forward.")
        self.assertEqual(structure.sections[0].number, "01")
        self.assertEqual(structure.sections[0].title, "What comes next")
        self.assertEqual(structure.sections[0].body, "Ship.")

    def test_freeform_snapshot_has_no_fabricated_structure(self) -> None:
        self.assertIsNone(extract_snapshot_structure("Intro\n\n## A regular section\nBody"))


if __name__ == "__main__":
    unittest.main()
