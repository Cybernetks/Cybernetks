# Cybernetks Hugo Website Design

Date: 2026-09-15

## Purpose

Replace the current Ghost publication at `https://www.cybernetks.be` with a static Hugo website hosted on GitHub Pages. The new site must give Cybernetks full control over presentation, make products and publishing equally credible, and remove the unused newsletter, membership, and sign-in features.

Cybernetks is presented as a solo product studio building thoughtful software in public. Products demonstrate what the studio makes; publications show the reasoning, progress, and lessons behind that work.

## Goals

- Make `cybernetks.be` the primary home for Cybernetks products and writing.
- Present Operator, Cybernetks Planner, and Alien Miner as real projects at different lifecycle stages.
- Publish two clearly related but visually distinct publication types: Logs and Monthly Snapshots.
- Keep Obsidian as the editorial source of truth.
- Make publication an explicit, safe, one-way action from Obsidian to Hugo.
- Preserve every existing published Ghost post URL.
- Deploy a static site automatically after reviewed changes reach the main branch.
- Leave a clean extension point for privacy-conscious analytics later.

## Non-goals for the first release

- Newsletter delivery or email collection
- Member accounts, sign-ins, or gated content
- Comments or other server-side community features
- On-site search
- Complex archive filters or public tag pages
- A content management interface inside the website
- Automatic publishing whenever a vault note changes
- Analytics at launch

## Information architecture

The primary navigation contains:

- Home
- Projects
- Logs
- Monthly Snapshots
- About

The content hierarchy is:

```text
/
/projects/
/projects/operator/
/projects/operator/privacy/
/projects/operator/support/
/projects/cybernetks-planner/
/projects/alien-miner/
/logs/
/snapshots/
/about/
```

Additional project-specific privacy or support pages follow the same nested structure. A project page links to its privacy and support pages, and those pages link back to the owning project.

Existing Ghost post URLs remain at their current paths instead of being moved below `/logs/` or `/snapshots/`. The section archive URLs organize discovery; individual legacy content retains its public address.

## Content model

### Logs

Logs contain all ordinary Cybernetks writing, including the material previously split between numbered Logs and regular posts. Existing and future Logs are unnumbered. Removing a number from a title does not change the post's existing URL.

A Log has:

- Title
- Publication date
- Publication status
- Summary
- Existing or generated URL path
- Optional topic labels
- Optional related projects
- Optional hero or Open Graph image
- Body
- Optional links to adaptations on YouTube or podcast platforms

The website is the canonical publication. A podcast episode, YouTube video, or social post is an optional adaptation and never blocks publishing the Log.

### Monthly Snapshots

Monthly Snapshots are structured studio reviews. They retain a recognisable recurring format without being reduced to output counts.

A Snapshot has:

- Title
- Review month
- Publication date
- Publication status
- Summary
- URL path
- Month-in-one-sentence statement
- Last month's bet and result
- Business movement
- Current focus
- What the month revealed
- What comes next
- Optional related projects
- Optional hero or Open Graph image

### Projects

The initial project index contains Operator, Cybernetks Planner, and Alien Miner. Each project has a permanent internal page even if its external destination or lifecycle changes.

A project has:

- Name
- Short promise
- Description
- Lifecycle status
- Project kind and supported platforms
- Official logo or app icon when available
- Screenshots or other genuine product media when available
- Audience or problem statement
- Core capabilities
- Privacy position where relevant
- Current release state and next meaningful outcome
- Related Logs and Monthly Snapshots
- Optional external destinations
- Optional nested privacy and support pages

The project page's primary action is derived from lifecycle state:

- Work in progress: `Read the latest update`
- Public beta: `Join the beta`
- Released native app: `Download on the App Store` or the relevant store
- Released web application: `Open the app`
- Open-source project: `View on GitHub`
- Archived experiment: no forced primary action

`Read the latest update` links to the newest publication associated with the project. It does not imply a subscription.

## Visual direction

### Brand treatment

The site uses the established Cybernetks dark indigo, gold, and white visual language. It avoids gradients, neon effects, excessive decoration, and unrelated accent colours.

The header uses two separate official assets:

- The circular Cybernetks head symbol
- The custom `CYBERNETKS` wordmark

They are placed beside one another in the interface but are not merged into a new source logo. The supplied black wordmark has a derived gold web-display variant. Its paths and proportions remain unchanged. The original file remains untouched.

Project identities appear only within project-specific areas. Project pages prominently show an official app icon or logo. The homepage uses project marks sparingly within the featured project and project cards. Logs and Snapshots remain editorial and do not show a project logo by default.

### Homepage hierarchy

1. Dark branded header
2. Hero: `A solo studio building thoughtful software in public.`
3. `Inside the studio` mosaic with a prominent Operator feature, latest Log, and latest Monthly Snapshot
4. `Projects and experiments` with Operator, Cybernetks Planner, and Alien Miner
5. `Latest from the studio`
6. Footer with relevant external channels

