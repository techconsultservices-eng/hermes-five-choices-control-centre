# Hermes Five Choices Control Centre

A Windows-first Hermes dashboard with one general assistant and five focused specialists:

1. Tech Support
2. Web Search & Scrape
3. Image Creator
4. Teach Me
5. Grill Me

## GitHub Pages preview

The `web/` directory is deployed as a static visual preview. Navigation, colour schemes, pane resizing, and local browser state work on GitHub Pages.

Chat, profile health, and **Open Hermes Desktop** require the local Python companion and a configured Hermes runtime. Those features will show as unavailable in the Pages preview because credentials and profile routes deliberately remain server-side.

## Run locally

On Windows, with the required Hermes profiles and API configuration installed:

```bat
start_five_choices.bat
```

The companion serves the dashboard at `http://127.0.0.1:9335/` by default.

## Test

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The project also contains Windows packaging, installer, profile-distribution, runtime-provenance, and release-candidate verification material. Generated builds, operational state, credentials, local databases, logs, caches, and test homes are excluded from Git.

## Security and release status

- Profile API keys remain server-side and are not included in static assets.
- Do not commit `.env`, `auth.json`, live Hermes homes, sessions, databases, logs, or caches.
- Hermes Agent `0.20.6` is a provisional pinned candidate, not an approved public customer release.
- A signed public release remains blocked until code-signing and clean-Windows acceptance requirements are satisfied.

See `HERMES.md`, `REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md`, and `RELEASE_PROCESS.md` for the product rules and acceptance criteria.
