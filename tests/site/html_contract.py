"""Validate deployable Hugo output without reaching the network."""

from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urljoin, urlsplit

import yaml


ORIGIN = "https://cybernetks.be"
DOMAIN = "cybernetks.be"
LOCAL_SCHEMES = {"", "http", "https"}
EXTERNAL_SCHEMES = {"data", "javascript", "mailto", "tel"}
ANALYTICS_MARKERS = (
    "analytics",
    "googletagmanager",
    "google-analytics",
    "plausible",
    "fathom",
    "umami",
)
FORBIDDEN_COPY = (
    ("Portal", "Portal"),
    ("newsletter signup", "newsletter signup"),
    ("member login", "member login"),
)
EXPECTED_LEGACY_ROUTE_COUNT = 40
MANIFEST_FIELDS = frozenset({"path", "kind", "status", "replacement"})
ROUTE_SEGMENT = re.compile(r"^[a-z0-9](?:[a-z0-9._~-]*[a-z0-9_~-])?$")


class _PageParser(HTMLParser):
    """Collect emitted-HTML facts checked by ``check_public_tree``."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[tuple[str, str]] = []
        self.canonicals: list[str] = []
        self.metas: dict[str, list[str]] = {}
        self.title_parts: list[str] = []
        self.main_count = 0
        self.h1_count = 0
        self.refresh_targets: list[str] = []
        self.script_sources: list[str] = []
        self.inline_script_parts: list[str] = []
        self._in_title = False
        self._script_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()
        for attribute in ("href", "src"):
            value = attributes.get(attribute)
            if value:
                self.references.append((attribute, value))
        if srcset := attributes.get("srcset"):
            for candidate in srcset.split(","):
                source = candidate.strip().split(maxsplit=1)[0]
                if source:
                    self.references.append(("srcset", source))
        if tag == "link" and "canonical" in attributes.get("rel", "").lower().split():
            self.canonicals.append(attributes.get("href", ""))
        if tag == "meta":
            key = attributes.get("property") or attributes.get("name")
            if key:
                self.metas.setdefault(key.lower(), []).append(attributes.get("content", ""))
            if attributes.get("http-equiv", "").lower() == "refresh":
                target = _refresh_target(attributes.get("content", ""))
                if target:
                    self.refresh_targets.append(target)
        if tag == "title":
            self._in_title = True
        elif tag == "main":
            self.main_count += 1
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "script":
            self._script_depth += 1
            if source := attributes.get("src"):
                self.script_sources.append(source)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False
        elif tag.lower() == "script" and self._script_depth:
            self._script_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._script_depth:
            self.inline_script_parts.append(data)


def _refresh_target(content: str) -> str | None:
    match = re.search(r"(?:^|;)\s*url\s*=\s*(.+?)\s*$", content, re.IGNORECASE)
    return match.group(1).strip(" '\"") if match else None


def _canonical_route(value: object, *, allow_root: bool) -> bool:
    """Accept one literal spelling for a public site-relative route."""
    if not isinstance(value, str):
        return False
    if value == "/":
        return allow_root
    if not value.startswith("/") or not value.endswith("/"):
        return False
    return all(ROUTE_SEGMENT.fullmatch(segment) for segment in value[1:-1].split("/"))


def _manifest_routes(manifest: Path) -> tuple[list[tuple[str, str]], list[str]]:
    routes: list[tuple[str, str]] = []
    errors: list[str] = []
    try:
        entries = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        problem = getattr(error, "problem", None) or type(error).__name__
        return [], [f"invalid migration manifest: {problem}"]
    if not isinstance(entries, list):
        return [], ["invalid migration manifest: expected a list"]
    if len(entries) != EXPECTED_LEGACY_ROUTE_COUNT:
        errors.append(
            "migration route count: "
            f"expected {EXPECTED_LEGACY_ROUTE_COUNT}, got {len(entries)}"
        )

    seen_paths: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            errors.append(f"invalid migration entry {index}: expected a mapping")
            continue
        fields = set(entry)
        if fields != MANIFEST_FIELDS:
            errors.append(
                f"invalid migration entry {index}: expected fields "
                "kind, path, replacement, status"
            )
            continue
        path = entry["path"]
        replacement = entry["replacement"]
        if not _canonical_route(path, allow_root=False):
            errors.append(f"invalid migration entry {index}: invalid path route: {path}")
            continue
        if not _canonical_route(replacement, allow_root=True):
            errors.append(
                f"invalid migration entry {index}: invalid replacement route: {replacement}"
            )
            continue
        if entry["kind"] not in {"page", "post"} or entry["status"] != "published":
            errors.append(f"invalid migration entry {index}: invalid kind or status")
            continue
        if path in seen_paths:
            errors.append(f"duplicate migration route: {path}")
            continue
        seen_paths.add(path)
        routes.append((path, replacement))
    return routes, errors


def _route_file(public: Path, route: str) -> Path:
    return public / route.strip("/") / "index.html"


def _page_route(public: Path, page: Path) -> str:
    relative = page.relative_to(public).as_posix()
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return "/" + relative.removesuffix("index.html")
    return "/" + relative


def _expected_url(route: str) -> str:
    return urljoin(f"{ORIGIN}/", route.lstrip("/"))


def _local_reference(page_url: str, reference: str) -> str | None:
    parsed = urlsplit(reference)
    scheme = parsed.scheme.lower()
    if scheme in EXTERNAL_SCHEMES or scheme not in LOCAL_SCHEMES:
        return None
    resolved = urlsplit(urljoin(page_url, reference))
    if resolved.netloc and resolved.netloc.lower() != DOMAIN:
        return None
    return resolved.path or "/"


def _output_exists(public: Path, url_path: str) -> bool:
    relative = unquote(url_path).lstrip("/")
    candidate = public / relative
    return (
        candidate.is_file()
        or (candidate.is_dir() and (candidate / "index.html").is_file())
        or (not Path(relative).suffix and (candidate / "index.html").is_file())
    )


def _is_analytics(source: str) -> bool:
    return any(marker in source.lower() for marker in ANALYTICS_MARKERS)


def _check_page(
    public: Path, page: Path, alias_targets: dict[str, str]
) -> tuple[list[str], _PageParser]:
    relative = page.relative_to(public).as_posix()
    page_label = f"/{relative}"
    page_route = _page_route(public, page)
    page_url = _expected_url(page_route)
    html = page.read_text(encoding="utf-8")
    parser = _PageParser()
    parser.feed(html)
    parser.close()
    errors: list[str] = []
    redirect_target = parser.refresh_targets[0] if parser.refresh_targets else None
    alias_target = alias_targets.get(page_route)
    expected_alias_url = _expected_url(alias_target) if alias_target else None
    actual_redirect_url = urljoin(page_url, redirect_target) if redirect_target else None
    verified_alias_redirect = (
        alias_target is not None
        and actual_redirect_url is not None
        and actual_redirect_url == expected_alias_url
    )
    expected_canonical = expected_alias_url or page_url
    if len(parser.canonicals) != 1:
        errors.append(f"canonical count: {page_label} -> {len(parser.canonicals)}")
    elif parser.canonicals[0] != expected_canonical:
        errors.append(f"invalid canonical: {page_label} -> {parser.canonicals[0]}")
    if redirect_target and alias_target is None:
        errors.append(f"unexpected redirect: {page_label} -> {actual_redirect_url}")
    for attribute, reference in parser.references:
        if (url_path := _local_reference(page_url, reference)) and not _output_exists(
            public, url_path
        ):
            errors.append(f"missing local {attribute}: {page_label} -> {reference}")
    for image in parser.metas.get("og:image", []):
        if (url_path := _local_reference(page_url, image)) and not _output_exists(
            public, url_path
        ):
            errors.append(f"missing local og:image: {page_label} -> {image}")
    if not verified_alias_redirect:
        if not "".join(parser.title_parts).strip():
            errors.append(f"missing title: {page_label}")
        for metadata in ("description", "og:title", "og:description", "og:image"):
            if not any(value.strip() for value in parser.metas.get(metadata, [])):
                errors.append(f"missing {metadata}: {page_label}")
        if parser.main_count == 0:
            errors.append(f"missing main landmark: {page_label}")
        elif parser.main_count != 1:
            errors.append(f"main landmark count: {page_label} -> {parser.main_count}")
        if parser.h1_count == 0:
            errors.append(f"missing h1: {page_label}")
        elif parser.h1_count != 1:
            errors.append(f"h1 count: {page_label} -> {parser.h1_count}")
    for source in parser.script_sources:
        if _is_analytics(source):
            errors.append(f"analytics script: {page_label} -> {source}")
    if _is_analytics("".join(parser.inline_script_parts)):
        errors.append(f"analytics script: {page_label} -> inline")
    for forbidden, label in FORBIDDEN_COPY:
        haystack = html if label == "Portal" else html.casefold()
        if forbidden in haystack:
            errors.append(f"forbidden {label}: {page_label}")
    return errors, parser


def check_public_tree(public: Path, manifest: Path) -> list[str]:
    """Return deterministic, human-actionable errors for a built public tree."""
    errors: list[str] = []
    parsers: dict[str, _PageParser] = {}
    routes, manifest_errors = _manifest_routes(manifest)
    errors.extend(manifest_errors)
    alias_targets = {
        path: replacement for path, replacement in routes if path != replacement
    }
    for page in sorted(public.rglob("*.html")):
        page_errors, parser = _check_page(public, page, alias_targets)
        parsers[_page_route(public, page)] = parser
        errors.extend(page_errors)
    for path, replacement in routes:
        route_file = _route_file(public, path)
        if not route_file.is_file():
            errors.append(f"missing legacy route: {path}")
            continue
        if path == replacement:
            continue
        if not _route_file(public, replacement).is_file():
            errors.append(f"missing redirect target: {path} -> {replacement}")
        parser = parsers.get(path)
        actual = parser.refresh_targets[0] if parser and parser.refresh_targets else None
        expected = _expected_url(replacement)
        if actual is None:
            errors.append(f"missing legacy redirect: {path} -> {expected}")
        else:
            actual_url = urljoin(_expected_url(path), actual)
            if actual_url != expected:
                errors.append(f"wrong legacy redirect: {path} -> {actual_url}")
    return sorted(set(errors))
