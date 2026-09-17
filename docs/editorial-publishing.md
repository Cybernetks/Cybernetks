# Publishing from Obsidian

Obsidian is the editorial source. Run `CYBERNETKS_VAULT="/path/to/vault" ./scripts/publish-site`
from this repository to validate the approved sources, regenerate `generated/content`,
and build the site. Use the pinned Python and Hugo versions described in the README.
Review and commit the generated output; editing generated Markdown directly will be
overwritten by the next publication run.

The publisher only reads the explicit Cybernetks source allowlist in
`tools/publish/config.py`, and only publishes notes with `publication_status: published`.
Published notes need `title`, `publish_date`, `summary`, and `url`. Keep existing public
URLs stable even when a title changes. Snapshots also need `review_month: YYYY-MM`.
Project notes need `status`, `promise`, and `project_kind`.

The publisher exports only supported public metadata. Common optional fields are
`topics`, `projects`, `aliases`, and `image`. Logs may also use `youtube_url`,
`podcast_url`, `youtube`, and `podcast`; Snapshots use `review_month` and derive their
structured sections from the public body. Projects may use `icon`, `screenshots`,
`why`, `capabilities`, `platforms`, `release_state`, `next`, `latest_update`,
`beta_url`, `store_url`, `app_url`, `source_url`, and `project_url`. Supporting pages
may use `project`. Other note properties are ignored, including vault classifications,
internal dates, nested `params`, and editorial notes. Keep only public values in
these supported fields; add new supported fields deliberately in the publisher.

## Log article boundaries

Use `# Blog post` immediately before the website article. It ends at the next
level-one heading. Article subsections can use `##` and `###` freely. Optional
podcast, YouTube, social, and transcript sections belong under separate level-one
headings after the article. A Log can be published without any of those adaptations.

```markdown
# Log title

# Blog post

The article to publish.

## An article subsection

More article text.

# Raw Transcript

Private editorial source material; excluded from the website article.
```

The legacy `## Published Content` marker consumes the rest of a note; do not put
private editorial material after it without an explicit `# Blog post` boundary.
For supporting pages and projects, `## Website Content` consumes the rest of the
note. Keep private roadmap, pricing, and planning material before that marker.
When all headings inside `Website Content` are nested below level two, publication
promotes them together so the first level is `##`, preserving their relative
hierarchy and leaving fenced code examples unchanged.

## Links and images

Link to a canonical public route or use a wiki link to another approved published
note. The publisher rejects wiki links to private or unresolved notes. Use explicit
local embeds such as `![[assets/screenshot.png|Descriptive alternative text]]` for
images that should be copied into the page bundle. Do not retain Ghost export
placeholders such as `__GHOST_URL__`.

The migration manifest in `data/migration/ghost.yaml` contains public routes only.
Do not commit the Ghost export or copy member, account, or settings data into this
repository. Changes to a former page's destination belong in the manifest;
identity mappings preserve all 32 migrated publication URLs.
