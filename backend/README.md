# Backend

The API uses PostgreSQL in production and keeps SQLite as a zero-configuration local fallback.

## Run

```powershell
cd backend
python server.py
```

Without `DATABASE_URL`, the API runs at `http://localhost:8000` and creates a local `bookmarks.db` automatically. The database file is private local data and is ignored by Git.

## PostgreSQL

Install the PostgreSQL driver and provide a connection URL:

```powershell
pip install -r requirements.txt
$env:DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/DATABASE"
python server.py
```

On Coolify, set these environment variables instead of writing secrets in the repository:

- `DATABASE_URL` — the PostgreSQL Internal URL from Coolify;
- `ALLOWED_ORIGIN` — the final Netlify frontend origin, such as `https://bookmark-studio.netlify.app`;
- `PORT` — optional; defaults to `8000`.

The included `Dockerfile` is the recommended Coolify deployment method.

## Endpoints

- `GET /api/health` — health check;
- `GET /api/bookmarks` — list bookmarks, newest first;
- `POST /api/bookmarks` — create or synchronize a bookmark.

User accounts remain intentionally reserved for a later stage.
