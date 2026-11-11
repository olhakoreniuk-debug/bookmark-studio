#!/usr/bin/env python3
"""Bookmark Studio local API using only the Python standard library."""

import json
import sqlite3
import time
import uuid
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


HOST = "127.0.0.1"
PORT = 8000
DATABASE_PATH = Path(__file__).with_name("bookmarks.db")


def connect_database():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


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
                created_at INTEGER NOT NULL
            )
            """
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
        "example": False,
    }


def list_bookmarks():
    with closing(connect_database()) as connection:
        rows = connection.execute(
            "SELECT * FROM bookmarks ORDER BY created_at DESC"
        ).fetchall()
    return [row_to_bookmark(row) for row in rows]


def upsert_bookmark(bookmark):
    with closing(connect_database()) as connection, connection:
        connection.execute(
            """
            INSERT INTO bookmarks
                (id, url, title, description, cover, note, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                url = excluded.url,
                title = excluded.title,
                description = excluded.description,
                cover = excluded.cover,
                note = excluded.note,
                tags = excluded.tags,
                created_at = excluded.created_at
            """,
            (
                bookmark["id"], bookmark["url"], bookmark["title"],
                bookmark["description"], bookmark["cover"], bookmark["note"],
                json.dumps(bookmark["tags"], ensure_ascii=False), bookmark["createdAt"],
            ),
        )


def validate_bookmark(payload):
    url = str(payload.get("url", "")).strip()
    title = str(payload.get("title", "")).strip()
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("Enter a complete URL using http:// or https://.")
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
        "tags": [str(tag).strip() for tag in raw_tags if str(tag).strip()],
        "createdAt": int(payload.get("createdAt") or time.time() * 1000),
    }


class BookmarkHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "http://localhost:8080")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def send_json(self, status, payload):
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            self.send_json(200, {"status": "ok"})
            return
        if self.path != "/api/bookmarks":
            self.send_json(404, {"error": "Not found"})
            return

        self.send_json(200, list_bookmarks())

    def do_POST(self):
        if self.path != "/api/bookmarks":
            self.send_json(404, {"error": "Not found"})
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length > 1_000_000:
                self.send_json(413, {"error": "Request is too large"})
                return
            payload = json.loads(self.rfile.read(content_length) or b"{}")
            bookmark = validate_bookmark(payload)
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            self.send_json(400, {"error": str(error)})
            return

        upsert_bookmark(bookmark)
        self.send_json(201, {**bookmark, "example": False})

    def log_message(self, message, *args):
        print(f"[{self.log_date_time_string()}] {message % args}")


if __name__ == "__main__":
    initialize_database()
    server = ThreadingHTTPServer((HOST, PORT), BookmarkHandler)
    print(f"Bookmark Studio API running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAPI stopped.")
    finally:
        server.server_close()
