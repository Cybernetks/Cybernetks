# Publishing

Publishing is a deliberate local operation. It reads only the Cybernetks source
files committed under `generated/content/`. It never reads Bear, pushes, deploys,
or edits the second brain automatically.

First adapt the relevant Bear material into a reviewed public page. Then, from the
repository root, validate the publication candidate and inspect the site locally:

```bash
make publish
make preview
./scripts/check-site
git add generated/content
git commit -m "content: publish Cybernetks updates"
git push origin main
```

Review the public changes before committing. The final `git push` is a separate,
explicit human action; only a successful commit on `main` starts the GitHub Pages
deployment workflow.

For note metadata, public-content boundaries, and migration details, see
[Publishing from Bear](../editorial-publishing.md).
