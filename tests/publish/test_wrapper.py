import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class PublishWrapperTest(unittest.TestCase):
    def test_wrapper_uses_project_venv_when_default_python_lacks_pyyaml(self) -> None:
        # Reverting to `python3` would run this shim and fail before publishing.
        with tempfile.TemporaryDirectory() as directory:
            repository = self._repository_copy(Path(directory), include_venv=True)
            commands = self._command_shims(Path(directory))

            result = subprocess.run(
                ["./scripts/publish-site"],
                cwd=repository,
                env={
                    **os.environ,
                    "CYBERNETKS_VAULT": str(repository / "tests/fixtures/vault"),
                    "PATH": f"{commands}:{os.defpath}",
                },
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("hugo v0.164.0-test+extended", result.stdout)
            self.assertIn("Published: log=3", result.stdout)
            self.assertNotIn("default python has no PyYAML", result.stderr)

    def test_wrapper_explains_when_project_dependencies_are_unavailable(self) -> None:
        # Falling back to an arbitrary host interpreter would hide a missing project environment.
        with tempfile.TemporaryDirectory() as directory:
            repository = self._repository_copy(Path(directory), include_venv=False)

            result = subprocess.run(
                ["./scripts/publish-site"],
                cwd=repository,
                env={
                    **os.environ,
                    "CYBERNETKS_VAULT": str(repository / "tests/fixtures/vault"),
                    "PATH": os.defpath,
                },
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Python 3.12 virtual environment is required", result.stderr)

    def test_wrapper_explains_when_project_venv_lacks_pinned_dependencies(self) -> None:
        # Falling through to a host package would turn a broken environment into a hidden dependency.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = self._repository_copy(root, include_venv=False)
            python = repository / ".venv/bin/python"
            python.parent.mkdir(parents=True)
            python.write_text(
                "#!/bin/sh\n"
                "case \"${2:-}\" in\n"
                "  *'import sys'*) exit 0 ;;\n"
                "  *'import yaml'*) exit 1 ;;\n"
                "esac\n"
                "exit 1\n",
                encoding="utf-8",
            )
            python.chmod(0o755)

            result = subprocess.run(
                ["./scripts/publish-site"],
                cwd=repository,
                env={
                    **os.environ,
                    "CYBERNETKS_VAULT": str(repository / "tests/fixtures/vault"),
                    "PATH": os.defpath,
                },
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing pinned publisher dependencies", result.stderr)

    def test_wrapper_rejects_a_wrong_pyyaml_version(self) -> None:
        # Removing the gate or changing its pin must reject these expectations.
        for version, expected_status in (("6.0.1", 1), ("6.0.2", 73)):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                repository = self._repository_copy(root, include_venv=True)
                packages = root / "python-path"
                yaml_package = packages / "yaml"
                yaml_package.mkdir(parents=True)
                (yaml_package / "__init__.py").write_text(
                    f'__version__ = "{version}"\n', encoding="utf-8"
                )
                commands = root / "commands"
                commands.mkdir()
                hugo = commands / "hugo"
                # Stop at the next boundary: this minimal yaml only models its version.
                hugo.write_text(
                    "#!/bin/sh\n"
                    "echo 'reached Hugo preflight' >&2\n"
                    "exit 73\n",
                    encoding="utf-8",
                )
                hugo.chmod(0o755)
                environment = {
                    **os.environ,
                    "CYBERNETKS_VAULT": str(repository / "tests/fixtures/vault"),
                    "PATH": f"{commands}:{os.defpath}",
                    "PYTHONPATH": str(packages),
                    "PYTHONNOUSERSITE": "1",
                }
                # Verify the real interpreter can import the controlled package.
                imported = subprocess.run(
                    [str(repository / ".venv/bin/python"), "-c",
                     "import yaml; print(yaml.__version__)"],
                    cwd=repository,
                    env=environment,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(imported.returncode, 0, imported.stderr)
                self.assertEqual(imported.stdout.strip(), version)

                result = subprocess.run(
                    ["./scripts/publish-site"],
                    cwd=repository,
                    env=environment,
                    capture_output=True,
                    text=True,
                )

                self.assertEqual(result.returncode, expected_status, result.stderr)
                if version == "6.0.1":
                    self.assertIn("must provide PyYAML 6.0.2", result.stderr)
                    self.assertNotIn("reached Hugo preflight", result.stderr)
                else:
                    self.assertIn("reached Hugo preflight", result.stderr)
                    self.assertNotIn("must provide PyYAML", result.stderr)
                self.assertFalse((repository / "generated").exists())

    def _repository_copy(self, destination: Path, *, include_venv: bool) -> Path:
        repository = destination / "repository"
        repository.mkdir()
        for relative_path in ("tools", "scripts", "tests/fixtures"):
            shutil.copytree(ROOT / relative_path, repository / relative_path, symlinks=True)
        shutil.copy2(ROOT / "hugo.toml", repository / "hugo.toml")
        if include_venv:
            shutil.copytree(ROOT / ".venv", repository / ".venv", symlinks=True)
        return repository

    def _command_shims(self, destination: Path) -> Path:
        commands = destination / "commands"
        commands.mkdir()
        (commands / "python3").write_text(
            "#!/bin/sh\n"
            "echo 'default python has no PyYAML' >&2\n"
            "exit 1\n",
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
