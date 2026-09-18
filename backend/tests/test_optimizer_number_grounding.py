import asyncio
import json
import sys
import types
import unittest


middleware_pkg = types.ModuleType("middleware")
middleware_pkg.__path__ = []
auth_module = types.ModuleType("middleware.auth")


class _FakeTable:
    def insert(self, _payload):
        return self

    def execute(self):
        return None


class _FakeSupabase:
    def table(self, _name):
        return _FakeTable()


async def _fake_authenticated_user():
    return {"user_id": "test-user"}


auth_module.get_authenticated_user = _fake_authenticated_user
database_module = types.ModuleType("database")
database_module.supabase = _FakeSupabase()
sys.modules.setdefault("middleware", middleware_pkg)
sys.modules.setdefault("middleware.auth", auth_module)
sys.modules.setdefault("database", database_module)

import routers.optimizer as optimizer  # noqa: E402
from routers.optimizer import (  # noqa: E402
    OptimizeRequest,
    _apply_optimizer_safety_filters,
    _audit_resume_numbers_against_source,
    _optimized_text_for_ats,
    optimize_resume,
)


class OptimizerNumberGroundingTests(unittest.TestCase):
    def test_reverts_or_removes_generated_numbers_not_in_source(self):
        resume_text = (
            "Kasanagottu Karthik\n"
            "Projects\n"
            "- Built Gmail automation with Gemini API, processing 100+ emails per day.\n"
            "- Created a parking management system in C, managing ~50 parking slots and ~100 vehicle records.\n"
            "Skills: Python, C, Gmail API, Gemini API, OAuth 2.0\n"
        )
        result = {
            "optimized_summary": "Processed 500 emails per run by optimizing backend systems.",
            "optimized_skills": {
                "Languages": ["Python", "C"],
                "Tools": ["Gmail API", "Gemini API", "OAuth 2.0"],
            },
            "improved_bullets": [
                {
                    "original": "Built Gmail automation with Gemini API, processing 100+ emails per day.",
                    "improved": "Automated Gmail API workflow with Gemini API, processing 500 emails per run.",
                    "keywords_added": ["automation"],
                    "metric_added": "500 emails per run",
                    "improvement_reason": "Added processing scale.",
                },
                {
                    "original": "Created a parking management system in C, managing ~50 parking slots and ~100 vehicle records.",
                    "improved": "Developed C parking management system, managing 100 parking slots.",
                    "keywords_added": ["parking management"],
                    "metric_added": "100 parking slots",
                    "improvement_reason": "Focused scale claim.",
                },
            ],
            "new_bullets": [
                {
                    "text": "Streamlined Gmail API processing for 250 tickets per run.",
                    "reason": "JD requires workflow automation.",
                    "jd_requirement": "workflow automation",
                }
            ],
            "added_keywords": ["workflow automation"],
            "missing_keywords": [],
            "improvement_explanation": {
                "metrics_added": ["500 emails per run", "100 parking slots"],
                "sections_improved": ["Bullets rewritten with source-only metrics"],
            },
            "ats_tips": ["Avoid adding 250 tickets unless it appears in the resume."],
            "overall_improvement": "Removed fabricated 500-email scale.",
            "match_score_estimate": 72,
            "confidence_level": "Medium",
        }

        validated = _apply_optimizer_safety_filters(
            result,
            resume_text,
            "workflow automation with Gmail API and parking management systems",
            "Automation Developer",
            "test-user",
        )
        optimized_text = _optimized_text_for_ats(validated)

        self.assertIn("processing 100+ emails per day", optimized_text)
        self.assertNotIn("500", optimized_text)
        self.assertNotIn("per run", optimized_text)
        self.assertIn("~50 parking slots", optimized_text)
        self.assertIn("~100 vehicle records", optimized_text)
        self.assertNotIn("managing 100 parking slots", optimized_text)
        self.assertNotIn("250", optimized_text)
        self.assertEqual(validated["new_bullets"], [])
        self.assertTrue(validated["number_grounding_applied"])
        self.assertNotIn("match_score_estimate", validated)
        self.assertNotIn("confidence_level", validated)

        rows = _audit_resume_numbers_against_source(validated, resume_text)
        self.assertTrue(rows)
        self.assertTrue(all(row["appears_in_source"] == "yes" for row in rows))
        self.assertIn({"number": "2.0", "appears_in_source": "yes"}, rows)

    def test_endpoint_reverts_known_fabricated_metrics(self):
        resume_text = (
            "Kasanagottu Karthik\n"
            "Skills: Python, C, Gmail API, OAuth 2.0\n"
            "Projects\n"
            "- Designed to read, analyze, and reply to emails automatically, processing 100+ emails per day.\n"
            "- Automated parking slot allocation and vehicle record management, managing ~50 parking slots and ~100 vehicle records.\n"
        )
        model_result = {
            "optimized_summary": "Processed 500 emails per run by optimizing backend systems.",
            "optimized_skills": {"Tools": ["Gmail API", "OAuth 2.0"]},
            "improved_bullets": [
                {
                    "original": "Designed to read, analyze, and reply to emails automatically, processing 100+ emails per day.",
                    "improved": "Automated Gmail workflow, processing 500 emails per run.",
                    "metric_added": "500 emails per run",
                },
                {
                    "original": "Automated parking slot allocation and vehicle record management, managing ~50 parking slots and ~100 vehicle records.",
                    "improved": "Developed a parking system, managing 100 parking slots.",
                    "metric_added": "100 parking slots",
                },
            ],
            "new_bullets": [{"text": "Streamlined Gmail processing for 250 tickets per run."}],
            "improvement_explanation": {"metrics_added": ["500 emails per run"]},
            "ats_tips": ["Add 250 tickets to demonstrate scale."],
            "match_score_estimate": 72,
            "confidence_level": "Medium",
        }

        async def fabricated_call(_messages, **_kwargs):
            return json.dumps(model_result)

        original_call = optimizer.call_groq
        original_supabase = optimizer.supabase
        optimizer.call_groq = fabricated_call
        optimizer.supabase = _FakeSupabase()
        try:
            response = asyncio.run(optimize_resume(
                OptimizeRequest(
                    resume_text=resume_text,
                    job_description="Python Gmail API workflow automation",
                    job_title="Automation Developer",
                ),
                user={"user_id": "number-grounding-e2e"},
            ))
        finally:
            optimizer.call_groq = original_call
            optimizer.supabase = original_supabase

        result = response["optimization"]
        optimized_text = _optimized_text_for_ats(result)
        self.assertNotIn("500", optimized_text)
        self.assertNotIn("per run", optimized_text.lower())
        self.assertIn("processing 100+ emails per day", optimized_text)
        self.assertIn("managing ~50 parking slots", optimized_text)
        self.assertIn("~100 vehicle records", optimized_text)
        self.assertNotIn("managing 100 parking slots", optimized_text)
        self.assertTrue(result["number_grounding_applied"])
        self.assertNotIn("match_score_estimate", result)
        self.assertTrue(all(
            row["appears_in_source"] == "yes"
            for row in _audit_resume_numbers_against_source(result, resume_text)
        ))


if __name__ == "__main__":
    unittest.main()