The projects section appears before the general latest-publications list. This establishes Cybernetks as a product studio first while the publication content supplies trust and context.

### Log view

The Log template is quiet and reading-first:

- Spacious title area
- Type, topic, date, and reading-time metadata
- Narrow readable body measure
- Restrained gold accents and pull quotes
- Related topics/projects and next-publication navigation after the body

### Monthly Snapshot view

The Snapshot uses the same typography, header, palette, and overall page structure, with a modest increase in structure:

- Review month displayed prominently
- Numbered review sections
- A highlighted `month in one sentence` statement
- Compact result blocks where the source contains meaningful measures
- A clearly separated next outcome and first concrete step

The `00 · In one sentence` label aligns to the same grid as all other numbered section labels in the production implementation.

### Project view

The project template contains:

- Lifecycle, platform, name, promise, and concise product explanation
- Official project logo or app icon near the title
- Genuine product screenshots or media when available
- Lifecycle-aware primary action
- At-a-glance product facts
- Why the product exists
- Core capabilities
- Current release state and next meaningful outcome
- Related build-in-public publications
- Privacy and support links where relevant

Until genuine screenshots are available, the implementation leaves the media area absent or deliberately reserved; it does not invent a fake product interface.

## Obsidian source of truth

The source vault is `The Lab`. The initial publishing allowlist is limited to Cybernetks-owned content beneath:

- `3. Businesses/Cybernetks/Logs/`
- `3. Businesses/Cybernetks/Posts/`
- `3. Businesses/Cybernetks/Monthly Snapshots/`
- Explicit project and page notes selected for publication beneath `3. Businesses/Cybernetks/`

The exporter never scans unrelated personal or business notes for publication. A referenced note outside the allowlist does not become public implicitly.

The old `Posts` folder remains readable during migration, but its published entries are exported as Logs. A later vault cleanup may move those notes into `Logs` after references are checked; that move is not required for the website migration.

Required shared front matter:

```yaml
title: A clear public title
status: published
publish_date: 2026-09-15
summary: A concise public description.
url: https://www.cybernetks.be/existing-or-chosen-path/
```

For existing notes, the exporter accepts the current full `www.cybernetks.be` URL and extracts its path. New notes may use either a site-relative path or the canonical `cybernetks.be` URL. The generated site's canonical host is always `cybernetks.be`.

Type-specific fields add the publication kind, review month, project relations, imagery, and external actions. Draft notes may omit public-only fields until publication, but published notes must pass all validations.

Obsidian remains the only editorial source. Generated Hugo Markdown is not edited by hand because the next export replaces it.

## Publishing pipeline

Publishing is an explicit local command run from the Cybernetks repository.

The pipeline is:

1. Read the allowlisted Obsidian notes.
2. Select only entries with `status: published`.
3. Parse and validate front matter before writing generated output.
4. Classify old regular posts as Logs and remove `#NNN - ` from displayed Log titles.
5. Preserve explicitly supplied URL paths.
6. Resolve supported Obsidian links and embeds.
7. Copy only assets referenced by published content.
8. Generate content into a staging directory.
9. Run content, URL, and asset validation against the staging result.
10. Replace the previous generated Hugo content only after validation succeeds.
11. Run a production Hugo build.
12. Leave the changes in the repository for local preview, review, and an intentional Git commit and push.

The tool never edits or deletes vault notes. It also never pushes changes automatically.

## Hugo structure

The repository separates authored presentation code from generated content:

```text
assets/                    Compiled styling and browser assets
content/                   Generated public Markdown
data/                      Site configuration and the URL migration manifest
layouts/                   Base, section, taxonomy, and content templates
static/                    Static brand assets and files
tools/publish/             Obsidian export and validation code
tests/                     Exporter and site-contract tests
docs/superpowers/specs/    Approved design specifications
hugo.toml                  Hugo configuration
```

Content-type templates are separate but share a base layout and small reusable partials. Project state-to-action selection is isolated from the project page layout so it can be tested independently.

The production site generates canonical URLs, Open Graph metadata, a sitemap, and RSS feeds for public writing. RSS is passive output; the site does not promote a newsletter or collect email addresses.

## Link and embed rules

- Normal Markdown links are preserved.
- Public Obsidian wiki links resolve to exported public pages.
- Links to non-public notes fail validation unless explicitly marked as plain text.
- Embeds copy only the referenced file and must resolve to an allowed asset type.
- Missing images or files fail the export.
- Every generated internal link is checked after the Hugo build.
- External links are rendered normally but are not required to be online for a local export to succeed.

## Migration and URL policy

The Ghost export `cybernetks.ghost.2026-09-15-18-34-30.json` is reference data, not the editorial source.

Its initial inventory contains:

