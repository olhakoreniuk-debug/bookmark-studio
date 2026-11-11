# Bookmark Studio

Bookmark Studio is a private bookmark library with a plain HTML/CSS/JavaScript frontend and a Python backend. Production uses PostgreSQL; local development can fall back to SQLite.

## Structure

```text
bookmark-studio/
├── frontend/   # current application interface
└── backend/    # Python JSON API, PostgreSQL config and Dockerfile
```

## What works

- add a URL with a link preview;
- manually edit the title, description and optional cover image;
- add a private note and tags;
- save bookmarks through an API in PostgreSQL (or local SQLite during development);
- keep `localStorage` as an offline fallback and synchronize it with the API;
- show each new card at the top of the library;
- responsive layout for mobile screens;
- a Barcelona demo card clearly marked as “Example”.

## Run locally

Open two PowerShell terminals in the repository.

Terminal 1 — backend and database:

```powershell
cd backend
python server.py
```

Terminal 2 — frontend:

```powershell
cd frontend
python -m http.server 8080
```

Then open [http://localhost:8080](http://localhost:8080). Stop the server with `Ctrl+C`.

You can also view the application by opening `frontend/index.html` directly in a browser.

## First-step scope

The backend currently runs without user accounts. Authentication, automatic metadata, search, filters and public pages remain outside this prototype’s scope.
