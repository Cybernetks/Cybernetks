# Cybernetks Hugo Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy the approved Cybernetks Hugo website, with Obsidian-driven publishing, complete Ghost URL migration, project pages, Logs, and Monthly Snapshots.

**Architecture:** Hugo 0.164.0 Extended renders a custom, theme-free static site. A small Python 3.12 publishing package reads only allowlisted Cybernetks notes, validates and transforms them into one staged `generated/content/` page-bundle tree, then atomically replaces the last valid generated tree. GitHub Actions runs the same tests and Hugo build before deploying the main branch to GitHub Pages.

**Tech Stack:** Hugo Extended 0.164.0, Go templates using Hugo's post-0.146 layout structure, HTML5, plain CSS, Python 3.12, PyYAML 6.0.2, Python `unittest`, GitHub Actions, GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-09-15-cybernetks-hugo-site-design.md`

## Global Constraints

- The canonical production origin is exactly `https://cybernetks.be/`; `www.cybernetks.be` redirects to it.
- Obsidian is the only editorial source; never edit files under `generated/content/` by hand.
- Only allowlisted notes with `publication_status: published` may be exported.
- Project lifecycle uses the separate `status` field.
- Existing published Ghost post paths remain unchanged even when titles lose their numbers.
- Old regular posts and numbered Logs both render as unnumbered Logs.
- Publication to the repository is explicit and local; the publisher never edits the vault, commits, pushes, or deploys.
- Keep the Ghost JSON export outside Git because it may contain account and configuration data.
- Use the official Cybernetks head symbol and unchanged wordmark geometry. Preserve the original black wordmark and derive the gold display copy with fill `#C4A76A`.
- Use only the approved website palette: `#20202D`, `#282C35`, `#30343B`, `#C4A76A`, and `#FFFFFF`, including transparent variants of those colours.
- Do not ship newsletter, membership, sign-in, comments, search, public tag pages, or analytics functionality.
- Do not invent project screenshots, logos, testimonials, traction, or release claims.
- Use genuine project media only; omit or reserve the media area when none exists.
- A failed export or build must leave the last valid `generated/content/` tree intact.
- Use the current Hugo layout structure: `layouts/baseof.html`, `layouts/_partials/`, `layouts/_markup/`, and content-path directories such as `layouts/logs/`.

## File and Responsibility Map

```text
.github/workflows/pages.yaml                 Test, build, and GitHub Pages deployment
.gitignore                                   Generated build caches and local publisher state
.python-version                              Local Python floor
Makefile                                     Human-facing test, build, preview, and publish commands
README.md                                    Setup, publishing, preview, and deployment instructions
hugo.toml                                    Canonical origin, outputs, security, and content mount
requirements.txt                             Pinned publisher dependency

assets/css/main.css                          Complete Cybernetks responsive design system
assets/css/syntax.css                        Code-block colours generated for the fixed dark theme
static/brand/logo.svg                        Official head symbol, unchanged
static/brand/wordmark.svg                    Official black wordmark, unchanged
static/brand/wordmark-gold.svg               Approved web-display colour variant
static/images/og-default.png                 Default 1200×630 Cybernetks social preview
static/CNAME                                 Canonical GitHub Pages domain

layouts/baseof.html                          Shared document shell and landmarks
layouts/home.html                            Approved homepage hierarchy
layouts/page.html                            Generic About, Uses, privacy, and support pages
layouts/section.html                         Generic fallback section
layouts/logs/page.html                       Reading-first Log page
layouts/logs/section.html                    Chronological Log archive
layouts/logs/_views/card.html                Reusable Log list item
layouts/snapshots/page.html                  Structured Monthly Snapshot page
layouts/snapshots/section.html               Snapshot archive grouped by year
layouts/snapshots/_views/card.html           Reusable Snapshot list item
layouts/projects/page.html                   Product profile page
layouts/projects/section.html                Project index
layouts/projects/_views/card.html             Reusable project card
layouts/_partials/head.html                  Canonical, SEO, Open Graph, RSS, and CSS tags
layouts/_partials/header.html                Cybernetks symbol, gold wordmark, and navigation
layouts/_partials/footer.html                Studio and external-channel footer
layouts/_partials/project-action.html        Lifecycle-to-action mapping
layouts/_partials/publication-meta.html      Shared date, topics, projects, and media links
layouts/_markup/render-image.html            Responsive page-bundle images
layouts/_markup/render-link.html             Safe internal and external links

data/navigation.yaml                         Primary and footer navigation
data/migration/ghost.yaml                    Public legacy route manifest only
data/project-actions.yaml                    Supported lifecycle action contract

generated/content/                           Publisher-owned Markdown and page resources

scripts/publish-site                         Explicit local publication entry point
scripts/check-site                           Production build and HTML contract check
tools/publish/__init__.py                    Package marker
tools/publish/__main__.py                    CLI argument handling and exit codes
tools/publish/config.py                      Allowlist and repository configuration
tools/publish/frontmatter.py                 YAML front-matter parsing and serialization
tools/publish/models.py                      Validated source and output models
tools/publish/discovery.py                   Allowlisted note discovery and kind selection
tools/publish/body.py                        Public-body and summary extraction
tools/publish/links.py                       Wiki-link resolution and Markdown rewriting
tools/publish/assets.py                      Embed lookup and page-resource copying
tools/publish/render.py                      Hugo bundle paths and generated Markdown
tools/publish/transaction.py                 Stage, validate, swap, and rollback
tools/publish/validate.py                    Cross-document and generated-tree checks
tools/migration/ghost_manifest.py            One-time public-route extraction from Ghost JSON

tests/fixtures/vault/                        Safe miniature Obsidian vault
tests/fixtures/site-content/                 Template-focused Hugo content
tests/publish/                               Publisher unit and integration tests
tests/site/build.py                          Temporary Hugo build helper
tests/site/html_contract.py                  Standard-library HTML assertions
tests/site/test_site_contract.py             Rendered page and metadata contract
tests/site/test_legacy_routes.py             Ghost path coverage
```

---

### Task 1: Establish the Reproducible Hugo and Python Foundation

**Files:**
- Create: `.gitignore`
- Create: `.python-version`
- Create: `requirements.txt`
- Create: `Makefile`
- Create: `hugo.toml`
- Create: `generated/content/_index.md`
- Create: `layouts/baseof.html`
- Create: `layouts/home.html`
- Create: `tests/site/build.py`
- Create: `tests/site/test_site_contract.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: Hugo Extended 0.164.0 and Python 3.12 available on `PATH`.
- Produces: `build_site(content_dir: Path | None = None) -> Path`, `make test`, `make build`, and `make preview` for every later task.

- [ ] **Step 1: Record tool versions and refuse incompatible Hugo releases**

Add the exact project floor to `.python-version`:

```text
3.12
```

Add the Hugo version to `hugo.toml` and the canonical host:

```toml
baseURL = 'https://cybernetks.be/'
languageCode = 'en'
defaultContentLanguage = 'en'
title = 'Cybernetks'
enableRobotsTXT = true
disableKinds = ['taxonomy', 'term']
contentDir = 'generated/content'

