# GitHub Pages cutover

Use this checklist when moving `cybernetks.be` from Ghost to GitHub Pages. It is a
human-run change: this repository does not modify DNS, GitHub Pages settings, or
the Ghost subscription. The committed `static/CNAME` is retained as site metadata,
but a GitHub Actions Pages deployment ignores CNAME files; the GitHub Pages
**Custom domain** setting is authoritative and must be set by a human.

1. In the repository's **Settings → Pages → Build and deployment**, set
   **Source** to **GitHub Actions**. This is a human-only setting:
   `configure-pages` does not switch the Pages source.
2. Confirm the GitHub Pages deployment preview works, then verify every one of the
   40 Ghost routes against it.
3. [Verify ownership of the custom domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
   in GitHub before changing DNS.
4. In the repository's **Settings → Pages**, set `cybernetks.be` as the custom
   domain before changing DNS. Selecting the apex makes GitHub redirect `www` to
   the apex.
5. At cutover, consult GitHub's current
   [custom-domain DNS guidance](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
   and copy its required apex records into the domain provider. Do not place guessed
   DNS values in this repository. Configure `www` as a CNAME to
   `Cybernetks.github.io`, and verify every record at the domain provider before
   saving it.
6. Wait for GitHub to issue the TLS certificate, then enable HTTPS enforcement in
   GitHub Pages.
7. Re-run the 40-route check against `https://cybernetks.be` after DNS and TLS are
   live.
8. Confirm the Operator privacy and support URLs publicly before entering them in
   App Store Connect.
9. Retain the Ghost export privately; it must not be committed to this repository.
10. Cancel Ghost only after the public-domain verification passes.

The GitHub Pages workflow is documented in
[GitHub's Hugo deployment guide](https://gohugo.io/host-and-deploy/host-on-github-pages/).