- 40 published entries
- 32 published posts
- 8 published pages
- 1 draft post

The vault currently contains public URL front matter for all 32 published Ghost posts. The eight Ghost pages require explicit reconciliation against the new About, project, privacy, and support structure.

Migration rules:

- Every published Ghost URL is recorded in a version-controlled migration manifest.
- Existing post URLs are preserved exactly wherever practical.
- Numbered Log URLs remain valid while displayed titles lose their numbers.
- New content uses clean, unnumbered slugs.
- Old Ghost pages that are superseded either retain their path or generate a deliberate redirect to the replacement.
- Operator privacy and support pages move to their clean nested URLs because their Ghost addresses have not been registered with Apple. Their old Ghost paths redirect to the nested replacements.
- The Ghost theme, member data, newsletter configuration, and analytics are not migrated.
- Ghost-hosted images are copied only when an equivalent source asset is not already available locally.

The Ghost export remains outside the website repository because it can contain settings and account data. The migration manifest contains only the public paths and non-sensitive reconciliation information required by the build.

## Validation and failure handling

The publisher fails without changing the current generated site when it detects:

- A published entry missing a required field
- An invalid or duplicate URL
- Duplicate content identifiers
- An unknown publication or project status
- A missing referenced asset
- An unresolved public Obsidian link
- An attempted implicit publication outside the allowlist
- A collision between a legacy URL and a new route

Errors identify the source note and field or link that must be fixed. Staging output is disposable and never becomes the active generated content after a failure.

The production build fails on invalid templates, broken required internal links, missing canonical metadata, or a missing migration route.

## Testing strategy

### Exporter tests

- Published and draft selection
- Allowlist enforcement
- Front-matter validation per content type
- Number removal from displayed legacy Log titles
- Preservation of existing URL paths
- Wiki-link and embed resolution
- Project relationship resolution
- Atomic staging-to-generated replacement
- Clear errors for every validation failure class

### Site contract tests

- Homepage contains the expected featured and latest sections
- Project index contains all three launch projects
- Each publication type selects the correct template
- Project lifecycle states produce the correct primary action
- Project privacy and support pages cross-link correctly
- Sitemap, canonical metadata, Open Graph metadata, and RSS are generated
- All internal links and referenced assets resolve
- Every published Ghost path is present or deliberately redirected

### Visual and accessibility review

- Review homepage, Log, Snapshot, project, privacy, support, archive, and About templates at desktop and narrow mobile widths
- Confirm keyboard navigation and visible focus treatment
- Confirm semantic heading order and landmark structure
- Confirm text and gold-accent contrast on dark surfaces
- Confirm project marks retain their proportions
- Confirm long titles and navigation do not overlap or clip

## Deployment

GitHub Actions builds the production Hugo site from the main branch and deploys it to GitHub Pages only after validation and tests pass.

Deployment configuration includes:

- A pinned Hugo version
- The production base URL `https://cybernetks.be/`
- The GitHub Pages custom-domain configuration
- HTTPS enforcement after DNS and certificate provisioning succeed
- No deployment secrets in generated files or the repository

Analytics, if adopted later, is added through a single disabled-by-default Hugo partial and configuration value. No analytics code ships in the first release.

## Cutover and Ghost cancellation

1. Keep the Ghost JSON export as a private safety copy.
2. Reconcile all 40 published Ghost entries with the vault and new page model.
3. Recover any Ghost-only images required by those entries.
4. Deploy the Hugo site to its GitHub Pages address and complete all checks.
5. Verify the custom domain configuration before changing DNS.
6. Point `cybernetks.be` and `www.cybernetks.be` to GitHub Pages, with `www` redirecting to the canonical apex domain.
7. Verify HTTPS, canonical host behaviour, pages, media, and the full legacy URL manifest on the public domain.
8. Cancel Ghost only after the new public site passes verification.

After DNS moves, the Ghost installation may remain accessible through its `ghost.io` administration address while its subscription is active, but edits made there do not affect the Hugo site.

## Acceptance criteria

- Cybernetks is presented as a solo product studio building thoughtful software in public.
- The approved dark Cybernetks visual direction is implemented responsively.
- The official head symbol and gold web-display wordmark appear correctly in the header.
- Operator, Cybernetks Planner, and Alien Miner appear on the homepage and have project pages.
- Logs are unnumbered in display and merge the old regular-post distinction.
- Monthly Snapshots have a subtly more structured template than Logs.
- Obsidian is the source of all publication content.
- Only explicitly published, allowlisted notes can enter the site.
- Existing Ghost post URLs continue to work.
- Operator privacy and support pages use the nested project structure.
- The site contains no newsletter, member, sign-in, or analytics functionality at launch.
- A failed export or build cannot partially replace the last valid generated site.
- The site deploys to GitHub Pages through a tested main-branch workflow.
