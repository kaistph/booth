# Merge guidance

When resolving conflicts around the `<script>` block in `index.html`, keep the version that initializes the API helpers (`apiFetch`, `loadBooths`, `registerUser`, etc.) and talks to the Python server introduced in commit "Add SQLite backend and API". In VS Code's conflict UI, that's the **incoming change** from the feature branch (`codex/develop-event-registration-website-with-booths-3746ht`).

That version ensures the dashboard loads booth metadata from `/api/booths`, persists attendees to the SQLite database through `/api/register` and `/api/login`, and requires organizer passwords server-side before flipping booth status via `/api/booths/<id>/complete`. Accepting the older "current" block would revert to the localStorage-only implementation and break parity with `server.py`.

After accepting the incoming section, rerun the usual formatting checks (if any) and reload the page so it can fetch data from the Python backend.
