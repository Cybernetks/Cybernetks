# Site development

The Cybernetks website is built with Hugo and published through GitHub Pages.

## Run locally

Use Python 3.12 and Hugo Extended 0.164.0. Create an isolated Python environment
and install the pinned dependencies:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

From the repository root, the site commands are:

```bash
make test
make build
make preview
make publish
```

See [Publishing from Obsidian](editorial-publishing.md) for source metadata,
public article boundaries, and migration guidance. Day-to-day release instructions
are in [Publishing](operations/publishing.md); use the human-only
[GitHub Pages cutover checklist](operations/cutover.md) when moving the live
domain from Ghost.
