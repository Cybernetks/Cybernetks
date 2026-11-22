# Operator website cutover

Prepared locally on 22 November 2026; not deployed.

Operator's product website is at `https://operator.cybernetks.be/`.
Cybernetks keeps `/projects/operator/` as a studio overview, with release
context and related writing. Its primary action points to the product website;
the App Store URL remains in the project metadata. Homepage and project-directory
cards continue to lead to the studio overview.

## Verified on 22 November 2026

- The HTTPS homepage loads with a valid certificate and returns HTTP 200.
- `/support/` and `/privacy/` return HTTP 200 and identify the intended pages.
- The project overview links directly to these new HTTPS destinations.
- Existing Cybernetks support and privacy pages retain their full content and
  legacy aliases, with a notice and clickable link to the current information
  on the product site. These pages do not redirect visitors.
- HTTP still returns 200 rather than redirecting to HTTPS. Cybernetks uses HTTPS
  links directly; enforcement remains an Operator hosting follow-up.

## Before publishing

Preview the Cybernetks project page and run `./scripts/check-site`, then follow
the normal publishing workflow. Nothing in this preparation changes App Store
Connect or deploys either website.

## Follow-up

Keep the old pages available while the App Store still links to them. In a
later release, update app links and App Store Connect to the new destinations.
After those changes are live, review retiring the old pages and legacy aliases.