[build]
  noJSConfigInAssets = true

[caches]
  [caches.images]
    dir = ':cacheDir/images'

[security]
  [security.funcs]
    getenv = ['^HUGO_']
```

Create `generated/content/_index.md` with only `title: Cybernetks` front matter so the initial Hugo build has a home content object. Task 5 makes this file publisher-owned with the rest of the generated tree.

- [ ] **Step 2: Write the failing Hugo smoke test**

```python
# tests/site/test_site_contract.py
from pathlib import Path
import unittest

from tests.site.build import build_site


class HugoSmokeTest(unittest.TestCase):
    def test_homepage_builds_with_canonical_origin(self) -> None:
        public = build_site()
        html = (public / "index.html").read_text(encoding="utf-8")
        self.assertIn('<link rel="canonical" href="https://cybernetks.be/">', html)
```

Implement the helper signature without hiding subprocess output:

```python
# tests/site/build.py
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_CONTENT = ROOT / "tests/fixtures/site-content"


def build_site(content_dir: Path | None = None) -> Path:
    destination = Path(tempfile.mkdtemp(prefix="cybernetks-hugo-"))
    command = ["hugo", "--source", str(ROOT), "--destination", str(destination)]
    if content_dir is not None:
        command.extend(["--contentDir", str(content_dir)])
    subprocess.run(command, check=True, cwd=ROOT)
    return destination


def built_html(relative_path: str, content_dir: Path = FIXTURE_CONTENT) -> str:
    return (build_site(content_dir) / relative_path).read_text(encoding="utf-8")
```

- [ ] **Step 3: Run the smoke test and verify it fails**

Run: `python3 -m unittest tests.site.test_site_contract.HugoSmokeTest.test_homepage_builds_with_canonical_origin -v`

Expected: FAIL because the base and home templates do not yet render the canonical link.

- [ ] **Step 4: Add the minimal document shell and home template**

```html
<!-- layouts/baseof.html -->
<!doctype html>
<html lang="{{ site.Language.LanguageCode }}">
  <head>{{ partial "head.html" . }}</head>
  <body>
    {{ partial "header.html" . }}
    <main id="main">{{ block "main" . }}{{ end }}</main>
    {{ partial "footer.html" . }}
  </body>
</html>
```

```html
<!-- layouts/home.html -->
{{ define "main" }}
  <h1>Cybernetks</h1>
{{ end }}
```

Create minimal `layouts/_partials/head.html`, `header.html`, and `footer.html` so the shell builds; Task 6 replaces their temporary markup with the approved components.

- [ ] **Step 5: Add repeatable commands and ignore build products**

```make
PYTHON ?= python3

.PHONY: test build preview publish
test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

build:
	hugo --gc --minify --cleanDestinationDir

preview:
	hugo server --disableFastRender

publish:
	./scripts/publish-site
```

Set `requirements.txt` to `PyYAML==6.0.2`. Ignore `public/`, `resources/`, `.hugo_build.lock`, `.publish-stage/`, `.publish-backup/`, `.venv/`, and Python cache files. Do not ignore `generated/content/`.

- [ ] **Step 6: Run the smoke test and full foundation checks**

Run: `hugo version`

Expected: output starts with `hugo v0.164.0` and contains `+extended`.

Run: `python3 -m unittest tests.site.test_site_contract -v`

Expected: PASS.

Run: `hugo --gc --minify --cleanDestinationDir`

Expected: exit 0 and `public/index.html` exists.

- [ ] **Step 7: Document local setup and commit**

Document Python 3.12, `python3 -m venv .venv`, `pip install -r requirements.txt`, Hugo 0.164.0 Extended, and the four `make` commands in `README.md`.

```bash
git add .gitignore .python-version requirements.txt Makefile hugo.toml layouts tests README.md
git commit -m "build: establish Hugo site foundation"
```

### Task 2: Define and Validate the Publication Contract

**Files:**
- Create: `tools/publish/__init__.py`
- Create: `tools/publish/models.py`
- Create: `tools/publish/frontmatter.py`
- Create: `tests/publish/test_frontmatter.py`
- Create: `tests/fixtures/vault/3. Businesses/Cybernetks/Logs/Published Log.md`
- Modify: `requirements.txt`
- Create: `tests/fixtures/vault/project.md`

**Interfaces:**
- Consumes: a UTF-8 Markdown path containing YAML front matter.
- Produces: `parse_source(path: Path, kind: ContentKind) -> SourceDocument`, `normalize_public_path(value: str) -> str`, and `SourceValidationError`.

- [ ] **Step 1: Write failing tests for host normalization and project status separation**

```python
# tests/publish/test_frontmatter.py
from pathlib import Path
import unittest

from tools.publish.frontmatter import normalize_public_path, parse_source
from tools.publish.models import ContentKind, SourceValidationError


class FrontMatterTest(unittest.TestCase):
    def test_normalizes_existing_www_url_to_path(self) -> None:
        self.assertEqual(
            normalize_public_path("https://www.cybernetks.be/005-scope/"),
            "/005-scope/",
        )

    def test_rejects_an_unrelated_host(self) -> None:
        with self.assertRaises(SourceValidationError):
            normalize_public_path("https://example.com/post/")

    def test_project_has_separate_publication_and_lifecycle_status(self) -> None:
        document = parse_source(
            Path("tests/fixtures/vault/project.md"), ContentKind.PROJECT
        )
        self.assertEqual(document.publication_status, "published")
        self.assertEqual(document.params["status"], "launching")
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `python3 -m unittest tests.publish.test_frontmatter -v`

Expected: FAIL with missing `tools.publish.frontmatter` and `tools.publish.models`.

- [ ] **Step 3: Implement focused types and deterministic validation**

```python
# tools/publish/models.py
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
    pass


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
```

`parse_source` must require `title`, `publication_status`, `publish_date`, `summary`, and `url` for published documents. It must require `review_month` for Snapshots and `status`, `promise`, and `project_kind` for Projects. Errors use the exact format `relative/path.md: field_name: explanation`.

`normalize_public_path` accepts `/path/`, `https://cybernetks.be/path/`, and `https://www.cybernetks.be/path/`; it rejects query strings, fragments, other hosts, missing leading slashes, and paths without a trailing slash.

- [ ] **Step 4: Add PyYAML and representative fixtures**

Pin:

```text
PyYAML==6.0.2
```

Create published Log, Snapshot, Project, draft, malformed, and duplicate-path fixtures. The Project fixture contains both:

```yaml
publication_status: published
status: launching
```

- [ ] **Step 5: Run validation tests**

Run: `python3 -m unittest tests.publish.test_frontmatter -v`

