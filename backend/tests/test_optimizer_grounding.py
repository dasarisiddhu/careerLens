import unittest
import sys
import types


middleware_pkg = types.ModuleType("middleware")
middleware_pkg.__path__ = []
auth_module = types.ModuleType("middleware.auth")


async def _fake_authenticated_user():
    return {"user_id": "test-user"}


auth_module.get_authenticated_user = _fake_authenticated_user
database_module = types.ModuleType("database")
database_module.supabase = None
sys.modules.setdefault("middleware", middleware_pkg)
sys.modules.setdefault("middleware.auth", auth_module)
sys.modules.setdefault("database", database_module)

from routers.optimizer import _stamp_ats_scores, _validate_against_source


class OptimizerGroundingTests(unittest.TestCase):
    def test_drops_skills_absent_from_resume_and_jd(self):
        result = {
            "optimized_skills": {
                "Frameworks": ["React", "Flask", "Angular", "Vue"],
                "Databases": ["MySQL", "PostgreSQL", "MongoDB", "SQLite"],
            },
            "skills_to_highlight": ["React", "Flask"],
            "added_keywords": ["MongoDB", "REST APIs"],
            "improved_bullets": [
                {
                    "original": "Built a parking management system.",
                    "improved": "Built Flask APIs with React dashboards handling 500+ emails/day.",
                    "keywords_added": ["React"],
                }
            ],
            "new_bullets": [
                {"text": "Managed 100+ parking slots and 500+ vehicle records with SQLite."}
            ],
        }
        resume_text = (
            "Karthik Rao\n"
            "Skills: Python, Flask, SQLite\n"
            "Project: Parking management system using Flask and SQLite.\n"
        )
        jd = "Build REST APIs using Flask."

        validated = _validate_against_source(result, resume_text, jd)

        self.assertEqual(validated["optimized_skills"]["Frameworks"], ["Flask"])
        self.assertEqual(validated["optimized_skills"]["Databases"], ["SQLite"])
        self.assertNotIn("React", validated["skills_to_highlight"])
        self.assertNotIn("MongoDB", validated["added_keywords"])
        self.assertIn("React", validated["dropped_ungrounded_skills"])
        self.assertIn("REST APIs", validated["jd_gap_fill_skills"])
        self.assertIn("~500 emails/day", validated["improved_bullets"][0]["improved"])
        self.assertIn("~100 parking slots", validated["new_bullets"][0]["text"])
        self.assertIn("~500 vehicle records", validated["new_bullets"][0]["text"])
        self.assertTrue(validated["grounding_warnings"])

    def test_stamps_ats_regression_flag(self):
        result = {
            "optimized_summary": "Python service.",
            "optimized_skills": ["Python"],
            "improved_bullets": [],
            "new_bullets": [],
            "added_keywords": [],
        }
        resume_text = "Python React Docker Kubernetes"
        jd = "Python React Docker Kubernetes"

        ats_before, ats_after = _stamp_ats_scores(result, resume_text, jd)

        self.assertLess(ats_after, ats_before)
        self.assertTrue(result["ats_regressed"])
        self.assertEqual(result["ats_before"], ats_before)
        self.assertEqual(result["ats_after"], ats_after)


if __name__ == "__main__":
    unittest.main()
