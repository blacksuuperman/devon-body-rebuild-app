name: Refresh UGC leads

on:
  schedule:
    - cron: '17 11 * * *'
  workflow_dispatch:

permissions:
  contents: write
  pages: write

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - name: Check out the repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Fetch fresh leads
        run: python automation/fetch_leads.py

      - name: Save leads.json if it changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add -A -- '*leads.json'
          if git diff --cached --quiet; then
            echo "No changes to save."
          else
            git commit -m "Refresh UGC leads"
            git push
          fi

      - name: Ask GitHub Pages to rebuild
        env:
          GH_TOKEN: ${{ github.token }}
        run: gh api -X POST "/repos/${{ github.repository }}/pages/builds" || true

# Turn on the daily UGC leads for Devon's Day Book

What this does: every morning GitHub runs a small script that collects new UGC job listings, saves them in a file called `leads.json`, and the app shows them to Devon on the UGC Desk. She does nothing.

You do this once. It takes about 10 minutes. You need to be signed in to github.com and be the owner of the repository where Devon's Day Book lives.

## Part 1: Add the new app files

1. Unzip `devons-day-book.zip` on your computer.
2. Open your Day Book repository on github.com.
3. Click the `Add file` button, then click `Upload files`.
4. Drag in `index.html`, `sw.js` and `leads.json` from the unzipped `devons-day-book` folder. Do not drag the `icons` folder or the other files again.
5. Under `Commit changes`, leave the default message and choose `Commit directly to the main branch`, then click the green `Commit changes` button.

## Part 2: Add the leads script

1. In the repository, click `Add file`, then click `Create new file`.
2. In the box named `Name your file...`, type: `automation/fetch_leads.py`
   (When you type the `/`, GitHub turns `automation` into a folder.)
3. Open `automation/fetch_leads.py` from this zip, select all of it, copy it, and paste it into the big text box.
4. Click the green `Commit changes...` button, then in the box that appears click `Commit changes` again.

## Part 3: Add the daily schedule

1. Click `Add file`, then `Create new file`.
2. In the `Name your file...` box, type: `.github/workflows/refresh-leads.yml`
3. Open `refresh-leads.yml` from this zip, copy all of it, and paste it into the big text box.
4. Click the green `Commit changes...` button, then click `Commit changes` again.

## Part 4: Run it once to test

1. Click the `Actions` tab at the top of the repository.
2. If GitHub shows a message asking you to enable workflows, click the green button to enable them.
3. In the left list, click `Refresh UGC leads`.
4. On the right, click the `Run workflow` drop-down, then click the green `Run workflow` button.
5. Wait about a minute and refresh the page. A green check mark means it worked. A red X means it failed: click the run, click `refresh`, and read the red line.
6. Go back to the `Code` tab. Click `leads.json`. It should show today's date and a list of items.
7. Open the Day Book on a phone, tap `UGC Desk`, and look for the `Fresh leads for you` card.

## If the run fails with a permissions error ("Permission denied" or 403)

1. Click `Settings` (top of the repository).
2. In the left column click `Actions`, then click `General`.
3. Scroll to the section called `Workflow permissions`.
4. Choose `Read and write permissions`.
5. Click `Save`.
6. Go back to `Actions`, click `Refresh UGC leads`, and run it again (Part 4, steps 3 to 5).

I could not open GitHub's help pages while building this, so the button names above are from memory and may be worded a little differently on your screen.

## If the app does not show the new leads after the run

GitHub's own Pages help page says: "Commits pushed by a GitHub Actions workflow that uses the `GITHUB_TOKEN` do not trigger a GitHub Pages build." So the new `leads.json` may not appear on your Pages site right away. Two things cover this:

1. The last step in the schedule file asks GitHub to rebuild Pages. I could not confirm that this step works on every account.
2. The app also reads `leads.json` straight from your repository (raw.githubusercontent.com) on its own, using your github.io address to work out your username and repository. This works when `leads.json` sits at the top level of the `main` (or `master`) branch. If you keep the app files in a subfolder, open the Day Book, go to `UGC Desk`, scroll to the bottom, open `Leads feed settings`, paste `https://raw.githubusercontent.com/YOUR-USERNAME/YOUR-REPOSITORY/main/FOLDER/leads.json` in the `Feed address (optional)` box, and tap `Save and refresh`.

## Things to know

- The schedule runs once a day at about 6:17 AM Central.
- The script reads public pages and feeds (Pitchlo's UGC jobs page, Remote OK, Himalayas, and the Mom Creators newsletter). It sends one request to each, once a day, and every lead links back to its source.
- Pitchlo's page layout could not be inspected while building this, so the first run is the real test. If `leads.json` shows no Pitchlo items, tell me and I will adjust the script.
- GitHub can pause scheduled runs in a repository that has had no activity for a long time. If new leads stop appearing, open the `Actions` tab and re-enable the workflow.
- Check Pitchlo's and each source's terms before relying on this long term.
