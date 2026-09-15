from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_CONTENT = ROOT / "tests/fixtures/site-content"
HUGO_PREFLIGHT = ROOT / "scripts/check-hugo"


def build_site(content_dir: Path | None = None) -> Path:
    destination = Path(tempfile.mkdtemp(prefix="cybernetks-hugo-"))
    subprocess.run([str(HUGO_PREFLIGHT)], check=True, cwd=ROOT)
    command = ["hugo", "--source", str(ROOT), "--destination", str(destination)]
    if content_dir is not None:
        command.extend(["--contentDir", str(content_dir)])
    subprocess.run(command, check=True, cwd=ROOT)
    return destination


def built_html(relative_path: str, content_dir: Path = FIXTURE_CONTENT) -> str:
    return (build_site(content_dir) / relative_path).read_text(encoding="utf-8")
