"""Render validated publication documents as deterministic Hugo page bundles."""

from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
import re
from typing import Iterable, Mapping

import yaml

from tools.publish.frontmatter import normalize_public_path
from tools.publish.models import ContentKind, SourceDocument, SourceValidationError


_NUMBERED_LOG_TITLE = re.compile(r"^\s*#?\d+\s*-\s*")
_SLUG = re.compile(r"[^a-z0-9]+")
_REVIEW_MONTH = re.compile(r"^\d{4}-\d{2}$")


@dataclass
class SectionDocument:
    """Publisher-owned Hugo section metadata eligible for migration aliases."""

    title: str
    url_path: str
    aliases: list[str] = field(default_factory=list)


def bundle_path(document: SourceDocument) -> Path:
    """Return the deterministic page-bundle path for one public document."""
    if document.kind == ContentKind.LOG:
        return Path("logs") / _source_slug(document) / "index.md"
    if document.kind == ContentKind.SNAPSHOT:
        review_month = document.params.get("review_month")
        if not isinstance(review_month, str) or not _REVIEW_MONTH.fullmatch(review_month):
            raise _document_error(document, "review_month must be YYYY-MM")
        return Path("snapshots") / review_month / "index.md"
    if document.kind == ContentKind.PROJECT:
        return Path("projects") / _project_slug(document) / "_index.md"
    if document.kind == ContentKind.PAGE:
        return Path(*_route_parts(_fixed_page_route(document))) / "index.md"
    raise _document_error(document, f"unsupported content kind: {document.kind}")


def serialize_document(document: SourceDocument) -> str:
    """Serialize a generated document with stable front-matter ordering."""
    template_params: dict[str, object] = {"kind": document.kind.value}
    for key in sorted(document.params):
        if key not in {"topics", "projects", "aliases"}:
            template_params[key] = document.params[key]
    metadata: dict[str, object] = {
        "title": _display_title(document),
        "date": document.publish_date.isoformat(),
        "description": document.summary,
        "url": document.url_path,
        "topics": _string_list(document.params.get("topics", []), document, "topics"),
        "projects": _string_list(document.params.get("projects", []), document, "projects"),
        "aliases": sorted(_string_list(document.params.get("aliases", []), document, "aliases")),
        "params": template_params,
    }
    return _serialize(metadata, document.body)


def render_bundle(document: SourceDocument, destination: Path) -> Path:
    """Write one document to its page-bundle ``index.md`` and return its path."""
    written = Path(destination) / bundle_path(document)
    written.parent.mkdir(parents=True, exist_ok=True)
    written.write_text(serialize_document(document), encoding="utf-8")
    return written


def render_section(section: SectionDocument, destination: Path) -> Path:
    """Write publisher-owned metadata for Hugo's home or section nodes."""
    route = _route_parts(section.url_path, allow_root=True)
    written = Path(destination) / (Path(*route) / "_index.md" if route else Path("_index.md"))
    written.parent.mkdir(parents=True, exist_ok=True)
    written.write_text(
        _serialize(
            {
                "title": section.title,
                "url": section.url_path,
                "aliases": sorted(_unique_aliases(section.aliases)),
            },
            "",
        ),
        encoding="utf-8",
    )
    return written


def apply_migration_aliases(
    documents: Iterable[SourceDocument],
    section_documents: Iterable[SectionDocument],
    entries: Iterable[Mapping[str, object]],
) -> None:
    """Attach non-identity migration paths to the document or section they replace."""
    document_list = list(documents)
    section_list = list(section_documents)
    targets: dict[str, SourceDocument | SectionDocument] = {}
    for target in [*document_list, *section_list]:
        route = _normalized_route(target.url_path, "replacement")
        if route in targets:
            raise SourceValidationError(f"migration: duplicate replacement target: {route}")
        targets[route] = target

    claimed_legacy_paths: set[str] = set()
    canonical_routes = set(targets)
    for entry in entries:
        path = _entry_route(entry, "path")
        replacement = _entry_route(entry, "replacement")
        if path == replacement:
            continue
        if path in claimed_legacy_paths:
            raise SourceValidationError(f"migration: duplicate legacy path: {path}")
        if path in canonical_routes:
            raise SourceValidationError(f"migration: legacy path collides with canonical route: {path}")
        target = targets.get(replacement)
        if target is None:
            raise SourceValidationError(
                f"migration: replacement target is missing: {replacement}"
            )
        _add_alias(target, path)
        claimed_legacy_paths.add(path)


