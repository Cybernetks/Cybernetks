"""Extract deliberately public Markdown sections from publishing source notes."""

from dataclasses import dataclass
from pathlib import Path
import re

from tools.publish.models import ContentKind, SourceValidationError


_LEVEL_ONE_HEADING = re.compile(r"^#\s+(.+?)(?:\s+#+)?\s*$")
_LEVEL_TWO_HEADING = re.compile(r"^##\s+(.+?)(?:\s+#+)?\s*$")
_FENCE = re.compile(r"^\s{0,3}(?:`{3,}|~{3,})")


@dataclass(frozen=True)
class SnapshotSection:
    number: str
    title: str
    body: str


@dataclass(frozen=True)
class SnapshotStructure:
    one_sentence: str
    sections: tuple[SnapshotSection, ...]


def extract_public_body(markdown: str, kind: ContentKind, source_path: Path) -> str:
    """Return the public body selected by the documented marker precedence."""
    lines = markdown.splitlines()
    body = _between_level_one_headings(lines, "Blog post")
    if body is None:
        body = _after_level_two_heading(lines, "Published Content")
    if body is None:
        website_body = _after_level_two_heading(lines, "Website Content")
        if website_body is not None and kind not in {
            ContentKind.PAGE,
            ContentKind.PROJECT,
        }:
            raise _source_error(
                source_path,
                "Website Content is only allowed for project and page notes",
            )
        body = website_body
    if body is None:
        body = _after_first_level_one_heading(lines)

    extracted = "\n".join(body).strip()
    if not extracted:
        raise _source_error(source_path, "is empty")
    return extracted


def extract_snapshot_structure(body: str) -> SnapshotStructure | None:
    """Return structured Snapshot sections only when their explicit marker exists."""
    lines = body.splitlines()
    headings = _headings(lines, _LEVEL_TWO_HEADING)
    one_sentence_index = next(
        (index for index, (_, title) in enumerate(headings) if title == "The month in one sentence"),
        None,
    )
    if one_sentence_index is None:
        return None

    marker_line, _ = headings[one_sentence_index]
    next_heading_line = (
        headings[one_sentence_index + 1][0]
        if one_sentence_index + 1 < len(headings)
        else len(lines)
    )
    one_sentence = "\n".join(lines[marker_line + 1 : next_heading_line]).strip()
    sections = tuple(
        SnapshotSection(
            number=f"{number:02d}",
            title=title,
            body="\n".join(
                lines[line_number + 1 : next_line_number]
            ).strip(),
        )
        for number, ((line_number, title), (next_line_number, _)) in enumerate(
            zip(headings[one_sentence_index + 1 :], headings[one_sentence_index + 2 :] + [(len(lines), "")]),
            start=1,
        )
    )
    return SnapshotStructure(one_sentence=one_sentence, sections=sections)


def _between_level_one_headings(lines: list[str], title: str) -> list[str] | None:
    marker_index = _heading_index(lines, _LEVEL_ONE_HEADING, title)
    if marker_index is None:
        return None
    end_index = next(
        (index for index, _ in _headings(lines, _LEVEL_ONE_HEADING) if index > marker_index),
        len(lines),
    )
    return lines[marker_index + 1 : end_index]


def _after_level_two_heading(lines: list[str], title: str) -> list[str] | None:
    marker_index = _heading_index(lines, _LEVEL_TWO_HEADING, title)
    return None if marker_index is None else lines[marker_index + 1 :]


def _after_first_level_one_heading(lines: list[str]) -> list[str]:
    title_index = next((index for index, _ in _headings(lines, _LEVEL_ONE_HEADING)), len(lines))
    return lines[title_index + 1 :]


def _heading_index(lines: list[str], pattern: re.Pattern[str], title: str) -> int | None:
    return next((index for index, heading in _headings(lines, pattern) if heading == title), None)


def _headings(lines: list[str], pattern: re.Pattern[str]) -> list[tuple[int, str]]:
    headings: list[tuple[int, str]] = []
    in_fenced_code = False
    for index, line in enumerate(lines):
        if _FENCE.match(line):
            in_fenced_code = not in_fenced_code
            continue
        if not in_fenced_code and (match := pattern.match(line)):
            headings.append((index, match.group(1)))
    return headings


def _source_error(source_path: Path, explanation: str) -> SourceValidationError:
    return SourceValidationError(f"{source_path.as_posix()}: public body: {explanation}")
