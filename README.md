# Bookmark Studio

The first prototype of a private bookmark library. It is a single responsive screen built with plain HTML, CSS and JavaScript, with no build step or dependencies.

## Structure

```text
bookmark-studio/
├── frontend/   # current application interface
└── backend/    # reserved for the future API and database
```

## What works

- add a URL with a link preview;
- manually edit the title, description and optional cover image;
- add a private note and tags;
- save bookmarks in browser `localStorage`;
- show each new card at the top of the library;
- responsive layout for mobile screens;
- a Barcelona demo card clearly marked as “Example”.

## Run locally

Open the frontend directory and start a local server:

```powershell
cd frontend
python -m http.server 8080
```

Then open [http://localhost:8080](http://localhost:8080). Stop the server with `Ctrl+C`.

You can also view the application by opening `frontend/index.html` directly in a browser.

## First-step scope

Data is currently stored only in the active browser. A backend, database, user accounts, automatic metadata, search, filters, public pages and deployment are outside this prototype’s scope.
