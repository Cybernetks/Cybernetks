# Publishing from Bear

Bear is the private editorial workspace and second brain. It contains operational,
personal, and project context that must never be exposed by an automated bulk export.
The website therefore uses an explicit public adaptation layer under
`generated/content/`. Despite the legacy directory name, these files are now reviewed
publication sources and may be edited deliberately.

The boundary is intentional:

- Bear owns the complete internal record and the evidence behind a publication.
- `generated/content/` owns the wording and metadata approved for the public website.
- GitHub Actions reads only the repository. It never connects to Bear.
- `make publish` validates and builds the reviewed public content. It does not copy,
  overwrite, commit, push, or deploy anything.

For a Monthly Snapshot, first complete the internal review in Bear. Then create a public
adaptation at `generated/content/snapshots/YYYY-MM/index.md`. Remove private client,
family, financial, and operational detail unless it is deliberately part of the public
story. Bear wikilinks must become public site links or plain text.

## Public metadata

Every public page uses Hugo front matter with `title`, `date`, `description`, `url`,
`topics`, `projects`, `aliases`, and `params.kind`. Keep an existing `url` stable even
when its title changes.

Snapshots additionally use:

- `params.review_month` in `YYYY-MM` form;
- `params.one_sentence` for the opening statement; and
- ordered `params.sections` entries with `number`, `title`, and Markdown `body`.

Projects and Logs retain their existing kind-specific fields. Use an existing published
file as the template rather than inventing new metadata. The retired Obsidian converter
under `tools/publish/` remains only as tested migration tooling; it is not part of the
current release workflow.

## Public body boundaries

The repository page bundle contains only the public article or page body. Editorial
notes, raw transcripts, social drafts, private roadmaps, and pricing analysis remain
in Bear. Adaptations such as YouTube or podcast links belong in supported public front
matter, not as copied private sections.

```markdown
The article to publish.

## An article subsection

More article text.
```

Bear headings such as `# Blog post`, `# Raw Transcript`, `## Published Content`, and
`## Website Content` are editorial boundaries only. Do not copy those wrapper headings
into the public page bundle.

## Links and images

Link to a canonical public route. Do not copy Bear wikilinks into public Markdown.
Place public images in the owning page bundle and reference them with ordinary Markdown,
including descriptive alternative text. Do not retain Ghost export placeholders such
as `__GHOST_URL__`.

The migration manifest in `data/migration/ghost.yaml` contains public routes only.
Do not commit the Ghost export or copy member, account, or settings data into this
repository. Changes to a former page's destination belong in the manifest;
identity mappings preserve all 32 migrated publication URLs.