def _source_slug(document: SourceDocument) -> str:
    slug = _SLUG.sub("-", document.source_path.stem.casefold()).strip("-")
    if not slug:
        raise _document_error(document, "source filename has no safe bundle slug")
    return slug


def _project_slug(document: SourceDocument) -> str:
    route = _route_parts(document.url_path)
    if len(route) != 2 or route[0] != "projects":
        raise _document_error(document, "project url must be /projects/<project-slug>/")
    return route[1]


def _fixed_page_route(document: SourceDocument) -> str:
    source_parts = document.source_path.parts
    if source_parts[-2:] == ("Pages", "About Cybernetks.md"):
        expected = "/about/"
    elif source_parts[-2:] == ("Pages", "Support.md"):
        expected = "/support/"
    elif source_parts[-2:] == ("Pages", "Uses.md"):
        expected = "/uses/"
    elif len(source_parts) >= 3 and source_parts[-3] == "Projects" and source_parts[-1] in {
        "Privacy.md",
        "Support.md",
    }:
        project_slug = _SLUG.sub("-", source_parts[-2].casefold()).strip("-")
        expected = f"/projects/{project_slug}/{source_parts[-1][:-3].casefold()}/"
    else:
        raise _document_error(document, "page is not an allowlisted page identity")
    if document.url_path != expected:
        raise _document_error(document, f"url: must be {expected}")
    return expected


def _route_parts(route: str, *, allow_root: bool = False) -> tuple[str, ...]:
    normalized = _normalized_route(route, "url")
    parts = PurePosixPath(normalized).parts[1:]
    if not parts and not allow_root:
        raise SourceValidationError("url: root is only valid for a section")
    if any(part in {"", ".", ".."} for part in parts):
        raise SourceValidationError(f"url: unsafe route: {normalized}")
    return tuple(parts)


def _normalized_route(value: object, field: str) -> str:
    try:
        return normalize_public_path(value)  # type: ignore[arg-type]
    except SourceValidationError as error:
        raise SourceValidationError(f"migration: {field}: {error}") from None


def _display_title(document: SourceDocument) -> str:
    if document.kind == ContentKind.LOG:
        title = _NUMBERED_LOG_TITLE.sub("", document.title).strip()
        if title:
            return title
    return document.title


def _string_list(value: object, document: SourceDocument, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise _document_error(document, f"{field} must be a list of non-empty strings")
    return list(value)


def _add_alias(target: SourceDocument | SectionDocument, path: str) -> None:
    if isinstance(target, SectionDocument):
        target.aliases = _unique_aliases([*target.aliases, path])
        return
    aliases = _string_list(target.params.get("aliases", []), target, "aliases")
    target.params["aliases"] = _unique_aliases([*aliases, path])


def _unique_aliases(aliases: Iterable[str]) -> list[str]:
    return sorted(set(aliases))


def _serialize(metadata: Mapping[str, object], body: str) -> str:
    front_matter = yaml.safe_dump(
        dict(metadata), allow_unicode=True, default_flow_style=False, sort_keys=False
    )
    normalized_body = body.strip()
    return f"---\n{front_matter}---\n" + (f"\n{normalized_body}\n" if normalized_body else "")


def _entry_route(entry: Mapping[str, object], field: str) -> str:
    if field not in entry:
        raise SourceValidationError(f"migration: {field}: is required")
    return _normalized_route(entry[field], field)


def _document_error(document: SourceDocument, explanation: str) -> SourceValidationError:
    return SourceValidationError(f"{document.source_path.as_posix()}: {explanation}")
