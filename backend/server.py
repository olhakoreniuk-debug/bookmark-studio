
#!/usr/bin/env python3
"""Bookmark Studio API with PostgreSQL and a local SQLite fallback."""

import json
import os
import sqlite3
import time
import uuid
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.environ.get(
        "ALLOWED_ORIGIN",
        "http://localhost:8080,http://127.0.0.1:5500,http://localhost:5500"
    ).split(",")
    if origin.strip()
}
DATABASE_PATH = Path(__file__).with_name("bookmarks.db")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
OWNER_GOOGLE_EMAIL = os.environ.get("OWNER_GOOGLE_EMAIL", "").strip().lower()


def connect_database():
    if DATABASE_URL:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as error:
            raise RuntimeError(
                "PostgreSQL support requires: pip install -r requirements.txt"
            ) from error
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def parameter_marker():
    return "%s" if DATABASE_URL else "?"


def initialize_database():
    with closing(connect_database()) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bookmarks (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                cover TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '[]',
                created_at BIGINT NOT NULL,
                category TEXT NOT NULL DEFAULT ''
            )
            """
        )

        if DATABASE_URL:
            connection.execute(
                "ALTER TABLE bookmarks "
                "ADD COLUMN IF NOT EXISTS category TEXT NOT NULL DEFAULT ''"
            )
        else:
            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(bookmarks)"
                )
            }
            if "category" not in columns:
                connection.execute(
                    "ALTER TABLE bookmarks "
                    "ADD COLUMN category TEXT NOT NULL DEFAULT ''"
                )


def row_to_bookmark(row):
    return {
        "id": row["id"],
        "url": row["url"],
        "title": row["title"],
        "description": row["description"],
        "cover": row["cover"],
        "note": row["note"],
        "tags": json.loads(row["tags"]),
        "createdAt": row["created_at"],
        "category": row["category"],
        "example": False,
    }


def list_bookmarks():
    with closing(connect_database()) as connection:
        rows = connection.execute(
            "SELECT * FROM bookmarks ORDER BY created_at DESC"
        ).fetchall()
    return [row_to_bookmark(row) for row in rows]


def upsert_bookmark(bookmark):
    markers = ", ".join([parameter_marker()] * 9)

    with closing(connect_database()) as connection, connection:
        connection.execute(
            f"""
            INSERT INTO bookmarks
                (id, url, title, description, cover, note,
                 tags, created_at, category)
            VALUES ({markers})
            ON CONFLICT(id) DO UPDATE SET
                url = excluded.url,
                title = excluded.title,
                description = excluded.description,
                cover = excluded.cover,
                note = excluded.note,
                tags = excluded.tags,
                created_at = excluded.created_at,
                category = excluded.category
            """,
            (
                bookmark["id"],
                bookmark["url"],
                bookmark["title"],
                bookmark["description"],
                bookmark["cover"],
                bookmark["note"],
                json.dumps(bookmark["tags"], ensure_ascii=False),
                bookmark["createdAt"],
                bookmark["category"],
            ),
        )


def validate_bookmark(payload):
    url = str(payload.get("url", "")).strip()
    title = str(payload.get("title", "")).strip()
    parsed_url = urlparse(url)

    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError(
            "Enter a complete URL using http:// or https://."
        )

    if not title:
        raise ValueError("A bookmark title is required.")

    raw_tags = payload.get("tags", [])

    if not isinstance(raw_tags, list):
        raise ValueError("Tags must be a list.")

    return {
        "id": str(payload.get("id") or uuid.uuid4()),
        "url": url,
        "title": title,
        "description": str(payload.get("description", "")).strip(),
        "cover": str(payload.get("cover", "")).strip(),
        "note": str(payload.get("note", "")).strip(),
        "tags": [
            str(tag).strip()
            for tag in raw_tags
            if str(tag).strip()
        ],
        "createdAt": int(
            payload.get("createdAt") or time.time() * 1000
        ),
        "category": str(payload.get("category") or "").strip(),
    }


class BookmarkHandler(BaseHTTPRequestHandler):

    def authorized(self):
        """Verify a Google ID token server-side and restrict access to the owner."""
        if not GOOGLE_CLIENT_ID or not OWNER_GOOGLE_EMAIL:
            self.send_json(503, {"error": "Google sign-in is not configured."})
            return False
        header = self.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            self.send_json(401, {"error": "Google sign-in required."})
            return False
        try:
            claims = id_token.verify_oauth2_token(
                header[7:].strip(), google_requests.Request(), GOOGLE_CLIENT_ID
            )
            if (claims.get("email", "").lower() != OWNER_GOOGLE_EMAIL
                    or claims.get("email_verified") is not True):
                self.send_json(403, {"error": "This account is not authorized."})
                return False
        except (ValueError, Exception):
            self.send_json(401, {"error": "Invalid or expired Google sign-in."})
            return False
        return True

    def end_headers(self):
        origin = self.headers.get("Origin")

        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, DELETE, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization"
        )
        super().end_headers()

    def send_json(self, status, payload):
        encoded = json.dumps(
            payload, ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if urlparse(self.path).path == "/api/health":
            with closing(connect_database()) as connection:
                connection.execute("SELECT 1").fetchone()

            self.send_json(200, {
                "status": "ok",
                "database": (
                    "postgresql" if DATABASE_URL else "sqlite"
                ),
            })
            return

        if urlparse(self.path).path != "/api/bookmarks":
            self.send_json(404, {"error": "Not found"})
            return

        if not self.authorized():
            return
        self.send_json(200, list_bookmarks())

    def do_POST(self):
        if urlparse(self.path).path != "/api/bookmarks":
            self.send_json(404, {"error": "Not found"})
            return

        if not self.authorized():
            return

        try:
            content_length = int(
                self.headers.get("Content-Length", "0")
            )

            if content_length > 1_000_000:
                self.send_json(
                    413, {"error": "Request is too large"}
                )
                return

            payload = json.loads(
                self.rfile.read(content_length) or b"{}"
            )
            bookmark = validate_bookmark(payload)

        except (json.JSONDecodeError, TypeError, ValueError) as error:
            self.send_json(400, {"error": str(error)})
            return

        upsert_bookmark(bookmark)
        self.send_json(201, {**bookmark, "example": False})

    def do_DELETE(self):
        if not self.authorized():
            return
        path = urlparse(self.path).path
        prefix = "/api/bookmarks/"
        bookmark_id = path[len(prefix):] if path.startswith(prefix) else ""
        if not bookmark_id or "/" in bookmark_id:
            self.send_json(404, {"error": "Not found"})
            return

        with closing(connect_database()) as connection, connection:
            cursor = connection.execute(
                f"DELETE FROM bookmarks WHERE id = {parameter_marker()}",
                (bookmark_id,),
            )
            deleted = cursor.rowcount

        if not deleted:
            self.send_json(404, {"error": "Bookmark not found"})
            return

        self.send_json(200, {"deleted": True, "id": bookmark_id})

    def log_message(self, message, *args):
        print(
            f"[{self.log_date_time_string()}] {message % args}"
        )


if __name__ == "__main__":
    initialize_database()

    server = ThreadingHTTPServer(
        (HOST, PORT),
        BookmarkHandler
    )

    print(
        f"Bookmark Studio API running at http://{HOST}:{PORT}"
    )
    print(
        f"Database: "
        f"{'PostgreSQL' if DATABASE_URL else 'SQLite (local fallback)'}"
    )
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAPI stopped.")
    finally:
        server.server_close()
