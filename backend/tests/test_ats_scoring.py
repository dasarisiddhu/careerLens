import unittest
from routers.resume import _apply_brutal_ats_scoring
from services.gemini_service import _calibrate_resume_scores, _fallback_ats_match


class ATSScoringTests(unittest.TestCase):
    def test_apply_brutal_ats_scoring_is_not_anchored_to_llm_score(self):
        """Authoritative deterministic scoring does not take inflated or deflated LLM score."""
        # Case 1: Model returned 100, but only 2 keywords matched and 6 skills missing -> capped below 40
        inflated_input = {
            "ats_score": 100,
            "matched_keywords": ["python", "sql"],
            "missing_keywords": ["docker", "k8s", "aws", "fastapi", "react", "redis"],
            "missing_skills": ["docker", "kubernetes", "aws", "fastapi", "react", "redis"],
        }
        res = _apply_brutal_ats_scoring(inflated_input)
        self.assertLessEqual(res["ats_score"], 39)

        # Case 2: Model returned 0, but candidate matches all keywords and has 0 missing skills -> deterministic high score
        deflated_input = {
            "ats_score": 0,
            "matched_keywords": ["python", "sql", "fastapi", "docker"],
            "missing_keywords": [],
            "missing_skills": [],
        }
        res = _apply_brutal_ats_scoring(deflated_input)
        self.assertGreaterEqual(res["ats_score"], 90)

    def test_calibrate_resume_scores_separates_readiness_from_job_match(self):
        """_calibrate_resume_scores produces distinct ats_readiness_score and job_match_score."""
        resume_text = """
        John Doe
        john@example.com
        Experience:
        - Built Python backend APIs handling 50,000 requests/day.
        - Deployed microservices using Docker.
        Skills: Python, Docker, PostgreSQL, REST APIs.
        Education: BS Computer Science.
        """
        result = {
            "score": 75,
            "skill_match_percentage": 80,
            "strengths": ["Strong backend experience"],
            "weaknesses": ["No cloud platform experience"],
            "missing_skills": ["AWS"],
            "top_keywords_missing": ["AWS", "Terraform"],
        }
        github_data = {"public_repos": 10, "total_stars": 15, "languages": {"Python": 1000}}

        calibrated = _calibrate_resume_scores(
            result=result,
            resume_text=resume_text,
            github_data=github_data,
            job_role="Backend Engineer",
        )

        self.assertIn("ats_readiness_score", calibrated)
        self.assertIn("job_match_score", calibrated)
        self.assertIn("ats_score", calibrated)
        self.assertEqual(calibrated["scoring_version"], "v2")
        self.assertIsInstance(calibrated["ats_readiness_score"], int)
        self.assertIsInstance(calibrated["job_match_score"], int)

    def test_fallback_ats_match_deterministic(self):
        """Deterministic fallback produces keyword matching and realistic scoring."""
        resume_text = "Python developer with experience in SQL, Git, and FastAPI."
        job_description = "Looking for a Python engineer skilled in SQL, Docker, Kubernetes, and AWS."

        res = _fallback_ats_match(resume_text, job_description)
        self.assertIn("python", res["matched_keywords"])
        self.assertIn("sql", res["matched_keywords"])
        self.assertIn("docker", res["missing_skills"])
        self.assertGreater(res["ats_score"], 0)
        self.assertLess(res["ats_score"], 100)


if __name__ == "__main__":
    unittest.main()