Expected: PASS for valid documents and exact validation errors for each malformed fixture.

- [ ] **Step 6: Commit the publication contract**

```bash
git add requirements.txt tools/publish tests/publish tests/fixtures/vault
git commit -m "feat: define Obsidian publication contract"
```

### Task 3: Discover Allowlisted Notes and Extract Only Public Bodies

**Files:**
- Create: `tools/publish/config.py`
- Create: `tools/publish/discovery.py`
- Create: `tools/publish/body.py`
- Create: `tests/publish/test_discovery.py`
- Create: `tests/publish/test_body.py`
- Modify: `tests/fixtures/vault/`

**Interfaces:**
- Consumes: `vault_root: Path` and the fixed allowlist in `PublisherConfig`.
- Produces: `discover_sources(vault_root: Path) -> list[DiscoveredSource]`, `extract_public_body(markdown: str) -> str`, and `extract_snapshot_structure(body: str) -> SnapshotStructure | None`.

- [ ] **Step 1: Write failing allowlist tests**

```python
class DiscoveryTest(unittest.TestCase):
    def test_posts_and_logs_both_map_to_log(self) -> None:
        found = discover_sources(FIXTURE_VAULT)
        kinds = {item.relative_path.as_posix(): item.kind for item in found}
        self.assertEqual(kinds["3. Businesses/Cybernetks/Posts/Old Post.md"], ContentKind.LOG)
        self.assertEqual(kinds["3. Businesses/Cybernetks/Logs/New Log.md"], ContentKind.LOG)

    def test_unrelated_daily_note_is_never_discovered(self) -> None:
        found = discover_sources(FIXTURE_VAULT)
        self.assertNotIn("1. Daily/private.md", {str(item.relative_path) for item in found})
```

The allowlist is exactly the Cybernetks `Logs`, `Posts`, and `Monthly Snapshots` directories plus individually named public project/page notes. Do not recursively allow all of `3. Businesses/Cybernetks/Projects/`, because it contains private roadmaps, pricing work, and client notes.

- [ ] **Step 2: Write failing body-extraction tests**

```python
class BodyExtractionTest(unittest.TestCase):
    def test_new_log_uses_blog_post_section_only(self) -> None:
        markdown = "# Title\n# Blog post\nPublic body\n# Podcast description\nPrivate package"
        self.assertEqual(extract_public_body(markdown), "Public body")

    def test_legacy_post_uses_everything_after_published_content(self) -> None:
        markdown = "# Title\n## Summary\nTeaser\n## Published Content\nIntro\n## Next up\nBody"
        self.assertEqual(extract_public_body(markdown), "Intro\n## Next up\nBody")

    def test_snapshot_without_marker_uses_body_after_first_title(self) -> None:
        markdown = "# Monthly Snapshot\nIntro\n## The month in one sentence\nMoved forward."
        self.assertEqual(
            extract_public_body(markdown),
            "Intro\n## The month in one sentence\nMoved forward.",
        )

    def test_project_uses_explicit_website_content_section(self) -> None:
        markdown = "# Operator\n## Internal roadmap\nPrivate\n## Website Content\nPublic"
        self.assertEqual(extract_public_body(markdown), "Public")

    def test_structured_snapshot_assigns_one_sentence_to_section_zero(self) -> None:
        body = "## The month in one sentence\nMoved forward.\n## What comes next\nShip."
        structure = extract_snapshot_structure(body)
        self.assertEqual(structure.one_sentence, "Moved forward.")
        self.assertEqual(structure.sections[0].number, "01")
        self.assertEqual(structure.sections[0].title, "What comes next")
```

- [ ] **Step 3: Run the tests and verify both modules are missing**

Run: `python3 -m unittest tests.publish.test_discovery tests.publish.test_body -v`

Expected: FAIL with missing discovery and body functions.

- [ ] **Step 4: Implement explicit discovery configuration**

```python
@dataclass(frozen=True)
class PublisherConfig:
    directories: tuple[tuple[str, ContentKind], ...] = (
        ("3. Businesses/Cybernetks/Logs", ContentKind.LOG),
        ("3. Businesses/Cybernetks/Posts", ContentKind.LOG),
        ("3. Businesses/Cybernetks/Monthly Snapshots", ContentKind.SNAPSHOT),
    )
    files: tuple[tuple[str, ContentKind], ...] = (
        ("3. Businesses/Cybernetks/Pages/About Cybernetks.md", ContentKind.PAGE),
        ("3. Businesses/Cybernetks/Pages/Uses.md", ContentKind.PAGE),
        ("3. Businesses/Cybernetks/Projects/Operator/Operator.md", ContentKind.PROJECT),
        ("3. Businesses/Cybernetks/Projects/Operator/Privacy.md", ContentKind.PAGE),
        ("3. Businesses/Cybernetks/Projects/Operator/Support.md", ContentKind.PAGE),
        ("3. Businesses/Cybernetks/Projects/Cybernetks Planner/Cybernetks Planner.md", ContentKind.PROJECT),
        ("3. Businesses/Cybernetks/Projects/Alien Miner/Alien Miner.md", ContentKind.PROJECT),
    )
```

Discovery sorts by relative POSIX path for deterministic output and ignores missing individually listed draft sources only when configured as optional. All seven launch page/project sources above are required before the production migration task completes.

- [ ] **Step 5: Implement the three body modes**

Use this precedence:

1. Content between `# Blog post` and the next level-one heading.
2. All content after `## Published Content`.
3. All content after `## Website Content` for public project and page notes.
4. All content after the document's first level-one title.

Reject a document when the extracted body is empty. Never export `Podcast description`, `YouTube description`, social copy, recommended titles, or raw transcripts from a packaged Log.

For Snapshots, parse level-two sections after body extraction. Return a structured model when `The month in one sentence` is present; number every subsequent section in source order. Return `None` for older freeform Snapshots so they keep their historical body without fabricated sections.

- [ ] **Step 6: Run all discovery and body tests**

Run: `python3 -m unittest tests.publish.test_discovery tests.publish.test_body -v`

Expected: PASS, including a fixture proving `Projects/Easyfairs/DevOps skills.md` is not discovered.

- [ ] **Step 7: Commit allowlisting and body extraction**

```bash
git add tools/publish tests/publish tests/fixtures/vault
git commit -m "feat: discover safe Cybernetks publication sources"
```

### Task 4: Resolve Wiki Links and Copy Page-Bundle Assets

**Files:**
- Create: `tools/publish/links.py`
- Create: `tools/publish/assets.py`
- Create: `tests/publish/test_links.py`
- Create: `tests/publish/test_assets.py`
- Modify: `tests/fixtures/vault/`

**Interfaces:**
- Consumes: validated documents indexed by Obsidian note name and normalized public path.
- Produces: `rewrite_links(document, index) -> str`, `collect_assets(document, vault_root) -> list[AssetCopy]`, and `AssetCopy(source: Path, bundle_name: str)`.

