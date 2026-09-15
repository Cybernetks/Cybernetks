from pathlib import Path
import tempfile
import unittest

from tools.publish.config import PublisherConfig
from tools.publish.discovery import discover_sources
from tools.publish.models import ContentKind, SourceValidationError


FIXTURE_VAULT = Path("tests/fixtures/vault")


class DiscoveryTest(unittest.TestCase):
    def test_posts_and_logs_both_map_to_log(self) -> None:
        found = discover_sources(FIXTURE_VAULT)
        kinds = {item.relative_path.as_posix(): item.kind for item in found}

        self.assertEqual(
            kinds["3. Businesses/Cybernetks/Posts/Old Post.md"], ContentKind.LOG
        )
        self.assertEqual(
            kinds["3. Businesses/Cybernetks/Logs/New Log.md"], ContentKind.LOG
        )

    def test_unrelated_daily_note_is_never_discovered(self) -> None:
        found = discover_sources(FIXTURE_VAULT)

        self.assertNotIn(
            "1. Daily/private.md", {item.relative_path.as_posix() for item in found}
        )

    def test_private_project_note_is_never_discovered(self) -> None:
        found = discover_sources(FIXTURE_VAULT)

        self.assertNotIn(
            "3. Businesses/Cybernetks/Projects/Easyfairs/DevOps skills.md",
            {item.relative_path.as_posix() for item in found},
        )

    def test_only_exact_published_status_is_discovered(self) -> None:
        found = discover_sources(FIXTURE_VAULT)

        self.assertNotIn(
            "3. Businesses/Cybernetks/Logs/Published Status Variance.md",
            {item.relative_path.as_posix() for item in found},
        )

    def test_sources_are_sorted_by_relative_posix_path(self) -> None:
        found = discover_sources(FIXTURE_VAULT)

        self.assertEqual(
            [item.relative_path.as_posix() for item in found],
            sorted(item.relative_path.as_posix() for item in found),
        )

    def test_missing_allowlisted_directory_is_rejected(self) -> None:
        config = PublisherConfig(directories=(("Logs", ContentKind.LOG),), files=())

        with tempfile.TemporaryDirectory() as directory, self.assertRaisesRegex(
            SourceValidationError,
            r"Logs: source: required allowlisted directory is missing$",
        ):
            discover_sources(Path(directory), config)

    def test_missing_required_listed_file_is_rejected(self) -> None:
        config = PublisherConfig(directories=(), files=(("About.md", ContentKind.PAGE),))

        with tempfile.TemporaryDirectory() as directory, self.assertRaisesRegex(
            SourceValidationError,
            r"About\.md: source: required allowlisted source is missing$",
        ):
            discover_sources(Path(directory), config)

    def test_missing_optional_listed_file_is_ignored(self) -> None:
        config = PublisherConfig(
            directories=(),
            files=(),
            optional_files=(("Draft.md", ContentKind.PAGE),),
        )

        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(discover_sources(Path(directory), config), [])

    def test_repeated_allowlisted_directory_is_rejected(self) -> None:
        config = PublisherConfig(
            directories=(("Logs", ContentKind.LOG), ("Logs", ContentKind.LOG)),
            files=(),
        )

        with tempfile.TemporaryDirectory() as directory, self.assertRaisesRegex(
            SourceValidationError, r"Logs: source: duplicate allowlisted directory$"
        ):
            discover_sources(Path(directory), config)

    def test_repeated_allowlisted_file_is_rejected(self) -> None:
        config = PublisherConfig(
            directories=(),
            files=(("About.md", ContentKind.PAGE), ("About.md", ContentKind.PAGE)),
        )

        with tempfile.TemporaryDirectory() as directory, self.assertRaisesRegex(
            SourceValidationError, r"About\.md: source: duplicate allowlisted file$"
        ):
            discover_sources(Path(directory), config)

    def test_listed_file_overlapping_directory_result_is_rejected(self) -> None:
        config = PublisherConfig(
            directories=(("Logs", ContentKind.LOG),),
            files=(("Logs/Published.md", ContentKind.PAGE),),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Logs").mkdir()
            (root / "Logs/Published.md").write_text(
                "---\npublication_status: published\n---\nPublic", encoding="utf-8"
            )

            with self.assertRaisesRegex(
                SourceValidationError,
                r"Logs/Published\.md: source: overlaps allowlisted directory Logs$",
            ):
                discover_sources(root, config)

    def test_absent_optional_file_overlapping_directory_is_rejected(self) -> None:
        config = PublisherConfig(
            directories=(("Logs", ContentKind.LOG),),
            files=(),
            optional_files=(("Logs/Draft.md", ContentKind.PAGE),),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Logs").mkdir()

            with self.assertRaisesRegex(
                SourceValidationError,
                r"Logs/Draft\.md: source: overlaps allowlisted directory Logs$",
            ):
                discover_sources(root, config)

    def test_empty_nested_allowlisted_directories_are_rejected(self) -> None:
        config = PublisherConfig(
            directories=(
                ("Sources", ContentKind.LOG),
                ("Sources/Logs", ContentKind.LOG),
            ),
            files=(),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Sources/Logs").mkdir(parents=True)

            with self.assertRaisesRegex(
                SourceValidationError,
                r"Sources/Logs: source: overlaps allowlisted directory Sources$",
            ):
                discover_sources(root, config)


if __name__ == "__main__":
    unittest.main()
