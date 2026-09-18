import unittest
from routers.resume import _truncation_flag, _RESUME_MAX_CHARS
from services.gemini_service import _validate_schema, REQUIRED_RESUME_FIELDS, RESUME_FIELD_DEFAULTS
from routers.optimizer import (
    _enforce_source_number_grounding,
    generate_structured_summary,
    _summary_role,
    SUMMARY_NOT_SUPPORTED,
)


class AIGroundingTests(unittest.TestCase):
    def test_truncation_detection(self):
        """Context truncation is correctly detected when input exceeds character limits."""
        short_text = "A" * 1000
        long_text = "A" * (_RESUME_MAX_CHARS + 500)

        self.assertFalse(_truncation_flag(short_text, _RESUME_MAX_CHARS))
        self.assertTrue(_truncation_flag(long_text, _RESUME_MAX_CHARS))

    def test_schema_validation_fills_defaults(self):
        """_validate_schema detects missing fields and applies safe defaults."""
        incomplete_model_output = {
            "score": 60,
            "strengths": ["Python"],
        }
        validated = _validate_schema(
            dict(incomplete_model_output),
            REQUIRED_RESUME_FIELDS,
            defaults=RESUME_FIELD_DEFAULTS,
        )

        for field in REQUIRED_RESUME_FIELDS:
            self.assertIn(field, validated)
            self.assertIsNotNone(validated[field])

    def test_optimizer_summary_never_fabricates_ml_engineer(self):
        """When number grounding fails on summary, it does not invent an ML Engineer persona."""
        source_resume = "Software developer with experience building Django websites."
        result = {
            # Model invented 500% increase which is absent from source
            "optimized_summary": "Machine Learning Engineer who drove 500% revenue increase.",
            "original_summary": "Software developer with experience building Django websites.",
            "improved_bullets": [],
            "new_bullets": [],
            "improvement_explanation": {},
            "ats_tips": [],
        }

        guarded = _enforce_source_number_grounding(
            result=result,
            resume_text=source_resume,
            user_id="test-user",
        )

        # Must NOT contain fabricated ML Engineer persona or ungrounded 500%
        self.assertNotIn("Machine Learning Engineer", guarded.get("optimized_summary", ""))
        self.assertNotIn("500%", guarded.get("optimized_summary", ""))
        # Should revert to original user summary
        self.assertEqual(guarded.get("optimized_summary"), "Software developer with experience building Django websites.")

    def test_generate_structured_summary_returns_sentinel_without_evidence(self):
        """When resume has no metrics, structured summary returns ADD_EVIDENCE_REQUIRED sentinel."""
        resume_text = "Frontend developer skilled in HTML, CSS, JavaScript."
        result = {"added_keywords": ["react"]}

        summary = generate_structured_summary(
            result=result,
            resume_text=resume_text,
            job_title="Frontend Engineer",
        )
        self.assertEqual(summary, SUMMARY_NOT_SUPPORTED)
        self.assertEqual(summary, "ADD_EVIDENCE_REQUIRED")

    def test_summary_role_defaults_safely(self):
        """Role derivation returns derived role or safe fallback, not hardcoded persona."""
        role = _summary_role("Frontend Developer")
        self.assertEqual(role, "Frontend Engineer")

        fallback_role = _summary_role("")
        self.assertEqual(fallback_role, "Software Engineer")


if __name__ == "__main__":
    unittest.main()
