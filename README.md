# Devon's Day Book

A journal-style daily planner that installs on a phone like an app. Plain HTML, no build step, no server, no accounts.

## Files

| File | What it does |
| --- | --- |
| `index.html` | The whole app |
| `manifest.webmanifest` | Name, colors and icons for the home screen |
| `sw.js` | Lets the app open offline and pick up new versions |
| `icons/` | Home screen icons |

## Put it on GitHub Pages

1. Create a new repository and upload everything in this folder, keeping `icons/` as a folder.
2. In the repository, open Settings, then Pages.
3. Under Build and deployment, set Source to Deploy from a branch, choose `main` and the `/ (root)` folder, and save.
4. After a minute the site is live at `https://YOUR-USERNAME.github.io/YOUR-REPO/`. Send that link to Devon.

Every path in the app is relative, so it works from a repository subfolder like the one above without changes.

## Saving it to a phone

The app shows an install card the first time it opens in a browser.

- **iPhone:** open the link in Safari, tap Share, then Add to Home Screen, then Add. Do this before entering anything, because the home screen copy keeps its own storage separate from Safari.
- **Android:** open the link in Chrome and tap Install app on the card. If no card appears, use the three dot menu, then Install app or Add to Home screen.

## Updating it

Change `index.html`, commit and push. The app checks for a new copy each time it opens with a connection. Her saved data is not touched. If a change does not show up, bump `VERSION` in `sw.js` (this release is `daybook-v2`, so use `daybook-v3` next) and push again.

## Where the data lives

Everything Devon enters is saved in the browser storage on her phone. Nothing is sent anywhere. The Set up page has a backup and restore box for moving to a new phone.
