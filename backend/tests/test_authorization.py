import unittest
import asyncio
from fastapi import HTTPException
from routers import resume, community


class _MockQuery:
    def __init__(self, store, table_name):
        self.store = store
        self.table_name = table_name
        self._filters = []
        self._action = "select"
        self._is_single = False

    def select(self, *cols):
        self._action = "select"
        return self

    def eq(self, col, val):
        self._filters.append((col, val))
        return self

    def limit(self, n):
        return self

    def order(self, *args, **kwargs):
        return self

    def single(self):
        self._is_single = True
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
            if self._is_single:
                class Result:
                    def __init__(self, d): self.data = d[0] if d else None
                return Result(matched)
            else:
                class Result:
                    def __init__(self, d): self.data = matched
                return Result(matched)

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
    def __init__(self, initial_data=None):
        self.store = initial_data or {}

    def table(self, name):
        return _MockQuery(self.store, name)


class AuthorizationIDORTests(unittest.TestCase):
    def setUp(self):
        self.original_resume_db = resume.supabase
        self.original_community_db = community.supabase

    def tearDown(self):
        resume.supabase = self.original_resume_db
        community.supabase = self.original_community_db

    def test_resume_analysis_idor_cross_user_blocked(self):
        """User B cannot fetch User A's resume analysis by analysis_id."""
        db = _MockSupabase({
            "resume_analyses": [
                {"id": "analysis-1", "user_id": "user-a", "score": 85}
            ]
        })
        resume.supabase = db

        # User A fetches own analysis -> 200 OK
        user_a = {"user_id": "user-a", "email": "a@example.com"}
        res_a = asyncio.run(resume.get_analysis("analysis-1", user=user_a))
        self.assertTrue(res_a["success"])
        self.assertEqual(res_a["analysis"]["id"], "analysis-1")

        # User B attempts to fetch User A's analysis -> 404 Not Found
        user_b = {"user_id": "user-b", "email": "b@example.com"}
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(resume.get_analysis("analysis-1", user=user_b))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_community_post_delete_cross_user_forbidden(self):
        """User B cannot delete User A's community post."""
        db = _MockSupabase({
            "community_posts": [
                {"id": "post-1", "user_id": "user-a", "title": "Post 1"}
            ]
        })
        community.supabase = db

        # User B attempts delete -> 403 Forbidden
        user_b = {"user_id": "user-b", "email": "b@example.com"}
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(community.delete_post("post-1", user=user_b))
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(len(db.store["community_posts"]), 1)

        # User A deletes own post -> success
        user_a = {"user_id": "user-a", "email": "a@example.com"}
        res = asyncio.run(community.delete_post("post-1", user=user_a))
        self.assertTrue(res["success"])
        self.assertEqual(len(db.store["community_posts"]), 0)

    def test_community_comment_delete_cross_user_forbidden(self):
        """User B cannot delete User A's comment."""
        db = _MockSupabase({
            "post_comments": [
                {"id": "comment-1", "post_id": "post-1", "user_id": "user-a", "content": "Hello"}
            ],
            "community_posts": [
                {"id": "post-1", "comments_count": 1}
            ]
        })
        community.supabase = db

        # User B attempts delete -> 403 Forbidden
        user_b = {"user_id": "user-b", "email": "b@example.com"}
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(community.delete_comment("comment-1", user=user_b))
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(len(db.store["post_comments"]), 1)


if __name__ == "__main__":
    unittest.main()
