import unittest
from services.pdf_service import extract_text_from_pdf_base64
from routers.optimizer import (
    _summary_role,
    _summary_impact_method,
    _summary_metric_sentence,
    RECRUITER_DIMENSION_MAXES,
)

class DefectFixesGroup678Tests(unittest.TestCase):

    def test_e1_recruiter_dimensions_include_red_flag_free_and_alias(self):
        """E1: red_flag_free is canonical (max 20) and red_flag_penalty is alias."""
        self.assertIn("red_flag_free", RECRUITER_DIMENSION_MAXES)
        self.assertIn("red_flag_penalty", RECRUITER_DIMENSION_MAXES)
        self.assertEqual(RECRUITER_DIMENSION_MAXES["red_flag_free"], 20)
        self.assertEqual(RECRUITER_DIMENSION_MAXES["red_flag_penalty"], 20)

    def test_f2_base64_size_rejected_before_decoding(self):
        """F2: extract_text_from_pdf_base64 rejects oversized b64 before decoding."""
        from config import settings
        max_bytes = settings.MAX_RESUME_SIZE_MB * 1024 * 1024
        oversized_b64 = "A" * (int(max_bytes * 4 / 3) + 1000)
        with self.assertRaises(ValueError) as ctx:
            extract_text_from_pdf_base64(oversized_b64)
        self.assertIn("exceeds maximum limit", str(ctx.exception))

    def test_group8_summary_role_no_invented_ml_engineer(self):
        """Group 8: _summary_role does not invent ML engineer for general terms."""
        # General terms like "Research Assistant" or "Analyst" do not become "Machine Learning Engineer"
        role = _summary_role("Research Assistant")
        self.assertNotEqual(role, "Machine Learning Engineer")
        self.assertEqual(role, "Research Assistant")

    def test_group8_summary_impact_method_no_hardcoded_backend_for_frontend(self):
        """Group 8: _summary_impact_method does not claim backend systems for frontend work."""
        frontend_text = "Designed React UI components with Tailwind CSS."
        method = _summary_impact_method(frontend_text)
        self.assertNotIn("backend", method)
        self.assertIn("frontend", method)

        # Unmatched text returns empty string, avoiding invented causal claim
        unmatched_text = "Worked on documentation and team training."
        method_unmatched = _summary_impact_method(unmatched_text)
        self.assertEqual(method_unmatched, "")

    def test_group8_summary_metric_sentence_no_invented_causal_claim(self):
        """Group 8: _summary_metric_sentence does not add 'by optimizing backend systems' when ungrounded."""
        record = {
            "action": "Improved",
            "metric_value": "35%",
            "metric_type": "scale",
            "outcome": "team velocity",
            "source_text": "Improved team velocity 35% through weekly retrospectives.",
        }
        sentence = _summary_metric_sentence(record)
        self.assertNotIn("by optimizing backend systems", sentence)


if __name__ == "__main__":
    unittest.main()
