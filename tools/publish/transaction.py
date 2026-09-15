"""Build, validate, and atomically publish one generated Hugo content tree."""

from dataclasses import dataclass, replace
from pathlib import Path
import shutil
from typing import Mapping

import yaml

from tools.publish.assets import AssetCopy, collect_assets, rewrite_embeds
from tools.publish.body import extract_public_body, extract_snapshot_structure
from tools.publish.discovery import discover_sources
from tools.publish.frontmatter import _DuplicateKeyError, load_unique_yaml, parse_source
from tools.publish.links import build_public_index, rewrite_links
from tools.publish.models import ContentKind, SourceDocument, SourceValidationError
from tools.publish.render import (
    SectionDocument,
    apply_migration_aliases,
    render_bundle,
    render_section,
)
from tools.publish.validate import validate_documents, validate_staged_content


class PublishFailed(RuntimeError):
    """Raised when publishing fails while the previous content tree remains active."""


@dataclass(frozen=True)
class PublishReport:
    counts: Mapping[str, int]
    assets: int


def publish(vault_root: Path, repository_root: Path) -> PublishReport:
    """Publish a validated vault into ``generated/content`` as one directory swap."""
    vault, repository = _validated_roots(vault_root, repository_root)
    stage_root = repository / ".publish-stage"
    backup_root = repository / ".publish-backup"
    if stage_root.exists() or backup_root.exists():
        raise PublishFailed("publisher workspace is not clean")

    try:
        documents, assets_for_document = _prepared_documents(vault)
        validate_documents(documents)
        sections = _sections()
        apply_migration_aliases(documents, sections, _migration_entries(repository))

        stage_content = stage_root / "content"
        stage_content.mkdir(parents=True)
        asset_count = _render_tree(documents, sections, assets_for_document, stage_content)
        validate_staged_content(stage_content)
        _swap_content(stage_content, repository, backup_root)
        _remove_tree(stage_root)
        return PublishReport(counts=_counts(documents), assets=asset_count)
    except PublishFailed:
        _remove_tree(stage_root)
        raise
    except (OSError, SourceValidationError, yaml.YAMLError, ValueError) as error:
        _remove_tree(stage_root)
        raise PublishFailed(str(error)) from None


def _validated_roots(vault_root: Path, repository_root: Path) -> tuple[Path, Path]:
    vault = Path(vault_root).resolve()
    repository = Path(repository_root).resolve()
    if not vault.is_dir():
        raise PublishFailed(f"vault directory is missing: {vault}")
    if not repository.is_dir():
        raise PublishFailed(f"repository directory is missing: {repository}")
    if vault == repository:
        raise PublishFailed("vault and repository must be different directories")
    generated = repository / "generated"
    target = generated / "content"
    if generated.is_symlink() or target.is_symlink():
        raise PublishFailed("generated content target must not be a symbolic link")
    try:
        target.resolve().relative_to(repository)
    except ValueError:
        raise PublishFailed("generated content target resolves outside the repository") from None
    return vault, repository


def _prepared_documents(vault: Path) -> tuple[list[SourceDocument], dict[Path, list[AssetCopy]]]:
    documents = [
        parse_source(discovered.source_path, discovered.kind)
        for discovered in discover_sources(vault)
    ]
    extracted = [_extract_document(document) for document in documents]
    public_index = build_public_index(extracted, vault)
    linked = [replace(document, body=rewrite_links(document, public_index)) for document in extracted]
    assets_for_document = {
        document.source_path: collect_assets(document, vault) for document in linked
    }
    return (
        [replace(document, body=rewrite_embeds(document, vault)) for document in linked],
        assets_for_document,
    )


def _extract_document(document: SourceDocument) -> SourceDocument:
    extracted = replace(
        document,
        body=extract_public_body(document.body, document.kind, document.source_path),
    )
    if extracted.kind != ContentKind.SNAPSHOT:
        return extracted
    structure = extract_snapshot_structure(extracted.body)
    if structure is None:
        return extracted
    return replace(
        extracted,
        params={
            **extracted.params,
            "one_sentence": structure.one_sentence,
            "sections": [
                {"number": section.number, "title": section.title, "body": section.body}
                for section in structure.sections
            ],
        },
    )


def _sections() -> list[SectionDocument]:
    return [
        SectionDocument(title="Cybernetks", url_path="/"),
        SectionDocument(title="Logs", url_path="/logs/"),
        SectionDocument(title="Monthly Snapshots", url_path="/snapshots/"),
        SectionDocument(title="Projects", url_path="/projects/"),
    ]


def _migration_entries(repository: Path) -> list[Mapping[str, object]]:
    manifest = repository / "data/migration/ghost.yaml"
    if not manifest.is_file():
        return []
    try:
        loaded = load_unique_yaml(manifest.read_text(encoding="utf-8"))
    except _DuplicateKeyError as error:
        raise SourceValidationError(f"migration: {error.key}: must not be duplicated") from None
    except yaml.YAMLError as error:
        raise SourceValidationError(f"migration: invalid manifest: {manifest}") from error
    if loaded is None:
        return []
    if not isinstance(loaded, list) or not all(isinstance(entry, dict) for entry in loaded):
        raise SourceValidationError("migration: manifest must be a list of entries")
    return loaded


def _render_tree(
    documents: list[SourceDocument],
    sections: list[SectionDocument],
    assets_for_document: Mapping[Path, list[AssetCopy]],
    destination: Path,
) -> int:
    for section in sections:
        render_section(section, destination)
    asset_count = 0
    for document in documents:
        written = render_bundle(document, destination)
        for asset in assets_for_document[document.source_path]:
            shutil.copy2(asset.source, written.parent / asset.bundle_name)
            asset_count += 1
    return asset_count


def _swap_content(stage_content: Path, repository: Path, backup_root: Path) -> None:
    target = repository / "generated/content"
    target.parent.mkdir(parents=True, exist_ok=True)
    backup_content = backup_root / "content"
    had_target = target.exists()
    if had_target:
        backup_root.mkdir()
    try:
        if had_target:
            target.rename(backup_content)
        stage_content.rename(target)
    except OSError as error:
        if had_target and backup_content.exists() and not target.exists():
            try:
                backup_content.rename(target)
            except OSError as restore_error:
                raise PublishFailed(
                    f"failed to replace generated content and restore the backup: {restore_error}"
                ) from error
        _remove_tree(backup_root)
        raise PublishFailed(f"failed to replace generated content: {error}") from error
    _remove_tree(backup_root)


def _remove_tree(path: Path) -> None:
    if path.exists() and not path.is_symlink():
        shutil.rmtree(path)


def _counts(documents: list[SourceDocument]) -> dict[str, int]:
    return {kind.value: sum(document.kind == kind for document in documents) for kind in ContentKind}
