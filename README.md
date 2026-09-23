# FollowScope

FollowScope is a local-first Instagram follower/following history tracker. It collects profile lists, stores timestamped snapshots in SQLite, compares complete snapshots, and provides a local result report.

## Use the portable release (recommended)

Download the `FollowScope-1.0.0-windows` release folder and keep its files together. It contains the extension files and four packaged Windows executables, so users do not need to install Python or any other runtime.

1. Open Edge or Chrome's extensions page (`edge://extensions` or `chrome://extensions`).
2. Enable **Developer mode**.
3. Choose **Load unpacked** and select the downloaded release folder.
4. Open Instagram and log in normally.
5. Double-click `run_server.bat` in the same release folder. Keep its window open while collecting.
6. Navigate to the Instagram profile and click **Start collection** in FollowScope.
7. Click **Stop** if needed. Everything collected before stopping is saved as a partial snapshot.
8. Double-click `result.bat` later to view changes or create a CSV report.

The database and token are stored in `Desktop\Instagram Exporter Data`, not in the browser or the release folder.

### The only scripts users need

- `run_server.bat`: start FollowScope's private local database service. Leave its window open while collecting.
- `result.bat`: open the latest totals and follower/following changes. It can optionally create a CSV report.
- `clear_database.bat`: permanently erase all saved data after a password and confirmation.

Users do not need to open Command Prompt or type commands. The extension itself is loaded once through the browser's **Load unpacked** button; after that, normal use is only opening `run_server.bat`, clicking **Start collection**, and later opening `result.bat`.

## Development mode (maintainers only)

1. Open the browser's extensions page.
2. Enable Developer mode.
3. Choose **Load unpacked**.
4. Select this `instagram-exporter` folder.
5. Open Instagram and log in normally.
6. Install Python 3 only for development, then double-click [run_server.bat](./run_server.bat). It creates `Desktop\Instagram Exporter Data` automatically, creates a persistent local authentication token once, and starts the SQLite service.
7. Navigate to the profile you want to monitor.
8. Open the extension popup and click **Start collection**. It opens Followers, collects the complete rendered list, closes it, opens Following, and collects that list.
9. Run **Start collection** again later to create a new complete snapshot. Use **Stop** at any time; collected data is saved as a partial snapshot.

Keep the server window open while using the extension. Close it when finished. Run the batch file once before loading the unpacked extension so it can generate `config.js`; after that, restarting the server does not require an extension reload because the token is persistent. The launcher validates and repairs the token automatically. The database is stored in the desktop data folder, not in the browser and not in the GitHub project.

### Clearing all database data

To permanently clear every profile, collection, username, and change:

1. Stop `run_server.bat`.
2. Double-click [clear_database.bat](./clear_database.bat).
3. The first run asks you to create a clear password twice.
4. Type `CLEAR` to confirm deletion.
5. Future runs require that password.

Only a salted PBKDF2 password hash is stored in `clear-password.txt`; the password itself is never stored. If the password is forgotten, delete `clear-password.txt` and create a new one. This does not recover deleted data.

### Viewing results

Double-click [result.bat](./result.bat) after a collection. It shows the latest profile totals, collection datetime, new accounts, and removed accounts. It can optionally print their usernames and create an Excel-compatible UTF-8 CSV report. The extension popup intentionally contains only **Start collection**, **Stop**, status/error messages, and **Feedback / suggestions**. Use `result.bat` for reports and `clear_database.bat` for administration.

## Report output

The result utility displays totals and changes and can create an Excel-compatible CSV with usernames and timestamps.

## Local SQLite backend

Collection data is stored by a local Python service in `Desktop\Instagram Exporter Data\instagram.db`; no browser storage is used by the backend. Start it before collecting:

For a manual start, run `py -3 server.py`. For normal use, double-click [run_server.bat](./run_server.bat). The batch files automatically use packaged `.exe` files when present and only fall back to Python in a source checkout.

## Maintainer commands, in order

End users do not need these commands. They are only for building and publishing a new release.

1. Install Python 3.13 or newer.
2. Run `py -3 -m pip install -r requirements-build.txt` — installs PyInstaller, which bundles Python into standalone `.exe` files.
3. Run `py -3 build_release.py` — creates the portable folder under `release\FollowScope-1.0.0-windows`.
4. Zip that folder without changing its internal layout — this is the file to attach to a GitHub Release.
5. `git add .` — stages source changes, never generated private data.
6. `git commit -m "Release FollowScope 1.0.0"` — records the changes locally.
7. `git push` — publishes the current branch to GitHub.

The build creates `followscope-launcher.exe`, `followscope-server.exe`, `followscope-result.exe`, and `followscope-clear-database.exe`. PyInstaller bundles the Python runtime and standard-library dependencies into those executables.

## Finding FollowScope on GitHub

The repository is:

`https://github.com/xxkyser-ctrl/FollowScope`

Someone who does not know the project name can search GitHub for terms such as:

- `Instagram follower tracker`
- `Instagram following changes`
- `SQLite Instagram exporter`
- `local Instagram follower history`
- `Chrome extension Instagram followers`

For best discoverability, set the repository description to:

`Privacy-first local Instagram follower and following history tracker with SQLite, change detection, and a Chrome/Edge extension.`

Recommended repository topics:

`instagram`, `instagram-extension`, `follower-tracker`, `following-tracker`, `social-graph`, `sqlite`, `chrome-extension`, `edge-extension`, `python`, `privacy`

To set these on GitHub: open the repository, choose **Settings**, edit the **Description**, and add the topics in the **Topics** field. Users can then find the project by searching those phrases or topics.

The service listens only on `127.0.0.1:8765`, configured by generated `config.js`. Use [config.template.js](./config.template.js) as the publishable template. The database path can be changed with `--db path\to\file.db` (or `INSTAGRAM_DB`). Check that it is running with `GET /api/health`. The authenticated extension API uses `POST /api/collections`, `GET /api/collections/history`, and `DELETE /api/collections?profile=...`.

Every Instagram profile is an independent database group. The profile username is taken from the active Instagram URL, so the same database can safely contain collections from multiple accounts without mixing their followers, following lists, totals, or changes.

The extension never asks for credentials, reads cookies, calls Instagram APIs, or sends data to a remote server.

## Security and privacy

- The server binds to loopback only and requires a random bearer token for every data operation.
- The token is generated locally by `run_server.bat` and stored in ignored `config.js`; it is never committed.
- Browser-origin requests are rejected. CORS is not wildcard-enabled.
- The extension exposes only fixed database operations; it cannot request arbitrary local URLs.
- Timestamps are generated by the local server, not accepted from the browser.
- SQLite and Excel files contain sensitive social-graph data. Keep the desktop data folder and exported workbooks private.
- Do not commit `config.js`, `instagram.db`, SQLite journal files, or `.xlsx` exports.
- The server token is kept in the desktop data folder in `server-token.txt`; protect that folder and delete it if you want to revoke the token. The launcher validates and repairs invalid token files automatically.
- See [SECURITY.md](./SECURITY.md) for the threat model, vulnerability reporting, and release checklist.

## Suggested project names

- **FollowScope** (recommended)
- **SocialPulse**
- **CircleTrack**
- **FollowLedger**
- **ProfileDelta**

## Notes

- Instagram must be displaying the profile page when **Start collection** is clicked.
- If Instagram is open in a tab from before the extension was installed, reload that Instagram tab once so Chrome injects the content script.
- The extension only collects usernames that Instagram renders in the dialogs; Instagram's loading, rate limits, or privacy restrictions can affect the result.
- A stopped collection is retained for inspection but is never used as the complete baseline for future comparisons.