- [ ] **Step 1: Write failing wiki-link tests**

```python
def test_public_wiki_link_becomes_canonical_path(self) -> None:
    body = "Read [[Operator]] and [[Operator|the product]]."
    rewritten = rewrite_links(replace(LOG_DOCUMENT, body=body), PUBLIC_INDEX)
    self.assertEqual(
        rewritten,
        "Read [Operator](/projects/operator/) and [the product](/projects/operator/).",
    )

def test_private_wiki_link_fails_with_source_location(self) -> None:
    with self.assertRaisesRegex(SourceValidationError, "Log.md: unresolved public link: Pricing Strategy - Operator"):
        rewrite_links(replace(LOG_DOCUMENT, body="[[Pricing Strategy - Operator]]"), PUBLIC_INDEX)
```

- [ ] **Step 2: Write failing embed tests**

```python
def test_embed_is_copied_into_owning_page_bundle(self) -> None:
    copies = collect_assets(LOG_WITH_IMAGE, FIXTURE_VAULT)
    self.assertEqual(copies[0].bundle_name, "operator-screen.png")

def test_missing_embed_is_an_error(self) -> None:
    with self.assertRaisesRegex(SourceValidationError, "missing asset"):
        collect_assets(LOG_WITH_MISSING_IMAGE, FIXTURE_VAULT)
```

- [ ] **Step 3: Run focused tests and verify failure**

Run: `python3 -m unittest tests.publish.test_links tests.publish.test_assets -v`

Expected: FAIL because the resolver and asset collector do not exist.

- [ ] **Step 4: Implement deterministic wiki-link resolution**

Support `[[Note]]`, `[[Note|Label]]`, and heading fragments on public notes. Index both relative path and unambiguous basename. Reject ambiguous basenames instead of guessing. Preserve ordinary Markdown links unchanged.

Transform public heading links to a normalized anchor:

```python
def heading_anchor(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
```

- [ ] **Step 5: Implement embeds as page resources**

Support `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.svg`, `.mp3`, and `.m4a`. Resolve Obsidian's `![[asset.ext]]` against the vault, reject ambiguity, sanitize the copied basename, and rewrite image embeds to `![alt](asset.ext)`. Reject unsupported executable or document types.

When two different sources sanitize to the same basename, append the first eight characters of the source SHA-256 digest before the extension.

- [ ] **Step 6: Run link and asset tests**

Run: `python3 -m unittest tests.publish.test_links tests.publish.test_assets -v`

Expected: PASS for public links, aliases, fragments, collisions, missing assets, and private notes.

- [ ] **Step 7: Commit link and asset handling**

```bash
git add tools/publish tests/publish tests/fixtures/vault
git commit -m "feat: resolve Obsidian links and page resources"
```

### Task 5: Render Hugo Bundles and Replace Them Transactionally

**Files:**
- Create: `tools/publish/render.py`
- Create: `tools/publish/validate.py`
- Create: `tools/publish/transaction.py`
- Create: `tools/publish/__main__.py`
- Create: `scripts/publish-site`
- Create: `tests/publish/test_render.py`
- Create: `tests/publish/test_transaction.py`
- Create: `tests/publish/test_cli.py`

**Interfaces:**
- Consumes: `list[SourceDocument]`, resolved Markdown, and page resources.
- Produces: `bundle_path(document: SourceDocument) -> Path`, `serialize_document(document: SourceDocument) -> str`, `apply_migration_aliases(documents, section_documents, entries) -> None`, `render_bundle(document, destination) -> Path`, `publish(vault_root: Path, repository_root: Path) -> PublishReport`, and CLI exit code 0 or 2.

- [ ] **Step 1: Write the failing bundle-path and title-normalization tests**

```python
def test_numbered_log_keeps_url_but_drops_display_number(self) -> None:
    rendered = serialize_document(NUMBERED_LOG)
    self.assertIn('title: Who Stops Scope Creep When You Work Alone?', rendered)
    self.assertIn('url: /005-who-stops-scope-creep-when-you-work-alone/', rendered)
    self.assertNotIn('#005 -', rendered)

def test_snapshot_is_written_below_snapshot_section(self) -> None:
    path = bundle_path(SNAPSHOT)
    self.assertEqual(path.as_posix(), "snapshots/2026-08/index.md")
```

- [ ] **Step 2: Write the failing transaction rollback test**

```python
def test_failed_validation_keeps_previous_generated_tree(self) -> None:
    existing = repository / "generated/content/logs/old/index.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("old valid content", encoding="utf-8")
    with self.assertRaises(PublishFailed):
        publish(BROKEN_VAULT, repository)
    self.assertEqual(existing.read_text(encoding="utf-8"), "old valid content")
```

- [ ] **Step 3: Run render and transaction tests and verify failure**

Run: `python3 -m unittest tests.publish.test_render tests.publish.test_transaction tests.publish.test_cli -v`

Expected: FAIL with missing render, transaction, and CLI modules.

- [ ] **Step 4: Implement Hugo bundle rendering**

Render YAML front matter with stable key order followed by transformed Markdown. Bundle locations are:

```text
logs/<source-stem>/index.md
snapshots/<review-month>/index.md
projects/<project-slug>/index.md
projects/<project-slug>/privacy/index.md
projects/<project-slug>/support/index.md
about/index.md
uses/index.md
```

The output front matter includes `title`, `date`, `description`, `url`, `kind`, `topics`, `projects`, `aliases`, and the type-specific parameters used by templates.

The renderer also creates publisher-owned `_index.md` files for the home, Logs, Snapshots, and Projects sections. These carry the section titles and any migration aliases assigned to section routes.

When `data/migration/ghost.yaml` exists, load its public entries before rendering. For every non-identity replacement, find the document or section whose `url` equals `replacement` and add `path` to that target's Hugo `aliases`. Fail before staging if the replacement target is missing or two targets claim the same legacy path.

- [ ] **Step 5: Implement the single-directory transaction**

Build `.publish-stage/content`, validate it, rename `generated/content` to `.publish-backup/content`, rename the staged directory to `generated/content`, and remove the backup only after the new tree is in place. On any rename failure, restore the backup and return exit code 2.

Refuse to operate when the target resolves outside `<repository>/generated/content` or when the vault and repository roots resolve to the same directory.

- [ ] **Step 6: Implement the explicit CLI and wrapper**

```bash
#!/usr/bin/env bash
set -euo pipefail
: "${CYBERNETKS_VAULT:?Set CYBERNETKS_VAULT to the Obsidian vault root}"
python3 -m tools.publish --vault "$CYBERNETKS_VAULT" --repository "$(pwd)"
hugo --gc --minify --cleanDestinationDir
```

The Python CLI supports only `--vault` and `--repository`, prints counts by content kind plus copied assets on success, and prints validation errors to standard error without a traceback for expected content failures.

