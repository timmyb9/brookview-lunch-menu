# Brookview Elementary Lunch Menu — DAKboard Feed

Fetches the current week's lunch menu from SchoolCafe (Waukee CSD / Brookview
Elementary) and renders it as a static HTML page, refreshed automatically via
GitHub Actions and served via GitHub Pages.

## Setup

1. Push this repo to GitHub (public repo is easiest, or private with Pages on
   a paid plan).
2. In repo Settings -> Pages, set Source = "Deploy from a branch", branch =
   `main`, folder = `/ (root)`. Save.
3. In repo Settings -> Actions -> General, under Workflow permissions,
   select "Read and write permissions" (needed so the Action can commit the
   generated index.html back to the repo).
4. Manually trigger the workflow once: Actions tab -> "Update Lunch Menu" ->
   Run workflow. This generates the first index.html.
5. Your page will be live at:
   https://<your-github-username>.github.io/<repo-name>/
6. In DAKboard, add a Website/iFrame block pointing at that URL. Set it to
   refresh every hour or two (DAKboard's own refresh setting) since the
   underlying page also self-refreshes.

## Files

- `fetch_menu.py` — talks to the SchoolCafe API, returns structured week data
- `generate_html.py` — renders `index.html` from that data
- `.github/workflows/update-menu.yml` — runs the above daily at 6am and 1pm
  Central and commits the result

## Notes

- School/serving line is hardcoded at the top of `fetch_menu.py`
  (`SCHOOL_ID`, `SERVING_LINE`, `MEAL_TYPE`). To switch to breakfast or a
  different Waukee school, change those constants.
- No login/API key required — this endpoint is public.
