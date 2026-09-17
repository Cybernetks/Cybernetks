from pathlib import Path
import shutil
import tempfile
import unittest

import yaml

from tools.publish.transaction import PublishFailed, publish


FIXTURE_VAULT = Path("tests/fixtures/vault")


def valid_vault(destination: Path) -> Path:
    shutil.copytree(FIXTURE_VAULT, destination)
    return destination


class PublishTransactionTest(unittest.TestCase):
    def test_editorial_metadata_never_reaches_generated_public_files(self) -> None:
        # Passing arbitrary source properties into params publishes private vault metadata.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            repository.mkdir()
            vault = valid_vault(root / "vault")
            note = vault / "3. Businesses/Cybernetks/Logs/New Log.md"
            note.write_text(
                note.read_text(encoding="utf-8").replace(
                    "publication_status: published",
                    "publication_status: published\n"
                    "editorial_notes: PRIVATE-EDITORIAL-SENTINEL\n"
                    "type: ['[[PRIVATE-VAULT-RELATION]]']\n"
                    "params: {secret: PRIVATE-NESTED-SENTINEL}\n"
                    "youtube_url: https://www.youtube.com/watch?v=public-video",
                ),
                encoding="utf-8",
            )

            publish(vault, repository)

            rendered = repository / "generated/content/logs/new-log/index.md"
            text = rendered.read_text(encoding="utf-8")
            self.assertNotIn("PRIVATE-", text)
            metadata = yaml.safe_load(text.split("---", 2)[1])
            self.assertEqual(
                metadata["params"]["youtube_url"],
                "https://www.youtube.com/watch?v=public-video",
            )

    def test_shared_fixture_publishes_without_test_only_edits(self) -> None:
        # The wrapper's fixture must be a complete valid vault, not a test-repaired copy.
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repository"
            repository.mkdir()

            report = publish(FIXTURE_VAULT, repository)

            self.assertEqual(report.assets, 1)
            self.assertTrue(
                (repository / "generated/content/logs/new-log/operator-screen.png").is_file()
            )

    def test_failed_validation_keeps_previous_generated_tree(self) -> None:
        # Moving the old tree before parsing all notes would destroy this valid content.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            repository.mkdir()
            vault = valid_vault(root / "vault")
            existing = repository / "generated/content/logs/old/index.md"
            existing.parent.mkdir(parents=True)
            existing.write_text("old valid content", encoding="utf-8")
            broken = vault / "3. Businesses/Cybernetks/Logs/New Log.md"
            broken.write_text(
                "---\n"
                "title: Broken Log\n"
                "publication_status: published\n"
                "publish_date: 2026-09-15\n"
                "url: /broken-log/\n"
                "---\n"
                "Broken\n",
                encoding="utf-8",
            )

            with self.assertRaises(PublishFailed):
                publish(vault, repository)

            self.assertEqual(existing.read_text(encoding="utf-8"), "old valid content")
            self.assertFalse((repository / ".publish-stage").exists())
            self.assertFalse((repository / ".publish-backup").exists())

    def test_success_replaces_the_entire_previous_generated_tree(self) -> None:
        # Leaving stale files behind would make deletion from the vault ineffective.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            repository.mkdir()
            vault = valid_vault(root / "vault")
            stale = repository / "generated/content/logs/stale/index.md"
            stale.parent.mkdir(parents=True)
            stale.write_text("stale", encoding="utf-8")

            report = publish(vault, repository)

            self.assertFalse(stale.exists())
            self.assertEqual(report.counts["log"], 3)
            self.assertEqual(report.counts["snapshot"], 1)
            self.assertEqual(report.assets, 1)
            self.assertTrue((repository / "generated/content/logs/new-log/index.md").is_file())
            self.assertTrue(
                (repository / "generated/content/logs/new-log/operator-screen.png").is_file()
            )
            self.assertFalse((repository / ".publish-stage").exists())
            self.assertFalse((repository / ".publish-backup").exists())

    def test_vault_cannot_be_the_repository(self) -> None:
        # Treating one directory as both inputs would make a failed export destructive.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            with self.assertRaisesRegex(PublishFailed, "vault and repository"):
                publish(root, root)

    def test_nonidentity_migration_route_is_rendered_as_a_hugo_alias(self) -> None:
        # Applying migrations after rendering would leave the generated front matter stale.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            repository.mkdir()
            vault = valid_vault(root / "vault")
            manifest = repository / "data/migration/ghost.yaml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                yaml.safe_dump(
                    [{"path": "/old-new-log/", "replacement": "/new-log/"}],
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            publish(vault, repository)

            rendered = repository / "generated/content/logs/new-log/index.md"
            metadata = yaml.safe_load(rendered.read_text(encoding="utf-8").split("---", 2)[1])
            self.assertEqual(metadata["aliases"], ["/old-new-log/"])
            self.assertEqual(metadata["params"]["kind"], "log")

    def test_structured_snapshot_body_becomes_template_data(self) -> None:
        # Ignoring Task 3's parsed structure would leave Snapshot templates with Markdown only.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            repository.mkdir()
            vault = valid_vault(root / "vault")
            snapshot = vault / "3. Businesses/Cybernetks/Monthly Snapshots/Published Snapshot.md"
            snapshot.write_text(
                snapshot.read_text(encoding="utf-8").replace(
                    "The month in one sentence.",
                    "## The month in one sentence\nA deliberate month.\n\n## What changed\nShipped.",
                ),
                encoding="utf-8",
            )

            publish(vault, repository)

            rendered = repository / "generated/content/snapshots/2026-09/index.md"
            metadata = yaml.safe_load(rendered.read_text(encoding="utf-8").split("---", 2)[1])
            self.assertEqual(metadata["params"]["one_sentence"], "A deliberate month.")
            self.assertEqual(metadata["params"]["sections"][0]["title"], "What changed")

    def test_duplicate_migration_keys_fail_before_staging(self) -> None:
        # A normal YAML loader silently keeps the last route and loses migration data.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            repository.mkdir()
            vault = valid_vault(root / "vault")
            existing = repository / "generated/content/logs/old/index.md"
            existing.parent.mkdir(parents=True)
            existing.write_text("old valid content", encoding="utf-8")
            manifest = repository / "data/migration/ghost.yaml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                "- path: /first-old-log/\n"
                "  path: /second-old-log/\n"
                "  replacement: /new-log/\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(PublishFailed, r"migration: path: must not be duplicated"):
                publish(vault, repository)

            self.assertEqual(existing.read_text(encoding="utf-8"), "old valid content")
            self.assertFalse((repository / ".publish-stage").exists())


if __name__ == "__main__":
    unittest.main()
