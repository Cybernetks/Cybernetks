from dataclasses import replace
from datetime import date
from pathlib import Path
import unittest

from tools.publish.links import build_public_index, heading_anchor, rewrite_links
from tools.publish.models import ContentKind, SourceDocument, SourceValidationError


LOG_DOCUMENT = SourceDocument(
    source_path=Path("Log.md"),
    kind=ContentKind.LOG,
    title="Log",
    publication_status="published",
    publish_date=date(2026, 9, 15),
    summary="A public log.",
    url_path="/logs/log/",
)
OPERATOR_DOCUMENT = SourceDocument(
    source_path=Path("Projects/Operator/Operator.md"),
    kind=ContentKind.PROJECT,
    title="Operator",
    publication_status="published",
    publish_date=date(2026, 9, 15),
    summary="A public project.",
    url_path="/projects/operator/",
)
PUBLIC_INDEX = build_public_index([OPERATOR_DOCUMENT])


class WikiLinkRewriteTest(unittest.TestCase):
    def test_public_wiki_link_becomes_canonical_path(self) -> None:
        body = "Read [[Operator]] and [[Operator|the product]]."

        rewritten = rewrite_links(replace(LOG_DOCUMENT, body=body), PUBLIC_INDEX)

        self.assertEqual(
            rewritten,
            "Read [Operator](/projects/operator/) and [the product](/projects/operator/).",
        )

    def test_public_relative_path_link_resolves_to_canonical_path(self) -> None:
        body = "Read [[Projects/Operator/Operator|the product]]."

        rewritten = rewrite_links(replace(LOG_DOCUMENT, body=body), PUBLIC_INDEX)

        self.assertEqual(rewritten, "Read [the product](/projects/operator/).")

    def test_absolute_source_paths_are_indexed_relative_to_the_vault(self) -> None:
        vault = Path("/private/tmp/vault")
        operator = replace(
            OPERATOR_DOCUMENT,
            source_path=vault / "Projects/Operator/Operator.md",
        )

        rewritten = rewrite_links(
            replace(LOG_DOCUMENT, body="[[Projects/Operator/Operator]]"),
            build_public_index([operator], vault),
        )

        self.assertEqual(rewritten, "[Operator](/projects/operator/)")

    def test_public_heading_link_uses_normalized_anchor(self) -> None:
        body = "Read [[Operator#What's New?!|the update]]."

        rewritten = rewrite_links(replace(LOG_DOCUMENT, body=body), PUBLIC_INDEX)

        self.assertEqual(rewritten, "Read [the update](/projects/operator/#what-s-new).")

    def test_private_wiki_link_fails_with_source_location(self) -> None:
        with self.assertRaisesRegex(
            SourceValidationError,
            r"^Log\.md: unresolved public link: Pricing Strategy - Operator$",
        ):
            rewrite_links(
                replace(LOG_DOCUMENT, body="[[Pricing Strategy - Operator]]"),
                PUBLIC_INDEX,
            )

    def test_ambiguous_basename_fails_instead_of_guessing(self) -> None:
        first = replace(OPERATOR_DOCUMENT, source_path=Path("One/Status.md"), url_path="/one/")
        second = replace(OPERATOR_DOCUMENT, source_path=Path("Two/Status.md"), url_path="/two/")

        with self.assertRaisesRegex(
            SourceValidationError,
            r"^Log\.md: ambiguous public link: Status$",
        ):
            rewrite_links(
                replace(LOG_DOCUMENT, body="[[Status]]"),
                build_public_index([first, second]),
            )

    def test_same_url_notes_with_an_ambiguous_basename_still_fail(self) -> None:
        first = replace(OPERATOR_DOCUMENT, source_path=Path("One/Status.md"), url_path="/shared/")
        second = replace(OPERATOR_DOCUMENT, source_path=Path("Two/Status.md"), url_path="/shared/")

        with self.assertRaisesRegex(
            SourceValidationError,
            r"^Log\.md: ambiguous public link: Status$",
        ):
            rewrite_links(
                replace(LOG_DOCUMENT, body="[[Status]]"),
                build_public_index([first, second]),
            )

    def test_shorter_backtick_run_does_not_close_a_longer_fence(self) -> None:
        body = "````\n[[Pricing Strategy - Operator]]\n```\n[[Operator]]\n````\n[[Operator]]"

        rewritten = rewrite_links(replace(LOG_DOCUMENT, body=body), PUBLIC_INDEX)

        self.assertEqual(
            rewritten,
            "````\n[[Pricing Strategy - Operator]]\n```\n[[Operator]]\n````\n[Operator](/projects/operator/)",
        )

    def test_mixed_delimiter_fence_does_not_close_the_open_fence(self) -> None:
        body = "~~~\n[[Pricing Strategy - Operator]]\n```\n[[Operator]]\n~~~\n[[Operator]]"

        rewritten = rewrite_links(replace(LOG_DOCUMENT, body=body), PUBLIC_INDEX)

        self.assertEqual(
            rewritten,
            "~~~\n[[Pricing Strategy - Operator]]\n```\n[[Operator]]\n~~~\n[Operator](/projects/operator/)",
        )

    def test_ordinary_markdown_link_is_preserved(self) -> None:
        body = "[Operator](https://example.com/operator) and [docs](/docs/)."

        self.assertEqual(rewrite_links(replace(LOG_DOCUMENT, body=body), PUBLIC_INDEX), body)

    def test_heading_anchor_normalizes_case_and_punctuation(self) -> None:
        self.assertEqual(heading_anchor("What's New?!"), "what-s-new")


if __name__ == "__main__":
    unittest.main()
