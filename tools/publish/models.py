from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any


class ContentKind(StrEnum):
    LOG = "log"
    SNAPSHOT = "snapshot"
    PROJECT = "project"
    PAGE = "page"


class SourceValidationError(ValueError):
    """Raised when a source note cannot enter the public publishing pipeline."""


@dataclass(frozen=True)
class SourceDocument:
    source_path: Path
    kind: ContentKind
    title: str
    publication_status: str
    publish_date: date
    summary: str
    url_path: str
    params: dict[str, Any] = field(default_factory=dict)
    body: str = ""
