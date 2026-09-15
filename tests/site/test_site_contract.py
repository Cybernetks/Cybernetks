from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tests.site.build import build_site


class HugoSmokeTest(unittest.TestCase):
    def test_homepage_builds_with_canonical_origin(self) -> None:
        public = build_site()
        html = (public / "index.html").read_text(encoding="utf-8")
        self.assertIn('<link rel="canonical" href="https://cybernetks.be/">', html)


class HugoPreflightTest(unittest.TestCase):
    def assert_build_rejected(self, version: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake_hugo = Path(directory) / "hugo"
            fake_hugo.write_text(
                f'#!/bin/sh\necho "{version}"\n', encoding="utf-8"
            )
            fake_hugo.chmod(0o755)
            with patch.dict(
                os.environ, {"PATH": f"{directory}:{os.environ['PATH']}"}
            ):
                with self.assertRaises(subprocess.CalledProcessError):
                    build_site()

    def test_rejects_non_extended_hugo(self) -> None:
        self.assert_build_rejected("hugo v0.164.0-ce2470 darwin/arm64")

    def test_rejects_wrong_hugo_version(self) -> None:
        self.assert_build_rejected("hugo v0.165.0-ce2470+extended darwin/arm64")
