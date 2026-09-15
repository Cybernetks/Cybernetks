from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest

from tests.publish.test_transaction import valid_vault
from tools.publish.__main__ import main


class PublisherCliTest(unittest.TestCase):
    def test_success_prints_kind_and_asset_counts(self) -> None:
        # Returning success without the report would hide what the publisher changed.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            repository.mkdir()
            vault = valid_vault(root / "vault")
            output = StringIO()

            with redirect_stdout(output):
                result = main(["--vault", str(vault), "--repository", str(repository)])

        self.assertEqual(result, 0)
        self.assertIn("log=3", output.getvalue())
        self.assertIn("snapshot=1", output.getvalue())
        self.assertIn("assets=1", output.getvalue())

    def test_expected_content_failure_returns_two_without_traceback(self) -> None:
        # Leaking exceptions through the CLI makes ordinary note corrections hard to act on.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            repository.mkdir()
            errors = StringIO()

            with redirect_stderr(errors):
                result = main(["--vault", str(root), "--repository", str(repository)])

        self.assertEqual(result, 2)
        self.assertIn("required allowlisted directory is missing", errors.getvalue())
        self.assertNotIn("Traceback", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
