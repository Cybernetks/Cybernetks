# Publishing

Publishing is a deliberate local operation. It reads only the Cybernetks source
allowlist, never reads outside that allowlist, and never pushes, deploys, or edits
the vault automatically.

From the repository root, publish the approved Obsidian material and inspect the
site locally:

```bash
export CYBERNETKS_VAULT="/Users/schabrechtsk/Library/Mobile Documents/iCloud~md~obsidian/Documents/The Lab"
make publish
make preview
./scripts/check-site
git add generated/content
git commit -m "content: publish Cybernetks updates"
git push origin main
```

Review the generated changes before committing. The final `git push` is a separate,
explicit human action; only a successful commit on `main` starts the GitHub Pages
deployment workflow.

For note metadata, public-content boundaries, and migration details, see
[Publishing from Obsidian](../editorial-publishing.md).
