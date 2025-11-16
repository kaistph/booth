# Running the shared SQLite API with Docker

Use the included `Dockerfile` and `docker-compose.yml` when you want one
centralized Kultura Quest API that every browser can reach. The container exposes
port `8000` and stores the SQLite file inside a bind-mounted `data/` folder so
you can redeploy without losing registrations.

## Requirements
- Docker Desktop or any compatible Docker Engine
- (Optional) docker-compose v2 for the helper commands below

## Quick start
```bash
# Build and start the API
docker compose up --build

# Visit the server locally
open http://localhost:8000
```

Because the compose file mounts `./data` into the container at `/data`, every
restart keeps the exact same `kultura.db`. Copy or back up `data/kultura.db`
whenever you need an off-site snapshot.

## Deploying remotely
On a VPS or cloud host, run the same `docker compose up --build -d` command.
Make sure you open port `8000` (or change the published port in
`docker-compose.yml`). Any front-end that uses the resulting public URL—either
through the `?api=` query parameter or the “Change server” button—will now share
the single SQLite database in `data/kultura.db`.
