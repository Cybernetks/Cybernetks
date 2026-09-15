"""Resolve public Obsidian wiki links into canonical Hugo URLs."""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Callable, Iterable, Mapping

from tools.publish.models import SourceDocument, SourceValidationError


_WIKI_LINK = re.compile(r"(?<!!)\[\[([^\]\r\n]+)\]\]")
_FENCE_OPEN = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


@dataclass(frozen=True)
class PublicLinkIndex:
    """Public destinations keyed by note-relative path and unambiguous stem."""

    destinations: Mapping[str, str]
    ambiguous_basenames: frozenset[str]


def build_public_index(
    documents: Iterable[SourceDocument], vault_root: Path | None = None
) -> PublicLinkIndex:
    """Index validated public documents without guessing duplicate note names."""
    path_destinations: dict[str, str] = {}
    basename_sources: dict[str, set[str]] = defaultdict(set)
    basename_destinations: dict[str, str] = {}
    for document in documents:
        if document.publication_status != "published":
            continue
        note_path = _note_path(document.source_path, vault_root)
        path_destinations[note_path.casefold()] = document.url_path
        basename = Path(note_path).name.casefold()
        basename_sources[basename].add(note_path.casefold())
        basename_destinations.setdefault(basename, document.url_path)

    ambiguous = frozenset(
        basename
        for basename, sources in basename_sources.items()
        if len(sources) > 1
    )
    destinations = dict(path_destinations)
    destinations.update(
        (basename, destination)
        for basename, destination in basename_destinations.items()
        if basename not in ambiguous
    )
    return PublicLinkIndex(destinations=destinations, ambiguous_basenames=ambiguous)


def heading_anchor(value: str) -> str:
    """Return the stable fragment identifier used for public heading links."""
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def rewrite_links(
    document: SourceDocument,
    index: PublicLinkIndex | Mapping[str, str | SourceDocument | None],
) -> str:
    """Replace public wiki links while retaining ordinary Markdown untouched."""
    def rewrite(match: re.Match[str]) -> str:
        reference, separator, label = match.group(1).partition("|")
        note_reference, fragment_separator, fragment = reference.strip().partition("#")
        target = _normalize_reference(note_reference)
        destination = _resolve_destination(document, target, index)
        if fragment_separator:
            anchor = heading_anchor(fragment)
            if anchor:
                destination = f"{destination}#{anchor}"
        text = label if separator else (_display_name(target) if target else fragment)
        return f"[{text}]({destination})"

    return _replace_unprotected(document.body, _WIKI_LINK, rewrite)


def _resolve_destination(
    document: SourceDocument,
    target: str,
    index: PublicLinkIndex | Mapping[str, str | SourceDocument | None],
) -> str:
    if not target:
        return document.url_path
    key = target.casefold()
    if isinstance(index, PublicLinkIndex):
        if key in index.ambiguous_basenames:
            raise _link_error(document, f"ambiguous public link: {target}")
        destination = index.destinations.get(key)
    else:
        destination = index.get(key, index.get(target))
    if isinstance(destination, SourceDocument):
        destination = destination.url_path
    if not isinstance(destination, str) or not destination:
        raise _link_error(document, f"unresolved public link: {target}")
    return destination


def _note_path(path: Path, vault_root: Path | None) -> str:
    source = Path(path)
    if vault_root is not None:
        root = Path(vault_root).resolve()
        try:
            source = source.resolve().relative_to(root)
        except ValueError:
            pass
    return _normalize_reference(source.with_suffix("").as_posix())


def _normalize_reference(reference: str) -> str:
    value = reference.replace("\\", "/").strip().lstrip("/")
    if value.casefold().endswith(".md"):
        value = value[:-3]
    return value


def _display_name(reference: str) -> str:
    return Path(reference).name if reference else ""


def _replace_unprotected(
    markdown: str, pattern: re.Pattern[str], replace: Callable[[re.Match[str]], str]
) -> str:
    """Apply a Markdown replacement outside fenced and inline code spans."""
    rewritten: list[str] = []
    fence: tuple[str, int] | None = None
    for line in markdown.splitlines(keepends=True):
        if fence is not None:
            if _closes_fence(line, fence):
                fence = None
            rewritten.append(line)
        elif (opener := _fence_opener(line)) is not None:
            fence = opener
            rewritten.append(line)
        else:
            rewritten.append(_replace_outside_inline_code(line, pattern, replace))
    return "".join(rewritten)


def _fence_opener(line: str) -> tuple[str, int] | None:
    match = _FENCE_OPEN.match(line)
    if match is None:
        return None
    delimiter = match.group(1)
    return delimiter[0], len(delimiter)


def _closes_fence(line: str, fence: tuple[str, int]) -> bool:
    character, length = fence
    return re.match(rf"^\s{{0,3}}{re.escape(character)}{{{length},}}\s*$", line) is not None


def _replace_outside_inline_code(
    line: str, pattern: re.Pattern[str], replace: Callable[[re.Match[str]], str]
) -> str:
    rewritten: list[str] = []
    cursor = 0
    while cursor < len(line):
        opening = line.find("`", cursor)
        if opening < 0:
            rewritten.append(pattern.sub(replace, line[cursor:]))
            break
        rewritten.append(pattern.sub(replace, line[cursor:opening]))
        run_end = opening
        while run_end < len(line) and line[run_end] == "`":
            run_end += 1
        delimiter = line[opening:run_end]
        closing = line.find(delimiter, run_end)
        if closing < 0:
            rewritten.append(line[opening:])
            break
        rewritten.append(line[opening : closing + len(delimiter)])
        cursor = closing + len(delimiter)
    return "".join(rewritten)


def _link_error(document: SourceDocument, explanation: str) -> SourceValidationError:
    return SourceValidationError(f"{document.source_path.as_posix()}: {explanation}")
