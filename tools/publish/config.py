"""The explicit set of Obsidian notes eligible for public publication."""

from dataclasses import dataclass

from tools.publish.models import ContentKind


@dataclass(frozen=True)
class PublisherConfig:
    """Allowlisted source locations relative to an Obsidian vault root."""

    directories: tuple[tuple[str, ContentKind], ...] = (
        ("3. Businesses/Cybernetks/Logs", ContentKind.LOG),
        ("3. Businesses/Cybernetks/Posts", ContentKind.LOG),
        ("3. Businesses/Cybernetks/Monthly Snapshots", ContentKind.SNAPSHOT),
    )
    files: tuple[tuple[str, ContentKind], ...] = (
        ("3. Businesses/Cybernetks/Pages/About Cybernetks.md", ContentKind.PAGE),
        ("3. Businesses/Cybernetks/Pages/Support.md", ContentKind.PAGE),
        ("3. Businesses/Cybernetks/Pages/Uses.md", ContentKind.PAGE),
        (
            "3. Businesses/Cybernetks/Projects/Operator/Operator.md",
            ContentKind.PROJECT,
        ),
        (
            "3. Businesses/Cybernetks/Projects/Operator/Privacy.md",
            ContentKind.PAGE,
        ),
        (
            "3. Businesses/Cybernetks/Projects/Operator/Support.md",
            ContentKind.PAGE,
        ),
        (
            "3. Businesses/Cybernetks/Projects/Cybernetks Planner/Cybernetks Planner.md",
            ContentKind.PROJECT,
        ),
        (
            "3. Businesses/Cybernetks/Projects/Alien Miner/Alien Miner.md",
            ContentKind.PROJECT,
        ),
    )
    optional_files: tuple[tuple[str, ContentKind], ...] = ()
