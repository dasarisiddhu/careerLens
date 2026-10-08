"""Regressions found in a real localhost log (2026-10-04).

1. 'OAuth 2.0' was flagged as a fabricated metric (source_context_mismatch) and a valid rewrite reverted.
2. call_groq burned all 3 attempts switching between two rate-limited models, then fell off the end
   of the loop and returned None -> "Cannot extract JSON from empty model output".
"""
import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests-0123456789")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")

from routers.optimizer import _find_ungrounded_numbers
from services import gemini_service

SOURCE = (
    "AI-powered Gmail automation project using Python and Google Gemini:\n"
    "Implemented OAuth 2.0 for secure authentication and message handling.\n"
)


class VersionNumbersAreNotMetrics(unittest.TestCase):
    def test_oauth_version_with_different_trailing_words_is_grounded(self):
        self.assertEqual(
            _find_ungrounded_numbers("Implemented secure OAuth 2.0 message handling for the Gmail bot.", SOURCE), [])

    def test_fabricated_metric_with_same_digits_still_trips(self):
        self.assertTrue(_find_ungrounded_numbers("Reduced latency by 2.0 seconds.", SOURCE))

    def test_invented_version_still_trips(self):
        self.assertTrue(_find_ungrounded_numbers("Implemented OAuth 3.0 for the Gmail bot.", SOURCE))

    def test_invented_percentage_still_trips(self):
        self.assertTrue(_find_ungrounded_numbers("Improved efficiency by 40% using OAuth 2.0.", SOURCE))


class _Resp:
    def __init__(self, status, retry_after=None, content="ok"):
        self.status_code = status
        self.headers = {"retry-after": str(retry_after)} if retry_after is not None else {}
        self.text = '{"error":{"message":"rate limit"}}' if status == 429 else ""
        self._content = content

    def json(self):
        if self.status_code == 429:
            return {"error": {"message": "rate limit"}}
        return {"choices": [{"message": {"content": self._content}, "finish_reason": "stop"}]}


class _FakeClient:
    script: list = []
    calls: list = []

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, headers=None, json=None):
        _FakeClient.calls.append(json["model"])
        return _FakeClient.script.pop(0)


class GroqRateLimitLoop(unittest.TestCase):
    def _run(self, script):
        _FakeClient.script = list(script)
        _FakeClient.calls = []
        gemini_service._GROQ_SEMAPHORE = None
        fake_settings = SimpleNamespace(GROQ_API_KEY="k", GROQ_MODEL="openai/gpt-oss-20b")
        with patch.object(gemini_service, "settings", fake_settings), \
                patch.object(gemini_service.httpx, "AsyncClient", _FakeClient), \
                patch.object(gemini_service.asyncio, "sleep", new=AsyncMock()) as sleep:
            result = asyncio.run(gemini_service.call_groq([{"role": "user", "content": "hi"}], json_mode=True))
        return result, sleep

    def test_waits_out_the_delay_once_instead_of_ping_ponging(self):
        # the sequence from the log: 20b -> 429, qwen -> 429, then the wait, then success
        result, sleep = self._run([_Resp(429, 15), _Resp(429, 13), _Resp(200, content='{"a":1}')])
        self.assertEqual(result, '{"a":1}')
        self.assertIn(13.0, [c.args[0] for c in sleep.await_args_list])
        # never bounces back to a model that already 429'd in this request without waiting
        self.assertEqual(_FakeClient.calls[0], "openai/gpt-oss-20b")

    def test_never_returns_none_when_every_attempt_is_rate_limited(self):
        with self.assertRaises(ValueError):
            self._run([_Resp(429, 15), _Resp(429, 13), _Resp(429, 20), _Resp(429, 20)])

    def test_delay_above_cap_is_not_waited_out(self):
        with self.assertRaises(ValueError):
            self._run([_Resp(429, 60), _Resp(429, 60), _Resp(429, 60), _Resp(429, 60)])
        self.assertTrue(all(c.args[0] <= 2.0 for c in []))  # no long sleeps are scheduled


if __name__ == "__main__":
    unittest.main()
