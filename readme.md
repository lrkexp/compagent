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
│   ├── index.html             # GitHub Pages entry point
│   ├── styles.css             # Dashboard styling
│   ├── app.js                 # Client-side rendering logic
│   └── data/latest.json       # Structured payload consumed by the page
├── reports/latest.md          # Most recent Markdown briefing
├── src/compliance_agent/      # Agent code for fetching, filtering, and scoring
└── .github/workflows/update-report.yml  # Daily automation
```

## Support

For questions, suggestions, or additional feeds to monitor, contact the
Clubessential Holdings compliance team.
