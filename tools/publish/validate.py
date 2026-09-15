"""Cross-document and staged-tree validation for the publisher."""

from pathlib import Path
from typing import Iterable

import yaml

from tools.publish.models import SourceDocument, SourceValidationError
from tools.publish.render import bundle_path


def validate_documents(documents: Iterable[SourceDocument]) -> None:
    """Reject duplicate public URLs and generated bundle destinations."""
    urls: dict[str, SourceDocument] = {}
    bundles: dict[Path, SourceDocument] = {}
    for document in documents:
        existing_url = urls.get(document.url_path)
        if existing_url is not None:
            raise SourceValidationError(
                f"{document.source_path.as_posix()}: url: duplicates {existing_url.source_path.as_posix()}"
            )
        urls[document.url_path] = document
        path = bundle_path(document)
        existing_bundle = bundles.get(path)
        if existing_bundle is not None:
            raise SourceValidationError(
                f"{document.source_path.as_posix()}: bundle: duplicates {existing_bundle.source_path.as_posix()}"
            )
        bundles[path] = document


def validate_staged_content(content_root: Path) -> None:
    """Check the staged tree is self-contained, parseable Hugo content."""
    root = Path(content_root)
    if not root.is_dir() or not (root / "_index.md").is_file():
        raise SourceValidationError("generated content: missing publisher-owned home section")
    urls: set[str] = set()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise SourceValidationError(f"generated content: symbolic link is not allowed: {path}")
        if not path.is_file() or path.suffix != ".md":
            continue
        metadata = _front_matter(path)
        url = metadata.get("url")
        if isinstance(url, str) and url:
            if url in urls:
                raise SourceValidationError(f"generated content: duplicate url: {url}")
            urls.add(url)


def _front_matter(path: Path) -> dict[object, object]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SourceValidationError(f"generated content: missing front matter: {path}")
    closing = text.find("\n---\n", 4)
    if closing < 0:
        raise SourceValidationError(f"generated content: unclosed front matter: {path}")
    try:
        metadata = yaml.safe_load(text[4:closing])
    except yaml.YAMLError as error:
        raise SourceValidationError(f"generated content: invalid front matter: {path}") from error
    if not isinstance(metadata, dict):
        raise SourceValidationError(f"generated content: front matter is not a mapping: {path}")
    return metadata
