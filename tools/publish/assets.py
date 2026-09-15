"""Collect explicit local Obsidian embeds as safe Hugo page resources."""

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from tools.publish.links import _replace_unprotected
from tools.publish.models import SourceDocument, SourceValidationError


_EMBED = re.compile(r"!\[\[([^\]\r\n]+)\]\]")
_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"})
_MEDIA_EXTENSIONS = frozenset({".mp3", ".m4a"})
_SUPPORTED_EXTENSIONS = _IMAGE_EXTENSIONS | _MEDIA_EXTENSIONS
_UNSAFE_BASENAME = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class AssetCopy:
    source: Path
    bundle_name: str


@dataclass(frozen=True)
class _Embed:
    reference: str
    alt: str


def collect_assets(document: SourceDocument, vault_root: Path) -> list[AssetCopy]:
    """Return explicitly embedded local assets for this document's page bundle."""
    copies, _ = _collect(document, vault_root)
    return copies


def rewrite_embeds(document: SourceDocument, vault_root: Path) -> str:
    """Translate explicit embeds to page-resource Markdown after safe collection."""
    _, resource_for_reference = _collect(document, vault_root)

    def rewrite(match: re.Match[str]) -> str:
        embed = _parse_embed(match.group(1), document)
        resource = resource_for_reference[embed.reference]
        if resource.source.suffix.casefold() in _IMAGE_EXTENSIONS:
            alt = embed.alt or resource.source.stem
            return f"![{alt}]({resource.bundle_name})"
        label = embed.alt or resource.source.stem
        return f"[{label}]({resource.bundle_name})"

    return _replace_unprotected(document.body, _EMBED, rewrite)


def _collect(document: SourceDocument, vault_root: Path) -> tuple[list[AssetCopy], dict[str, AssetCopy]]:
    root = Path(vault_root).resolve()
    embeds = _embedded_references(document)
    sources_for_reference: dict[str, Path] = {}
    ordered_sources: list[Path] = []
    for embed in embeds:
        source = _resolve_asset(embed.reference, document, root)
        sources_for_reference[embed.reference] = source
        if source not in ordered_sources:
            ordered_sources.append(source)

    bundle_names = _bundle_names(ordered_sources)
    resource_for_source = {
        source: AssetCopy(source=source, bundle_name=bundle_names[source])
        for source in ordered_sources
    }
    return (
        [resource_for_source[source] for source in ordered_sources],
        {
            reference: resource_for_source[source]
            for reference, source in sources_for_reference.items()
        },
    )


def _embedded_references(document: SourceDocument) -> list[_Embed]:
    embeds: list[_Embed] = []

    def record(match: re.Match[str]) -> str:
        embeds.append(_parse_embed(match.group(1), document))
        return match.group(0)

    _replace_unprotected(document.body, _EMBED, record)
    return embeds


def _parse_embed(value: str, document: SourceDocument) -> _Embed:
    reference, _, alt = value.partition("|")
    reference = reference.strip()
    if not reference:
        raise _asset_error(document, "missing asset")
    return _Embed(reference=reference, alt=alt)


def _resolve_asset(reference: str, document: SourceDocument, root: Path) -> Path:
    normalized = reference.replace("\\", "/")
    relative = Path(normalized)
    if relative.is_absolute() or any(part == ".." for part in relative.parts):
        raise _asset_error(document, f"asset path traversal: {reference}")
    extension = relative.suffix.casefold()
    if extension not in _SUPPORTED_EXTENSIONS:
        display_extension = extension or "(none)"
        raise _asset_error(document, f"unsupported asset type: {display_extension}")

    source_parent = _source_parent(document.source_path, root)
    direct_candidates = [source_parent / relative, root / relative]
    matches = _safe_existing_files(direct_candidates, root)
    if not matches and len(relative.parts) == 1:
        matches = _safe_existing_files(root.rglob(relative.name), root)
    if not matches:
        raise _asset_error(document, f"missing asset: {reference}")
    if len(matches) > 1:
        raise _asset_error(document, f"ambiguous asset: {reference}")
    return matches[0]


def _source_parent(source_path: Path, root: Path) -> Path:
    source = Path(source_path)
    if not source.is_absolute():
        source = root / source
    resolved = source.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise SourceValidationError(f"{source_path.as_posix()}: asset source is outside the vault") from None
    return resolved.parent


def _safe_existing_files(candidates: object, root: Path) -> list[Path]:
    matches: set[Path] = set()
    for candidate in candidates:  # type: ignore[union-attr]
        try:
            resolved = Path(candidate).resolve(strict=True)
            resolved.relative_to(root)
        except (FileNotFoundError, ValueError):
            continue
        if resolved.is_file():
            matches.add(resolved)
    return sorted(matches, key=lambda path: path.as_posix())


def _bundle_names(sources: list[Path]) -> dict[Path, str]:
    initial_names = {source: _sanitize_basename(source.name) for source in sources}
    collisions: dict[str, list[Path]] = {}
    for source, name in initial_names.items():
        collisions.setdefault(name.casefold(), []).append(source)

    names: dict[Path, str] = {}
    for source, name in initial_names.items():
        if len(collisions[name.casefold()]) == 1:
            names[source] = name
            continue
        stem, suffix = _split_basename(name)
        names[source] = f"{stem}-{_sha256(source)[:8]}{suffix}"

    if len(set(names.values())) != len(names):
        raise SourceValidationError("asset bundle collision after digest disambiguation")
    return names


def _sanitize_basename(name: str) -> str:
    stem, suffix = _split_basename(name)
    safe_stem = _UNSAFE_BASENAME.sub("-", stem).strip(".-")
    safe_suffix = _UNSAFE_BASENAME.sub("", suffix)
    if not safe_stem or safe_suffix.casefold() not in _SUPPORTED_EXTENSIONS:
        raise SourceValidationError(f"unsafe asset basename: {name}")
    return f"{safe_stem}{safe_suffix.casefold()}"


def _split_basename(name: str) -> tuple[str, str]:
    suffix = Path(name).suffix
    return name[: -len(suffix)] if suffix else name, suffix


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as asset:
        for chunk in iter(lambda: asset.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _asset_error(document: SourceDocument, explanation: str) -> SourceValidationError:
    return SourceValidationError(f"{document.source_path.as_posix()}: {explanation}")
