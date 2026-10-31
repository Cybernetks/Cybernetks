import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class PublishWrapperTest(unittest.TestCase):
    def test_check_wrapper_uses_project_venv_instead_of_host_python(self) -> None:
        # A host Python older than 3.11 cannot import or execute this project's test suite.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = self._repository_copy(root)
            python = repository / ".venv/bin/python"
            python.parent.mkdir(parents=True)
            python.write_text(
                "#!/bin/sh\necho 'project Python ran the tests'\nexit 0\n",
                encoding="utf-8",
            )
            python.chmod(0o755)
            commands = self._command_shims(root)

            result = subprocess.run(
                ["./scripts/check-site"],
                cwd=repository,
                env={**os.environ, "PATH": f"{commands}:{os.defpath}"},
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("project Python ran the tests", result.stdout)
            self.assertNotIn("default python ran", result.stderr)

    def test_publish_validates_reviewed_content_without_a_vault(self) -> None:
        # Publishing must work without the retired Obsidian path or access to Bear.
        with tempfile.TemporaryDirectory() as directory:
            repository = self._repository_copy(Path(directory))
            self._add_public_content(repository)
            self._replace_check_site(repository, "echo 'site checks passed'\nexit 0")

            result = subprocess.run(
                ["./scripts/publish-site"],
                cwd=repository,
                env={key: value for key, value in os.environ.items() if key != "CYBERNETKS_VAULT"},
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("site checks passed", result.stdout)
            self.assertIn("Publication candidate validated and built", result.stdout)

    def test_publish_refuses_a_missing_public_content_tree(self) -> None:
        # A successful no-op would make a missing or misplaced publication look releasable.
        with tempfile.TemporaryDirectory() as directory:
            repository = self._repository_copy(Path(directory))
            self._replace_check_site(repository, "echo 'must not run'\nexit 0")

            result = subprocess.run(
                ["./scripts/publish-site"],
                cwd=repository,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("reviewed public content is missing", result.stderr)
            self.assertNotIn("must not run", result.stdout)

    def test_publish_propagates_validation_failure(self) -> None:
        # A failed site check must never be presented as a releasable publication.
        with tempfile.TemporaryDirectory() as directory:
            repository = self._repository_copy(Path(directory))
            self._add_public_content(repository)
            self._replace_check_site(repository, "echo 'invalid site' >&2\nexit 73")

            result = subprocess.run(
                ["./scripts/publish-site"],
                cwd=repository,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 73)
            self.assertIn("invalid site", result.stderr)
            self.assertNotIn("Publication candidate validated", result.stdout)

    def _repository_copy(self, destination: Path) -> Path:
        repository = destination / "repository"
        repository.mkdir()
        shutil.copytree(ROOT / "scripts", repository / "scripts", symlinks=True)
        shutil.copy2(ROOT / "hugo.toml", repository / "hugo.toml")
        return repository

    def _add_public_content(self, repository: Path) -> None:
        content = repository / "generated/content"
        content.mkdir(parents=True)
        (content / "_index.md").write_text("---\ntitle: Cybernetks\n---\n", encoding="utf-8")

    def _replace_check_site(self, repository: Path, body: str) -> None:
        script = repository / "scripts/check-site"
        script.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
        script.chmod(0o755)

    def _command_shims(self, destination: Path) -> Path:
        commands = destination / "commands"
        commands.mkdir()
        (commands / "python3").write_text(
            "#!/bin/sh\necho 'default python ran' >&2\nexit 1\n",
            encoding="utf-8",
        )
        (commands / "hugo").write_text(
            "#!/bin/sh\n"
            "if [ \"${1:-}\" = version ]; then\n"
            "  echo 'hugo v0.164.0-test+extended test/arm64'\n"
            "fi\n",
            encoding="utf-8",
        )
        for command in commands.iterdir():
            command.chmod(0o755)
        return commands


if __name__ == "__main__":
    unittest.main()
