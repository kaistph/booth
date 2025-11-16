# Deploying Kultura Quest with the SQLite backend

The booth tracker now relies on the Python server (`server.py`) to read and write
registrations plus booth completions into `kultura.db`. Use the steps below to
run it locally or point a hosted front end (e.g., GitHub Pages) at the same API
so every browser shares the same records.

## Local testing
1. Install Python 3.9+.
2. From the repo root, run `python server.py`.
3. Open `http://localhost:8000` in any browser. The same origin serves both the
   static files and the JSON API, so no extra configuration is required.
4. Stop and restart the process whenever you need—the `kultura.db` file keeps
   everyone’s progress until you delete it manually.

## Hosting the API elsewhere
If you deploy `server.py` on a public host (Render, Railway, Fly.io, a VPS, etc.)
you can keep your static site on GitHub Pages and simply point the browser to the
remote API:

1. Deploy the Python server and note its base URL (for example,
   `https://kultura-api.example.com`).
2. Open the front end and append `?api=https://kultura-api.example.com` to the
   URL once. The page stores that base URL in `localStorage`, cleans up the query
   string, and uses it for all future requests in that browser.
3. Repeat step 2 in each browser/device that needs to talk to the hosted API.

### Alternate configuration methods
If you prefer a hard-coded base URL, define it before `index.html` loads the main
script—for example:

```html
<script>
  window.KULTURA_API_BASE = 'https://kultura-api.example.com';
</script>
```

You can also clear or change the stored API base by removing the
`kulturaApiBase` entry from `localStorage` and reloading with a new `?api=`
parameter.