- [ ] **Step 7: Run integration tests and a fixture publish**

Run: `python3 -m unittest tests.publish.test_render tests.publish.test_transaction tests.publish.test_cli -v`

Expected: PASS.

Run: `CYBERNETKS_VAULT="$PWD/tests/fixtures/vault" ./scripts/publish-site`

Expected: exit 0, a summary count, a successful Hugo build, and no `.publish-stage` or `.publish-backup` left behind.

- [ ] **Step 8: Commit the publisher transaction**

```bash
git add tools/publish scripts/publish-site tests/publish generated/content
git commit -m "feat: publish validated Hugo bundles atomically"
```

### Task 6: Implement the Shared Cybernetks Visual System and Metadata

**Files:**
- Create: `assets/css/main.css`
- Create: `assets/css/syntax.css`
- Create: `static/brand/logo.svg`
- Create: `static/brand/wordmark.svg`
- Create: `static/brand/wordmark-gold.svg`
- Create: `static/images/og-default.png`
- Create: `layouts/_partials/head.html`
- Create: `layouts/_partials/header.html`
- Create: `layouts/_partials/footer.html`
- Create: `layouts/_partials/publication-meta.html`
- Create: `layouts/_markup/render-image.html`
- Create: `layouts/_markup/render-link.html`
- Create: `data/navigation.yaml`
- Modify: `layouts/baseof.html`
- Modify: `tests/site/test_site_contract.py`

**Interfaces:**
- Consumes: Hugo page context, `data/navigation.yaml`, and page front matter.
- Produces: a responsive shared shell, `main.css`, canonical/Open Graph/RSS metadata, and accessible asset rendering for every page.

- [ ] **Step 1: Write failing shell and metadata contract tests**

```python
def test_shell_contains_official_identity_and_primary_navigation(self) -> None:
    public = build_site(FIXTURE_CONTENT)
    html = (public / "index.html").read_text(encoding="utf-8")
    self.assertIn('/brand/logo.svg', html)
    self.assertIn('/brand/wordmark-gold.svg', html)
    for label in ("Projects", "Logs", "Monthly Snapshots", "About"):
        self.assertIn(label, html)

def test_page_has_canonical_and_open_graph_metadata(self) -> None:
    html = built_html("back-to-building/index.html")
    self.assertIn('property="og:title"', html)
    self.assertIn('property="og:image"', html)
    self.assertIn('rel="canonical"', html)
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python3 -m unittest tests.site.test_site_contract -v`

Expected: FAIL because the identity, navigation, and complete metadata are absent.

- [ ] **Step 3: Add official assets without changing geometry**

Copy the official symbol from `/Users/schabrechtsk/Documents/02 Business/Cybernetks/Logo/Logo.svg` to `static/brand/logo.svg` and the supplied wordmark to `static/brand/wordmark.svg`. Create `wordmark-gold.svg` by changing only the wordmark path fill from `#000000` to `#C4A76A`.

Verify that the symbol and original wordmark SHA-256 digests match their source files. Generate a 1200×630 PNG with the approved dark background, official symbol, and gold wordmark; do not add slogans or unapproved effects.

- [ ] **Step 4: Implement the header, footer, and metadata partials**

The header uses separate `<img>` elements for the symbol and gold wordmark, with meaningful identity text on one image only. Navigation data is:

```yaml
primary:
  - {label: Projects, url: /projects/}
  - {label: Logs, url: /logs/}
  - {label: Monthly Snapshots, url: /snapshots/}
  - {label: About, url: /about/}
footer:
  - {label: GitHub, url: https://github.com/Cybernetks}
  - {label: YouTube, url: https://www.youtube.com/@Cybernetks}
  - {label: Spotify, url: https://open.spotify.com/show/1yUXmMLARRlLCRrPnfio1r}
  - {label: Twitch, url: https://www.twitch.tv/cybernetks}
  - {label: Itch.io, url: https://cybernetks.itch.io}
```

`head.html` chooses `.Params.image` when present and otherwise `/images/og-default.png`. It emits the canonical URL from `.Permalink`, description from `.Description`, and alternate RSS for the home, Logs, and Snapshots outputs.

- [ ] **Step 5: Implement the responsive dark design tokens**

Define component-scoped CSS custom properties with the five approved colours, a system sans body stack, and JetBrains Mono with a local monospace fallback for metadata. Implement visible focus outlines, a skip link, fluid title sizes, a maximum reading measure of approximately 68 characters, and breakpoints at 760px and 430px.

Do not use a CSS framework, remote JavaScript, gradients, or animation loops.

- [ ] **Step 6: Add render hooks and run the shell tests**

Images use intrinsic width and height where Hugo can determine them, `loading="lazy"` below the fold, and page-resource processing for raster images. External links receive `rel="noopener noreferrer"`; internal links remain same-tab without decorative external-link icons.

Run: `python3 -m unittest tests.site.test_site_contract -v`

Expected: PASS for identity, navigation, canonical, Open Graph, focus target, and responsive-image assertions.

- [ ] **Step 7: Commit the shared visual system**

```bash
git add assets static layouts data/navigation.yaml tests/site
git commit -m "feat: add Cybernetks visual system and metadata"
```

### Task 7: Implement Logs and Monthly Snapshots

**Files:**
- Create: `layouts/logs/page.html`
- Create: `layouts/logs/section.html`
- Create: `layouts/logs/_views/card.html`
- Create: `layouts/snapshots/page.html`
- Create: `layouts/snapshots/section.html`
- Create: `layouts/snapshots/_views/card.html`
- Create: `tests/fixtures/site-content/logs/_index.md`
- Create: `tests/fixtures/site-content/logs/scope/index.md`
- Create: `tests/fixtures/site-content/snapshots/_index.md`
- Create: `tests/fixtures/site-content/snapshots/2026-08/index.md`
- Modify: `tests/site/test_site_contract.py`

**Interfaces:**
- Consumes: generated `kind: log` and `kind: snapshot` content contracts.
- Produces: reading-first Log pages, structured Snapshot pages, `/logs/`, and `/snapshots/`.

- [ ] **Step 1: Write failing template-selection tests**

```python
def test_log_is_reading_first_and_unnumbered(self) -> None:
    html = built_html("005-who-stops-scope-creep-when-you-work-alone/index.html")
    self.assertIn('data-template="log"', html)
    self.assertIn("Who Stops Scope Creep When You Work Alone?", html)
    self.assertNotIn("#005", html)

def test_snapshot_has_aligned_numbered_sections(self) -> None:
    html = built_html("monthly-snapshot-august-2026/index.html")
    self.assertIn('data-template="snapshot"', html)
    self.assertIn('data-snapshot-section="00"', html)
    self.assertIn('data-snapshot-section="01"', html)
    self.assertIn('class="snapshot-grid"', html)
```

- [ ] **Step 2: Run focused site tests and verify failure**

