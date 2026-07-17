# DailyPlanner CI/CD and Docker

## Local Docker Run

Build and run the full app with Postgres:

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:8080
- Backend health: http://localhost:8000/health
- Backend docs: http://localhost:8000/docs

The local compose file starts Postgres with a persistent Docker volume named
`dailyplanner_postgres_data`.

## Production-Style Run

Use `docker-compose.prod.yml` when you already have a managed Postgres database:

```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

Required production env vars:

- `DATABASE_URL`
- `SECRET_KEY`
- `FRONTEND_URL`
- `CORS_ORIGINS`

Optional env vars:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`
- `GITHUB_REDIRECT_URI`
- `BACKEND_IMAGE`
- `FRONTEND_IMAGE`
- `BACKEND_PORT`
- `FRONTEND_PORT`

## GitHub Actions

The repo has two workflows:

- `ci.yml`: runs backend tests, frontend build, and Docker build checks.
- `docker-publish.yml`: publishes backend and frontend images to GitHub Container Registry on pushes to `main` and tags like `v1.0.0`.

Published image names:

- `ghcr.io/hamzakhyperlinkinfosystem-code/dailyplanner-backend`
- `ghcr.io/hamzakhyperlinkinfosystem-code/dailyplanner-frontend`

## End-of-Phase Checklist

At the end of each phase:

1. Run backend tests: `.venv/bin/python -m pytest`
2. Run frontend build: `npm run build --prefix frontend`
3. Build Docker images: `docker compose build`
4. Commit code to git.
5. Push to `main` to publish fresh `latest` Docker images.
6. Optionally create a phase tag, for example `v0.2.0`, to publish immutable versioned images.

The first real deployment target can be wired later once you pick the host
(Render, Railway, AWS ECS, Fly.io, a VPS, etc.).
