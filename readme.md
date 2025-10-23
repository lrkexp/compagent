# SaaS Compliance Intelligence Dashboard

This repository powers a GitHub Pages site that tracks privacy, cybersecurity,
and regulatory updates for a global SaaS portfolio serving Golf &amp; Club,
Fitness, and Parks &amp; Recreation markets. The site is designed for compliance
leaders who need a quick, structured snapshot without installing a local
Python environment.

## What you get

- **Static web dashboard** &mdash; `docs/index.html` renders a minimalist feed with
  manual refresh controls, coloured vertical badges, and responsive typography so
  you can skim headline summaries from any browser.
- **Automated refresh** &mdash; A scheduled GitHub Action (`update-report.yml`)
  gathers fresh articles daily, builds the JSON payload, and deploys the site via
  GitHub Pages without touching the main branch &mdash; no more merge conflicts from
  generated files.
- **Markdown archive** &mdash; The deployed site also exposes `/reports/latest.md`,
  making it easy to copy content into newsletters or Vanta evidence folders.

## View the dashboard on GitHub Pages

1. Open the repository **Settings → Pages** panel.
2. Under **Build and deployment**, choose **GitHub Actions** (the workflow in this
   repo already prepares the artifact).
3. After the next workflow run completes, GitHub will provide a public URL such
   as `https://<org>.github.io/<repo>/`. Bookmark it to review the daily updates.

If you just cloned the repository and want to preview the experience without
waiting for Pages, open `docs/index.html` directly in your browser. The page will
fall back to a bundled sample payload (`docs/data/sample.json`) when the live
endpoint is unreachable, giving you a realistic preview even when offline.
# Compliance Intelligence Dashboard

This repository powers a GitHub Pages site that tracks privacy, cybersecurity,
and regulatory updates for the SaaS portfolio serving
Golf &amp; Club, Fitness, and Parks &amp; Recreation markets. The site is designed for
compliance leaders who need a quick, structured snapshot without installing a
local Python environment.

## What you get

- **Static web dashboard** &mdash; `docs/index.html` renders a responsive view of
the latest briefing with filters by vertical and compliance theme so you can
skim headline summaries from any browser.
- **Automated refresh** &mdash; A scheduled GitHub Action (`update-report.yml`)
collects fresh articles daily, writes a JSON payload (`docs/data/latest.json`),
and commits the results back to the repository so GitHub Pages always serves the
latest data.
- **Markdown archive** &mdash; Each run also stores a Markdown briefing in
`reports/latest.md`, making it easy to copy content into newsletters or Vanta
evidence folders.

## View the dashboard on GitHub Pages

1. Open the repository settings in GitHub and enable **Pages**.
2. Choose the branch that contains this code (typically `main`) and set the
   source folder to `docs/`.
3. After saving, GitHub will provide a public URL such as
   `https://<org>.github.io/<repo>/`. Bookmark it to review the daily updates.

If you just cloned the repository and want to preview the latest build without
waiting for Pages, open `docs/index.html` directly in your browser. GitHub’s
file viewer also renders the static HTML when you click `docs/index.html` in the
web interface, making it easy to spot-check content before publishing.

The `docs/index.html` file also works offline &mdash; simply open it in a browser if
you want to preview the experience locally.

## How the automated update works

The workflow in `.github/workflows/update-report.yml` runs once per day (10:00
UTC by default) and can also be triggered manually. It:

1. Installs Python 3.11 and the required dependencies.
2. Executes `python build_site.py` to gather news, classify it, and write `site/`
   artifacts (`data/latest.json`, `reports/latest.md`).
3. Packages the static assets from `docs/` together with the generated payloads
   and publishes them to GitHub Pages via the official deployment actions.

Because the site is deployed from workflow artifacts, the main branch remains
clean and you never have to resolve merge conflicts caused by automated updates.
1. Installs Python 3.11.
2. Executes `python build_site.py` to gather news, classify it, and write
   `docs/data/latest.json` plus `reports/latest.md`.
3. Commits any changes back to the repository, which in turn updates the
   published dashboard.

> **Note:** The workflow uses the repository’s GitHub token to push changes.
> Ensure branch protection rules allow the workflow bot to update the branch, or
> adjust the schedule/branch to fit your governance process.

## Optional local preview

You never need to run Python to benefit from the hosted dashboard, but you can
validate changes or experiment with configuration offline:

```bash
python build_site.py --offline --limit 5 --output-json artifacts/latest.json
```

This command uses the sample articles in `sample_data/offline_articles.json` and
writes to the local `artifacts/` directory so your working tree stays clean.
Point the `--output-json` argument at `docs/data/sample.json` if you want to
refresh the preview payload.
python build_site.py --offline --limit 5
```

This command uses the sample articles in `sample_data/offline_articles.json` and
updates both the static site data and the Markdown report.

## Customising the monitoring scope

| File | Purpose |
| ---- | ------- |
| `config/topics.json` | Keyword clusters for each vertical and compliance theme. Update labels or keywords to refine matching. |
| `config/news_sources.json` | RSS/Atom feeds to monitor. Add or remove sources and specify vertical hints for each feed. |
| `config/agent.json` | Runtime defaults (timeouts, per-feed item limits). |

After editing configuration files, let the scheduled workflow run (or execute
`python build_site.py`) to regenerate the dashboard.

## Repository layout

```
├── build_site.py              # CLI used by the workflow to render JSON + Markdown
├── docs/
│   ├── index.html             # GitHub Pages entry point (source)
│   ├── styles.css             # Dashboard styling
│   ├── app.js                 # Client-side rendering logic
│   └── data/sample.json       # Bundled preview payload
│   ├── index.html             # GitHub Pages entry point
│   ├── styles.css             # Dashboard styling
│   ├── app.js                 # Client-side rendering logic
│   └── data/latest.json       # Structured payload consumed by the page
├── reports/latest.md          # Most recent Markdown briefing
├── src/compliance_agent/      # Agent code for fetching, filtering, and scoring
└── .github/workflows/update-report.yml  # Daily automation
```

## Troubleshooting merge conflicts

If a pull request reports "This branch has conflicts that must be resolved"
for files such as `docs/index.html` or `build_site.py`, follow one of the
workflows below to reconcile your branch with `main`.

### Resolve directly on GitHub

1. Open the pull request and press **Resolve conflicts**.
2. For each conflicted file, keep the desired block of code and remove the Git
   conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`). The **Preview** tab helps
   you confirm the final content.
3. Click **Mark as resolved** and then **Commit merge**.
4. Re-run the **Update daily compliance briefing** workflow (or press the
   dashboard refresh button) to make sure the site still renders correctly.

### Resolve locally with Git

```bash
git checkout work                   # switch to your feature branch
git fetch origin
git merge origin/main               # bring in the latest published changes
# edit the listed files to remove conflict markers and keep the right content
python build_site.py --offline --limit 5  # optional: sanity-check the result
git add docs/index.html docs/app.js docs/styles.css build_site.py readme.md
git commit                          # record the resolution
git push                            # update the branch so the PR can merge
```

Once the branch rebases or merges cleanly, GitHub will update the pull request
status and enable the **Merge** button.

## Support

For questions, suggestions, or additional feeds to monitor, open an issue or
contact the compliance operations team.
## Support

For questions, suggestions, or additional feeds to monitor, contact the
Clubessential Holdings compliance team.