Run: `python3 -m unittest tests.site.test_site_contract.PublicationTemplateTest -v`

Expected: FAIL because the publication templates do not exist.

- [ ] **Step 3: Implement the Log template and archive**

`layouts/logs/page.html` renders type/topic metadata, title, summary, date, reading time, body, project/topic relations, optional YouTube/podcast adaptations, and next/previous Log navigation. It does not render a sequence number.

`layouts/logs/section.html` groups all Logs by year in reverse chronology and renders title, date, summary, and optional project association. Do not render tag filters or search controls.

- [ ] **Step 4: Implement the Snapshot template and archive**

Use one `.snapshot-grid` definition for the `00` statement and every later numbered section so their labels share the same left column. Render structured front-matter fields when present; otherwise render the authored Markdown body inside the same grid.

The archive groups Snapshots by year, orders months descending, and shows review month, title, and summary.

- [ ] **Step 5: Verify publication templates and archives**

Run: `python3 -m unittest tests.site.test_site_contract.PublicationTemplateTest -v`

Expected: PASS.

Run: `hugo --contentDir tests/fixtures/site-content --gc --minify --cleanDestinationDir`

Expected: exit 0; the built Log uses the legacy root path while the archive remains `/logs/`.

- [ ] **Step 6: Commit publication templates**

```bash
git add layouts/logs layouts/snapshots tests/fixtures/site-content tests/site
git commit -m "feat: add Log and Monthly Snapshot views"
```

### Task 8: Implement Project Pages, Homepage, and Supporting Pages

**Files:**
- Create: `data/project-actions.yaml`
- Create: `layouts/_partials/project-action.html`
- Create: `layouts/projects/page.html`
- Create: `layouts/projects/section.html`
- Create: `layouts/projects/_views/card.html`
- Create: `layouts/page.html`
- Modify: `layouts/home.html`
- Modify: `assets/css/main.css`
- Create: `tests/fixtures/site-content/projects/`
- Create: `tests/fixtures/site-content/about/index.md`
- Create: `tests/fixtures/site-content/uses/index.md`
- Modify: `tests/site/test_site_contract.py`

**Interfaces:**
- Consumes: project front matter including `status`, `project_kind`, `promise`, `icon`, `platforms`, `latest_update`, and optional destination URLs.
- Produces: lifecycle-aware project profiles, project index, approved homepage order, About, Uses, privacy, and support rendering.

- [ ] **Step 1: Write failing project-action tests**

```python
def test_launching_project_links_to_latest_update(self) -> None:
    html = built_html("projects/operator/index.html")
    self.assertIn('href="/005-who-stops-scope-creep-when-you-work-alone/"', html)
    self.assertIn("Read the latest update", html)

def test_released_native_project_uses_store_action(self) -> None:
    html = built_html("projects/released-app/index.html")
    self.assertIn("Download on the App Store", html)

def test_archived_project_has_no_primary_action(self) -> None:
    html = built_html("projects/archived-experiment/index.html")
    self.assertNotIn('class="project-primary-action"', html)
```

- [ ] **Step 2: Write failing homepage-order test**

```python
def test_homepage_places_projects_before_latest_publications(self) -> None:
    html = built_html("index.html")
    self.assertLess(html.index("Projects and experiments"), html.index("Latest from the studio"))
    for project in ("Operator", "Cybernetks Planner", "Alien Miner"):
        self.assertIn(project, html)
```

- [ ] **Step 3: Run project and homepage tests and verify failure**

Run: `python3 -m unittest tests.site.test_site_contract.ProjectTemplateTest tests.site.test_site_contract.HomepageTest -v`

Expected: FAIL because lifecycle actions and the approved homepage are absent.

- [ ] **Step 4: Implement lifecycle actions as data, not scattered conditionals**

```yaml
# data/project-actions.yaml
launching: {label: Read the latest update, field: latest_update}
beta: {label: Join the beta, field: beta_url}
released-native: {label: Download on the App Store, field: store_url}
released-web: {label: Open the app, field: app_url}
open-source: {label: View on GitHub, field: source_url}
released-experiment: {label: View the project, field: project_url}
archived: {label: '', field: ''}
```

The partial emits nothing when the mapped destination is absent. Unknown lifecycle values already fail publisher validation.

- [ ] **Step 5: Implement project profiles and project index**

Render the official project icon beside the title when supplied, genuine screenshot resources in the media area, product facts, why it exists, capabilities, current release state, next outcome, related publications, and privacy/support links. A missing screenshot collection removes the large media region rather than rendering a fake interface.

The project index shows all three initial projects with lifecycle, promise, icon when available, and a link to the internal project page.

- [ ] **Step 6: Implement the approved homepage hierarchy**

The home template renders, in order:

1. Hero with `A solo studio building thoughtful software in public.`
2. `Inside the studio`: featured Operator, latest Log, latest Snapshot
3. `Projects and experiments`: Operator, Cybernetks Planner, Alien Miner
4. `Latest from the studio`
5. Shared footer

The featured project and project cards use official icons only. Publication cards stay editorial.

- [ ] **Step 7: Implement generic pages and reciprocal project links**

`layouts/page.html` supports About, Uses, privacy, and support. Project-owned pages read `project: operator`, link back to `/projects/operator/`, and appear as secondary links on that project page.

- [ ] **Step 8: Run project, homepage, and page tests**

Run: `python3 -m unittest tests.site.test_site_contract.ProjectTemplateTest tests.site.test_site_contract.HomepageTest tests.site.test_site_contract.GenericPageTest -v`

Expected: PASS, including mobile-safe long titles and absence of invented media.

- [ ] **Step 9: Commit the complete page system**

```bash
git add data/project-actions.yaml layouts assets/css/main.css tests/fixtures/site-content tests/site
git commit -m "feat: add project profiles and approved homepage"
```

### Task 9: Reconcile Ghost Routes and Prepare the Obsidian Sources

**Files:**
- Create: `tools/migration/ghost_manifest.py`
- Create: `tests/publish/test_ghost_manifest.py`
- Create: `data/migration/ghost.yaml`
- Modify: `3. Businesses/Cybernetks/Logs/001 - From Planning to Building.md`
- Modify: `3. Businesses/Cybernetks/Logs/002 - Picking Up the Ball Again.md`
- Modify: `3. Businesses/Cybernetks/Logs/003 - A First Release.md`
- Modify: `3. Businesses/Cybernetks/Logs/004 - Why Is Sharing the Work So Much Harder Than Doing It?.md`
- Modify: `3. Businesses/Cybernetks/Logs/005 - Who Stops Scope Creep When You Work Alone?.md`
- Modify: every Markdown file directly within `3. Businesses/Cybernetks/Posts/` (20 legacy Logs)
- Modify: every Markdown file directly within `3. Businesses/Cybernetks/Monthly Snapshots/` (7 Snapshots)
- Create: `3. Businesses/Cybernetks/Pages/About Cybernetks.md`
- Create: `3. Businesses/Cybernetks/Pages/Uses.md`
- Modify: `3. Businesses/Cybernetks/Projects/Operator/Operator.md`
- Create: `3. Businesses/Cybernetks/Projects/Operator/Privacy.md`
- Create: `3. Businesses/Cybernetks/Projects/Operator/Support.md`
- Create: `3. Businesses/Cybernetks/Projects/Cybernetks Planner/Cybernetks Planner.md`
- Create: `3. Businesses/Cybernetks/Projects/Alien Miner/Alien Miner.md`

