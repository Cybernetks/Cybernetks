"""Discover only explicitly allowlisted published source notes."""

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

import yaml

from tools.publish.config import PublisherConfig
from tools.publish.models import ContentKind, SourceValidationError


@dataclass(frozen=True)
class DiscoveredSource:
    source_path: Path
    relative_path: Path
    kind: ContentKind


def discover_sources(
    vault_root: Path, config: PublisherConfig = PublisherConfig()
) -> list[DiscoveredSource]:
    """Return published Markdown notes from the fixed publication allowlist.

    This is intentionally only a selection step. Full front-matter validation
    remains at ``parse_source`` after selection, so invalid published notes are
    rejected rather than treated as valid publication metadata.
    """
    root = Path(vault_root)
    _reject_duplicate_allowlist_entries(config)
    _reject_allowlist_overlaps(config)
    candidates = _directory_sources(root, config.directories)
    candidates.extend(_listed_sources(root, config.files, required=True))
    candidates.extend(_listed_sources(root, config.optional_files, required=False))
    _reject_duplicate_candidates(candidates)

    sources = [
        DiscoveredSource(path, path.relative_to(root), kind)
        for path, kind in candidates
        if _publication_status(path) == "published"
    ]
    return sorted(sources, key=lambda item: item.relative_path.as_posix())


def _directory_sources(
    root: Path, directories: Iterable[tuple[str, ContentKind]]
) -> list[tuple[Path, ContentKind]]:
    candidates: list[tuple[Path, ContentKind]] = []
    for relative_directory, kind in directories:
        directory = root / relative_directory
        if not directory.is_dir():
            raise SourceValidationError(
                f"{directory.as_posix()}: source: required allowlisted directory is missing"
            )
        candidates.extend((path, kind) for path in directory.rglob("*.md") if path.is_file())
    return candidates


def _reject_duplicate_allowlist_entries(config: PublisherConfig) -> None:
    _reject_duplicate_entries(config.directories, "directory")
    _reject_duplicate_entries(config.files + config.optional_files, "file")


def _reject_duplicate_entries(
    entries: Iterable[tuple[str, ContentKind]], entry_type: str
) -> None:
    seen: set[str] = set()
    for relative_path, _ in entries:
        if relative_path in seen:
            raise SourceValidationError(
                f"{relative_path}: source: duplicate allowlisted {entry_type}"
            )
        seen.add(relative_path)


def _reject_allowlist_overlaps(config: PublisherConfig) -> None:
    directories = tuple(relative_path for relative_path, _ in config.directories)
    for index, first_directory in enumerate(directories):
        for second_directory in directories[index + 1 :]:
            overlap = _nested_path(first_directory, second_directory)
            if overlap is not None:
                nested, parent = overlap
                raise SourceValidationError(
                    f"{nested}: source: overlaps allowlisted directory {parent}"
                )

    for relative_file, _ in config.files + config.optional_files:
        for relative_directory in directories:
            if _is_within(relative_file, relative_directory):
                raise SourceValidationError(
                    f"{relative_file}: source: overlaps allowlisted directory {relative_directory}"
                )


def _nested_path(first: str, second: str) -> tuple[str, str] | None:
    if _is_within(first, second):
        return first, second
    if _is_within(second, first):
        return second, first
    return None


def _is_within(path: str, parent: str) -> bool:
    path_parts = PurePosixPath(path).parts
    parent_parts = PurePosixPath(parent).parts
    return path_parts[: len(parent_parts)] == parent_parts


def _reject_duplicate_candidates(candidates: Iterable[tuple[Path, ContentKind]]) -> None:
    seen: set[Path] = set()
    for source_path, _ in candidates:
        if source_path in seen:
            raise SourceValidationError(
                f"{source_path.as_posix()}: source: selected by multiple allowlist entries"
            )
        seen.add(source_path)


def _listed_sources(
    root: Path,
    files: Iterable[tuple[str, ContentKind]],
    *,
    required: bool,
) -> list[tuple[Path, ContentKind]]:
    candidates: list[tuple[Path, ContentKind]] = []
    for relative_file, kind in files:
        source_path = root / relative_file
        if source_path.is_file():
            candidates.append((source_path, kind))
        elif required:
            raise SourceValidationError(
                f"{source_path.as_posix()}: source: required allowlisted source is missing"
            )
    return candidates


def _publication_status(path: Path) -> object:
    """Read only the front-matter switch used to select a candidate source."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return None
    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.rstrip("\r\n") == "---"),
        None,
    )
    if closing_index is None:
        return None
    try:
        metadata = yaml.safe_load("".join(lines[1:closing_index]))
    except yaml.YAMLError:
        return None
    if not isinstance(metadata, dict):
        return None
    return metadata.get("publication_status")
