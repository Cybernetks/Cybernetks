"""Parse and validate the front matter boundary for public source notes."""

from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml
from yaml.resolver import BaseResolver

from tools.publish.models import ContentKind, SourceDocument, SourceValidationError


_PUBLICATION_STATUSES = {"draft", "published"}
_CANONICAL_HOSTS = {"cybernetks.be", "www.cybernetks.be"}
_SHARED_FIELDS = {
    "title",
    "publication_status",
    "publish_date",
    "summary",
    "url",
}
_KIND_REQUIRED_FIELDS = {
    ContentKind.SNAPSHOT: ("review_month",),
    ContentKind.PROJECT: ("status", "promise", "project_kind"),
}
_PROJECT_ONLY_FIELDS = frozenset(_KIND_REQUIRED_FIELDS[ContentKind.PROJECT])


class _DuplicateKeyError(yaml.YAMLError):
    def __init__(self, key: object) -> None:
        self.key = str(key)


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[object, Any]:
    loader.flatten_mapping(node)
    mapping: dict[object, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise _DuplicateKeyError(key)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def load_unique_yaml(text: str) -> Any:
    """Load YAML while rejecting duplicate mapping keys at every nesting level."""
    return yaml.load(text, Loader=_UniqueKeyLoader)


def normalize_public_path(value: str) -> str:
    """Return a canonical site-relative path for an approved public URL."""
    if not isinstance(value, str) or not value:
        raise SourceValidationError("url: must be a non-empty string")

    parsed = urlsplit(value)
    if parsed.query:
        raise SourceValidationError("url: must not include a query string")
    if parsed.fragment:
        raise SourceValidationError("url: must not include a fragment")

    if parsed.scheme:
        if parsed.scheme != "https":
            raise SourceValidationError("url: must use HTTPS")
        if parsed.netloc not in _CANONICAL_HOSTS:
            raise SourceValidationError("url: must use the cybernetks.be host")
    elif parsed.netloc:
        raise SourceValidationError("url: must be site-relative or use the cybernetks.be host")
    elif not parsed.path.startswith("/"):
        raise SourceValidationError("url: must start with a slash")

    if not parsed.path.endswith("/"):
        raise SourceValidationError("url: must end with a slash")
    return parsed.path


def parse_source(path: Path, kind: ContentKind) -> SourceDocument:
    """Parse one Markdown source note without making any publishing decisions."""
    source_path = Path(path)
    content_kind = _validated_content_kind(kind, source_path)
    metadata, body = _read_front_matter(source_path)
    _reject_project_only_fields(metadata, content_kind, source_path)
    publication_status = _required_string(
        metadata, "publication_status", source_path
    )
    if publication_status not in _PUBLICATION_STATUSES:
        _raise(source_path, "publication_status", "must be 'published' or 'draft'")

    if publication_status == "published":
        title = _required_string(metadata, "title", source_path)
        publish_date = _required_date(metadata, "publish_date", source_path)
        summary = _required_string(metadata, "summary", source_path)
        url_value = _required_string(metadata, "url", source_path)
        try:
            url_path = normalize_public_path(url_value)
        except SourceValidationError as error:
            _raise(source_path, "url", _explanation(error))
    else:
        title = _optional_string(metadata, "title", source_path)
        publish_date = _optional_date(metadata, "publish_date", source_path)
        summary = _optional_string(metadata, "summary", source_path)
        url_path = _optional_url(metadata, source_path)

    for field in _KIND_REQUIRED_FIELDS.get(content_kind, ()):
        _required_string(metadata, field, source_path)

    params = {key: value for key, value in metadata.items() if key not in _SHARED_FIELDS}
    return SourceDocument(
        source_path=source_path,
        kind=content_kind,
        title=title,
        publication_status=publication_status,
        publish_date=publish_date,
        summary=summary,
        url_path=url_path,
        params=params,
        body=body,
    )


def _read_front_matter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        _raise(path, "front_matter", "must start with a YAML delimiter")

    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.rstrip("\r\n") == "---"),
        None,
    )
    if closing_index is None:
        _raise(path, "front_matter", "is missing its closing YAML delimiter")

    try:
        loaded = load_unique_yaml("".join(lines[1:closing_index]))
    except _DuplicateKeyError as error:
        _raise(path, error.key, "must not be duplicated")
    except yaml.YAMLError:
        _raise(path, "front_matter", "contains invalid YAML")
    if not isinstance(loaded, dict):
        _raise(path, "front_matter", "must be a mapping")
    return loaded, "".join(lines[closing_index + 1 :])


def _validated_content_kind(kind: object, path: Path) -> ContentKind:
    try:
        return ContentKind(kind)
    except (TypeError, ValueError):
        _raise(path, "kind", "must be one of log, snapshot, project, page")


def _reject_project_only_fields(
    metadata: dict[str, Any], kind: ContentKind, path: Path
) -> None:
    if kind == ContentKind.PROJECT:
        return
    for field in _PROJECT_ONLY_FIELDS:
        if field in metadata:
            _raise(path, field, "is only allowed for projects")


def _required_string(metadata: dict[str, Any], field: str, path: Path) -> str:
    value = metadata.get(field)
    if not isinstance(value, str) or not value.strip():
        _raise(path, field, "is required")
    return value


def _optional_string(metadata: dict[str, Any], field: str, path: Path) -> str:
    if field not in metadata:
        return ""
    return _required_string(metadata, field, path)


def _required_date(metadata: dict[str, Any], field: str, path: Path) -> date:
    if field not in metadata:
        _raise(path, field, "is required")
    return _coerce_date(metadata[field], field, path)


def _optional_date(metadata: dict[str, Any], field: str, path: Path) -> date:
    if field not in metadata:
        return date.min
    return _coerce_date(metadata[field], field, path)


def _coerce_date(value: Any, field: str, path: Path) -> date:
    if isinstance(value, datetime):
        _raise(path, field, "must be an ISO 8601 date")
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    _raise(path, field, "must be an ISO 8601 date")


def _optional_url(metadata: dict[str, Any], path: Path) -> str:
    if "url" not in metadata:
        return ""
    value = _required_string(metadata, "url", path)
    try:
        return normalize_public_path(value)
    except SourceValidationError as error:
        _raise(path, "url", _explanation(error))


def _explanation(error: SourceValidationError) -> str:
    return str(error).split(": ", maxsplit=1)[-1]


def _raise(path: Path, field: str, explanation: str) -> None:
    raise SourceValidationError(f"{_display_path(path)}: {field}: {explanation}")


def _display_path(path: Path) -> str:
    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()