**Interfaces:**
- Consumes: private Ghost export `/Users/schabrechtsk/Downloads/cybernetks.ghost.2026-09-15-18-34-30.json` and the existing vault.
- Produces: a non-sensitive 40-route manifest and fully valid Obsidian publication sources. The Ghost JSON is never copied into the repository.

- [ ] **Step 1: Write the failing Ghost-manifest privacy test**

```python
def test_manifest_contains_only_public_route_fields(self) -> None:
    manifest = build_manifest(GHOST_FIXTURE)
    self.assertEqual(set(manifest[0]), {"path", "kind", "status", "replacement"})
    serialized = yaml.safe_dump(manifest)
    self.assertNotIn("email", serialized)
    self.assertNotIn("newsletter", serialized)
    self.assertNotIn("stripe", serialized)
```

- [ ] **Step 2: Run the test and verify failure**

Run: `python3 -m unittest tests.publish.test_ghost_manifest -v`

Expected: FAIL because `tools.migration.ghost_manifest` does not exist.

- [ ] **Step 3: Implement and run public-route extraction**

Read only `db[0].data.posts`; select `status == "published"`; derive `/<slug>/`; emit `kind` from Ghost's `type`; sort by path. Never serialize IDs, HTML, lexical JSON, authors, settings, members, newsletters, email addresses, or payment data.

Run:

```bash
python3 -m tools.migration.ghost_manifest \
  --input /Users/schabrechtsk/Downloads/cybernetks.ghost.2026-09-15-18-34-30.json \
  --output data/migration/ghost.yaml
```

Expected: 40 routes: 32 posts and 8 pages.

- [ ] **Step 4: Encode the eight Ghost page decisions**

Set exact replacements on the eight page entries in `data/migration/ghost.yaml`:

```yaml
- {path: /about/, kind: page, status: published, replacement: /about/}
- {path: /topics/, kind: page, status: published, replacement: /logs/}
- {path: /uses/, kind: page, status: published, replacement: /uses/}
- {path: /support/, kind: page, status: published, replacement: /projects/operator/support/}
- {path: /cybernetks-planner/, kind: page, status: published, replacement: /projects/cybernetks-planner/}
- {path: /projects/, kind: page, status: published, replacement: /projects/}
- {path: /operator-privacy/, kind: page, status: published, replacement: /projects/operator/privacy/}
- {path: /operator-support/, kind: page, status: published, replacement: /projects/operator/support/}
```

The two identity mappings mean the page remains at the same path. All 32 posts use identity mappings to their existing paths.

- [ ] **Step 5: Update the 32 existing publication notes**

For every existing Ghost post represented in the vault:

- add `publication_status: published`;
- add a concise `summary` based on the existing Summary section, Ghost custom excerpt, or opening paragraph;
- retain the existing `url` value;
- add `kind: log` or `kind: snapshot`;
- add `projects` only where the relationship is explicit;
- remove `#001 -` through `#005 -` from front-matter titles and visible document titles, without renaming the source files yet.

Run the publisher after the edits and require exactly 32 published publications before adding the new pages and projects.

- [ ] **Step 6: Create the seven required page and project sources**

Create About and Uses from the corresponding Ghost page content, then make Obsidian authoritative. Create Operator Privacy and Support from the Ghost page content at clean nested URLs. Expand the two existing project-type notes into Cybernetks Planner and Alien Miner project sources. Update Operator with public fields while retaining its private roadmap and pricing links outside the extracted public body.

All seven use `publication_status: published`. Operator uses `status: launching`, `latest_update: /monthly-snapshot-august-2026/`, and nested privacy/support paths. Do not invent download URLs.

- [ ] **Step 7: Run the real publisher and reconcile counts**

Run:

```bash
CYBERNETKS_VAULT="/Users/schabrechtsk/Library/Mobile Documents/iCloud~md~obsidian/Documents/The Lab" ./scripts/publish-site
```

Expected: 32 migrated publications plus 3 projects and 4 supporting pages, no validation failures, and a successful Hugo build. The migration manifest still covers all 40 Ghost routes through identity paths or explicit replacements.

- [ ] **Step 8: Run all publisher tests and commit only public generated output**

Run: `python3 -m unittest discover -s tests/publish -p 'test_*.py' -v`

Expected: PASS.

Inspect `git status --short` and confirm the Ghost JSON is absent.

```bash
git add tools/migration tests/publish data/migration generated/content
git commit -m "content: migrate Ghost routes from Obsidian"
```

The Obsidian edits remain in the vault's own history and are not copied wholesale into the website repository.

### Task 10: Enforce Built-Site and Legacy-Route Contracts

**Files:**
- Create: `tests/site/html_contract.py`
- Create: `tests/site/test_legacy_routes.py`
- Create: `scripts/check-site`
- Modify: `tests/site/test_site_contract.py`
- Modify: `Makefile`

**Interfaces:**
- Consumes: a production Hugo `public/` directory and `data/migration/ghost.yaml`.
- Produces: `check_public_tree(public: Path, manifest: Path) -> list[str]` and a zero/nonzero `scripts/check-site` result.

- [ ] **Step 1: Write failing legacy-route coverage tests**

```python
def test_every_ghost_path_has_a_page_or_redirect(self) -> None:
    errors = check_public_tree(BUILT_PUBLIC, ROOT / "data/migration/ghost.yaml")
    self.assertEqual(errors, [])

def test_missing_legacy_route_names_the_path(self) -> None:
    errors = check_public_tree(BROKEN_PUBLIC, GHOST_MANIFEST)
    self.assertIn("missing legacy route: /operator-support/", errors)
```

- [ ] **Step 2: Run the tests and verify failure**

Run: `python3 -m unittest tests.site.test_legacy_routes -v`

Expected: FAIL because the built-site checker does not exist.

- [ ] **Step 3: Implement standard-library HTML checks**

Use `html.parser.HTMLParser` to collect local `href`, `src`, canonical, Open Graph, heading, and landmark attributes. Check:

- every internal link resolves to a generated file;
- every local image and media source exists;
- each HTML page has one canonical link on `https://cybernetks.be/`;
- every content page has title, description, `og:title`, `og:description`, and `og:image`;
- every page has one `main` landmark and one level-one heading;
- every route in the Ghost manifest has an output page or redirect page to its declared replacement;
- `/operator-privacy/` and `/operator-support/` resolve to their nested project pages;
- no HTML contains Portal, newsletter signup, member login, analytics script, or `www.cybernetks.be` canonical URLs.

