import unittest
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class Group3GroundingTests(unittest.TestCase):
    def test_b1_contains_grounded_term_boundaries_and_special_chars(self):
        from routers.optimizer import _contains_grounded_term
        # False substring matches must NOT match
        self.assertFalse(_contains_grounded_term("digital transformation expert", "git"))
        self.assertFalse(_contains_grounded_term("draws wireframes", "aws"))
        self.assertFalse(_contains_grounded_term("interested in cloud systems", "rest"))
        self.assertFalse(_contains_grounded_term("expert in javascript programming", "java"))
        self.assertFalse(_contains_grounded_term("maintain cloud infrastructure", "ai"))

        # Genuine matches with special symbols MUST still match
        self.assertTrue(_contains_grounded_term("Proficient in C++ and Python", "C++"))
        self.assertTrue(_contains_grounded_term("Developed services in C# and .NET", "C#"))
        self.assertTrue(_contains_grounded_term("Built APIs on .NET framework", ".NET"))
        self.assertTrue(_contains_grounded_term("Backend engineer with Node.js experience", "Node.js"))
        self.assertTrue(_contains_grounded_term("Maintained CI/CD pipelines", "CI/CD"))
        self.assertTrue(_contains_grounded_term("Machine learning with scikit-learn", "scikit-learn"))

    def test_b2_second_year_summary_no_false_internship_or_cs(self):
        from services.resume_structure import parse_source_resume
        from routers.optimizer import _build_skills_education_summary
        text = (FIXTURES / "resume_second_year_student.txt").read_text(encoding="utf-8")
        doc = parse_source_resume(text)
        summary = _build_skills_education_summary(text, {}, doc=doc)
        lowered = summary.lower()
        self.assertNotIn("internship", lowered)
        self.assertNotIn("graduate", lowered)
        self.assertNotIn("computer science", lowered)

    def test_b4_claim_verb_guard_scoped_to_bullet(self):
        from routers.optimizer import _validate_optimized_structure
        from services.resume_structure import parse_source_resume
        raw = (
            "Alex\n"
            "alex@example.com\n"
            "Experience\n"
            "Acme Corp\n"
            "Engineer  Jan 2023 - Present\n"
            "- Spearheaded frontend architecture and led weekly team standups.\n"
            "- Managed database migrations across environments.\n"
        )
        doc = parse_source_resume(raw)
        b1_id = doc.experience[0].bullets[0].source_id
        b2_id = doc.experience[0].bullets[1].source_id
        # Bullet 2 rewrite adds "led" which was in bullet 1, but NOT in bullet 2
        rewrites = {
            b1_id: doc.experience[0].bullets[0].original,
            b2_id: "Led database migrations across environments.",
        }
        res = _validate_optimized_structure(doc, {"bullet_rewrites": rewrites})
        # Bullet 2 should be reverted to original because "led" was not in bullet 2's source
        self.assertEqual(res["bullet_rewrites"][b2_id], doc.experience[0].bullets[1].original)

    def test_b6_hedges_preserved_in_quantifiers(self):
        from routers.optimizer import _clean_quantifiers
        text1 = _clean_quantifiers("Served ~500 users concurrently.")
        self.assertTrue("~500" in text1 or "about 500" in text1)
        text2 = _clean_quantifiers("Scaled to approximately 40 services.")
        self.assertTrue("approximately 40" in text2 or "about 40" in text2)

    def test_b8_preserve_domain_nouns_deleted_no_hallucinated_customer(self):
        import routers.optimizer as opt
        self.assertFalse(hasattr(opt, "_preserve_domain_nouns"))

    def test_b9_common_tech_canonical_no_added_prefixes(self):
        from services.resume_structure import COMMON_TECH_CANONICAL
        self.assertNotEqual(COMMON_TECH_CANONICAL.get("spark"), "Apache Spark")
        self.assertNotEqual(COMMON_TECH_CANONICAL.get("kafka"), "Apache Kafka")
        self.assertNotEqual(COMMON_TECH_CANONICAL.get("resnet"), "ResNet-50")

    def test_b11_optimizer_ml_markers_boundary_matching(self):
        from routers.optimizer import _has_ml_markers
        self.assertFalse(_has_ml_markers("Managed student enrollment database"))
        self.assertFalse(_has_ml_markers("Robert Half recruiter contact"))
        self.assertFalse(_has_ml_markers("Albert Einstein scholarship"))
        self.assertTrue(_has_ml_markers("Trained LLM models on GPU clusters"))
        self.assertTrue(_has_ml_markers("Fine-tuned BERT embeddings"))
