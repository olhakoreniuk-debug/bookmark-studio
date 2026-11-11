import unittest
from pathlib import Path

import server


class BookmarkDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.original_database_path = server.DATABASE_PATH
        server.DATABASE_PATH = Path(__file__).with_name("test-bookmarks.db")
        server.DATABASE_PATH.unlink(missing_ok=True)
        server.initialize_database()

    def tearDown(self):
        server.DATABASE_PATH.unlink(missing_ok=True)
        server.DATABASE_PATH = self.original_database_path

    def test_create_list_and_update_without_duplicate(self):
        bookmark = server.validate_bookmark({
            "id": "saved-bookmark",
            "url": "https://example.com/article",
            "title": "First title",
            "description": "Description",
            "note": "Private note",
            "tags": ["test", "api"],
            "createdAt": 1700000000000,
        })
        server.upsert_bookmark(bookmark)
        bookmark["title"] = "Updated title"
        server.upsert_bookmark(bookmark)

        bookmarks = server.list_bookmarks()
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0]["title"], "Updated title")
        self.assertEqual(bookmarks[0]["tags"], ["test", "api"])

    def test_rejects_invalid_url_and_missing_title(self):
        with self.assertRaisesRegex(ValueError, "complete URL"):
            server.validate_bookmark({"url": "not-a-url", "title": "Title"})
        with self.assertRaisesRegex(ValueError, "title is required"):
            server.validate_bookmark({"url": "https://example.com", "title": ""})


if __name__ == "__main__":
    unittest.main()