- [ ] **Step 4: Add the production check entry point**

```bash
#!/usr/bin/env bash
set -euo pipefail
hugo --gc --minify --cleanDestinationDir
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Make `make test` call unit tests and `make check` call `scripts/check-site`.

- [ ] **Step 5: Run the complete validation suite**

Run: `./scripts/check-site`

Expected: Hugo exit 0, all tests PASS, 40/40 legacy routes accounted for, and no unresolved internal links or assets.

- [ ] **Step 6: Commit the site contract**

```bash
git add tests/site scripts/check-site Makefile
git commit -m "test: enforce site and migration contracts"
```

### Task 11: Add GitHub Pages Deployment and Cutover Documentation

**Files:**
- Create: `.github/workflows/pages.yaml`
- Create: `static/CNAME`
- Modify: `README.md`
- Create: `docs/operations/publishing.md`
- Create: `docs/operations/cutover.md`

**Interfaces:**
- Consumes: a main-branch commit that passes `./scripts/check-site`.
- Produces: a GitHub Pages deployment artifact and an explicit human cutover checklist.

- [ ] **Step 1: Write a workflow contract test before the workflow exists**

Add to `tests/site/test_site_contract.py`:

```python
def test_pages_workflow_builds_before_deploying(self) -> None:
    workflow = (ROOT / ".github/workflows/pages.yaml").read_text(encoding="utf-8")
    self.assertIn("./scripts/check-site", workflow)
    self.assertIn("actions/deploy-pages@v5", workflow)
    self.assertIn("needs: build", workflow)
```

- [ ] **Step 2: Run the workflow test and verify failure**

Run: `python3 -m unittest tests.site.test_site_contract.DeploymentContractTest -v`

Expected: FAIL because `.github/workflows/pages.yaml` does not exist.

- [ ] **Step 3: Implement the official GitHub Pages workflow**

Use `actions/checkout@v5`, `actions/configure-pages@v5`, `actions/upload-pages-artifact@v5`, and `actions/deploy-pages@v5`. Pin `HUGO_VERSION: 0.164.0`, install the Extended Linux release, install Python 3.12 and `requirements.txt`, run `./scripts/check-site`, upload `public/`, and deploy only after the build job succeeds.

The workflow triggers on pushes to `main` and `workflow_dispatch`, uses `contents: read`, `pages: write`, and `id-token: write`, and sets deployment concurrency to avoid overlapping releases.

- [ ] **Step 4: Add the canonical domain file and operational instructions**

`static/CNAME` contains exactly:

```text
cybernetks.be
```

`docs/operations/publishing.md` documents:

```bash
export CYBERNETKS_VAULT="/Users/schabrechtsk/Library/Mobile Documents/iCloud~md~obsidian/Documents/The Lab"
make publish
make preview
./scripts/check-site
git add generated/content
git commit -m "content: publish Cybernetks updates"
git push origin main
```

State clearly that publishing never reads outside the allowlist and never pushes automatically.

- [ ] **Step 5: Write the exact cutover checklist**

`docs/operations/cutover.md` requires:

1. Verify the GitHub Pages preview and all 40 Ghost routes.
2. Verify the custom domain in GitHub before changing DNS.
3. Configure the apex records required by GitHub Pages and `www` as a CNAME to `Cybernetks.github.io`.
4. Set `cybernetks.be` as the GitHub Pages custom domain so GitHub redirects `www` to the apex.
5. Wait for GitHub's TLS certificate and enable HTTPS enforcement.
6. Re-run the 40-route check against the public domain.
7. Confirm Operator privacy and support URLs before entering them in App Store Connect.
8. Retain the Ghost export privately.
9. Cancel Ghost only after the public verification passes.

Do not place guessed DNS values in the repository; at cutover, copy the current official GitHub Pages apex records from GitHub's documentation and verify them in the domain provider before saving.

- [ ] **Step 6: Run all local checks and review the workflow diff**

Run: `./scripts/check-site`

Expected: PASS.

Run: `git diff --check`

Expected: no output and exit 0.

Run: `git status --short`

Expected: only the workflow, CNAME, README, and operations documents for this task.

- [ ] **Step 7: Commit deployment configuration**

```bash
git add .github/workflows/pages.yaml static/CNAME README.md docs/operations tests/site/test_site_contract.py
git commit -m "ci: deploy Cybernetks with GitHub Pages"
```

### Task 12: Final Review and Pre-DNS Release Candidate

**Files:**
- Modify only files required to correct findings from the checks below.

**Interfaces:**
- Consumes: the complete implemented plan.
- Produces: a locally verified release candidate ready to push and configure in GitHub Pages; it does not change DNS or cancel Ghost.

- [ ] **Step 1: Run the complete automated suite from a clean generated tree**

Run:

```bash
CYBERNETKS_VAULT="/Users/schabrechtsk/Library/Mobile Documents/iCloud~md~obsidian/Documents/The Lab" ./scripts/publish-site
./scripts/check-site
```

Expected: publisher success, Hugo success, all unit and site tests PASS, 40/40 Ghost routes covered, and no missing assets.

- [ ] **Step 2: Review every page family at desktop and mobile widths**

Run: `hugo server --disableFastRender`

Review `/`, `/projects/`, all three project pages, Operator privacy/support, `/logs/`, one short and one long Log, `/snapshots/`, one early and the latest Snapshot, `/about/`, and `/uses/` at approximately 1280px, 760px, 430px, and 320px.

Verify header identity rendering, title wrapping, project icons, genuine media only, Snapshot `00` alignment, keyboard focus, heading order, colour contrast, and footer wrapping.

- [ ] **Step 3: Verify repository privacy and generated ownership**

Run:

```bash
git ls-files | grep -E 'ghost.*json|Downloads|The Lab' && exit 1 || true
git grep -n -E '/Users/schabrechtsk|cybernetks\.ghost\.' -- ':!docs' && exit 1 || true
git grep -n -E '#/portal/|member.*login|google-analytics|gtag\(' -- layouts assets static generated/content
```

Expected: no private Ghost export filename, newsletter or sign-in UI, or analytics code in the shipped site. Editorial mentions of newsletters inside migrated historical articles are allowed.

- [ ] **Step 4: Verify the release-candidate diff and commit corrections**

Run: `git diff --check`

Expected: no output.

Run: `git status --short`

Expected: either clean or only reviewed corrections from this task.

If corrections were required:

```bash
git add -u
git commit -m "fix: resolve Cybernetks release review findings"
```

- [ ] **Step 5: Stop before external cutover**

Report the Pages workflow status and release-candidate commit. Do not push, change DNS, enter App Store URLs, enable external analytics, or cancel Ghost without the user's explicit instruction at that stage.
