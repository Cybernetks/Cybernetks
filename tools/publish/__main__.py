"""Explicit command-line entry point for local Hugo content publication."""

import argparse
from pathlib import Path
import sys
from typing import Sequence

from tools.publish.transaction import PublishFailed, publish


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish validated Obsidian notes for Hugo")
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    arguments = parser.parse_args(argv)
    try:
        report = publish(arguments.vault, arguments.repository)
    except PublishFailed as error:
        print(error, file=sys.stderr)
        return 2
    counts = ", ".join(f"{kind}={count}" for kind, count in report.counts.items())
    print(f"Published: {counts}; assets={report.assets}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
