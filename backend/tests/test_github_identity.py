import unittest
import asyncio
from fastapi import HTTPException
from routers import github_identity


class _MockQuery:
    def __init__(self, store, table_name):
        self.store = store
        self.table_name = table_name
        self._filters = []
        self._action = "select"
        self._insert_data = None
        self._update_data = None

    def select(self, *cols):
        self._action = "select"
        return self

    def eq(self, col, val):
        self._filters.append((col, val))
        return self

    def limit(self, n):
        return self

    def insert(self, data):
        self._action = "insert"
        self._insert_data = data
        return self

    def update(self, data):
        self._action = "update"
        self._update_data = data
        return self

    def delete(self):
        self._action = "delete"
        return self

    def execute(self):
        table = self.store.setdefault(self.table_name, [])
        if self._action == "select":
            matched = [
                row for row in table
                if all(row.get(col) == val for col, val in self._filters)
            ]
            class Result:
                def __init__(self, d): self.data = d
            return Result(matched)

        elif self._action == "insert":
            data = dict(self._insert_data)
            # Enforce unique constraints on github_identities
            if self.table_name == "github_identities":
                for r in table:
                    if r.get("careerlens_user_id") == data.get("careerlens_user_id"):
                        raise Exception("duplicate key value violates unique constraint idx_github_identities_user_id")
                    if r.get("github_user_id") == data.get("github_user_id"):
                        raise Exception("duplicate key value violates unique constraint idx_github_identities_github_user_id")
            table.append(data)
            class Result:
                def __init__(self, d): self.data = [d]
            return Result(data)

        elif self._action == "update":
            updated = []
            for r in table:
                if all(r.get(col) == val for col, val in self._filters):
                    r.update(self._update_data)
                    updated.append(r)
            class Result:
                def __init__(self, d): self.data = d
            return Result(updated)

        elif self._action == "delete":
            deleted = []
            remaining = []
            for r in table:
                if all(r.get(col) == val for col, val in self._filters):
                    deleted.append(r)
                else:
                    remaining.append(r)
            self.store[self.table_name] = remaining
            class Result:
                def __init__(self, d): self.data = d
            return Result(deleted)


class _MockSupabase:
    def __init__(self):
        self.store = {}

    def table(self, name):
        return _MockQuery(self.store, name)


class GitHubIdentityTests(unittest.TestCase):
    def setUp(self):
        self.mock_db = _MockSupabase()
        self.original_db = github_identity.supabase
        self.original_provider_fn = github_identity._get_github_provider_id_from_supabase
        github_identity.supabase = self.mock_db

    def tearDown(self):
        github_identity.supabase = self.original_db
        github_identity._get_github_provider_id_from_supabase = self.original_provider_fn

    def test_g001_first_link_success(self):
        """G001: First link of GitHub identity for a user succeeds."""
        github_identity._get_github_provider_id_from_supabase = lambda uid: ("12345", "octocat", "https://avatar.png")
        user = {"user_id": "user-a", "email": "a@example.com"}

        res = asyncio.run(github_identity.link_github_identity(user=user))
        self.assertTrue(res["success"])
        self.assertEqual(res["github_user_id"], "12345")
        self.assertEqual(res["github_login"], "octocat")
        self.assertEqual(len(self.mock_db.store["github_identities"]), 1)

    def test_g002_repeat_link_is_idempotent(self):
        """G002: Re-linking the same GitHub account for the same user is idempotent."""
        github_identity._get_github_provider_id_from_supabase = lambda uid: ("12345", "octocat", "https://avatar.png")
        user = {"user_id": "user-a", "email": "a@example.com"}

        res1 = asyncio.run(github_identity.link_github_identity(user=user))
        self.assertTrue(res1["success"])

        res2 = asyncio.run(github_identity.link_github_identity(user=user))
        self.assertTrue(res2["success"])
        self.assertIn("confirmed", res2["message"].lower())
        self.assertEqual(len(self.mock_db.store["github_identities"]), 1)

    def test_g003_user_b_cannot_claim_github_owned_by_user_a(self):
        """G003: User B cannot link GitHub account X already owned by User A."""
        github_identity._get_github_provider_id_from_supabase = lambda uid: ("12345", "octocat", "https://avatar.png")

        user_a = {"user_id": "user-a", "email": "a@example.com"}
        asyncio.run(github_identity.link_github_identity(user=user_a))

        user_b = {"user_id": "user-b", "email": "b@example.com"}
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(github_identity.link_github_identity(user=user_b))
        self.assertEqual(ctx.exception.status_code, 409)

    def test_g004_user_a_cannot_link_second_github(self):
        """G004: User A cannot link a second GitHub account without unlinking the first."""
        user_a = {"user_id": "user-a", "email": "a@example.com"}

        github_identity._get_github_provider_id_from_supabase = lambda uid: ("12345", "octocat", None)
        asyncio.run(github_identity.link_github_identity(user=user_a))

        github_identity._get_github_provider_id_from_supabase = lambda uid: ("67890", "second_octo", None)
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(github_identity.link_github_identity(user=user_a))
        self.assertEqual(ctx.exception.status_code, 409)

    def test_g008_username_change_preserves_identity(self):
        """G008: Changing GitHub username preserves identity and updates display login."""
        user = {"user_id": "user-a", "email": "a@example.com"}

        github_identity._get_github_provider_id_from_supabase = lambda uid: ("12345", "old_login", None)
        asyncio.run(github_identity.link_github_identity(user=user))

        # Username changed to new_login on GitHub, but numeric ID remains 12345
        github_identity._get_github_provider_id_from_supabase = lambda uid: ("12345", "new_login", None)
        res = asyncio.run(github_identity.link_github_identity(user=user))
        self.assertTrue(res["success"])
        self.assertEqual(res["github_login"], "new_login")
        self.assertEqual(self.mock_db.store["github_identities"][0]["github_login"], "new_login")

    def test_g010_unlink_removes_own_identity(self):
        """G010: Unlinking removes only the user'\''s own GitHub identity."""
        user = {"user_id": "user-a", "email": "a@example.com"}
        github_identity._get_github_provider_id_from_supabase = lambda uid: ("12345", "octocat", None)
        asyncio.run(github_identity.link_github_identity(user=user))

        res = asyncio.run(github_identity.unlink_github_identity(user=user))
        self.assertTrue(res["success"])
        self.assertEqual(len(self.mock_db.store["github_identities"]), 0)


if __name__ == "__main__":
    unittest.main()
