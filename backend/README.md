# Backend

The second prototype includes a small local JSON API backed by SQLite. It uses only Python’s standard library, so there are no packages to install.

## Run

```powershell
cd backend
python server.py
```

The API runs at `http://localhost:8000` and creates `bookmarks.db` automatically. The database file is private local data and is ignored by Git.

## Endpoints

- `GET /api/health` — health check;
- `GET /api/bookmarks` — list bookmarks, newest first;
- `POST /api/bookmarks` — create or synchronize a bookmark.

User accounts and remote deployment are intentionally reserved for a later stage.
