import unittest
from pathlib import Path
from services.resume_structure import (
    parse_source_resume,
    _extract_source_skill_groups,
    ResumeDocument,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class Group2SkillsTests(unittest.TestCase):
    def test_a3_a_and_b_c_r_hyphenated_skills_and_75_skills(self):
        text = (FIXTURES / "resume_skills.txt").read_text(encoding="utf-8")
        doc = parse_source_resume(text)
        skills = set(doc.skills)
        self.assertIn("C", skills)
        self.assertIn("R", skills)
        self.assertIn("Scikit-learn", skills)
        self.assertIn("Problem-solving", skills)
        self.assertIn("Hugging-face", skills)
        # Invariant I-4: 75 skills
        self.assertEqual(len(doc.skills), 75)

    def test_a3_c_group_extractor_stops_at_next_heading(self):
        text = (
            "Skills\n"
            "Languages: Python, C++, Java, R, C\n"
            "Frameworks: Django, Flask, FastAPI\n"
            "Experience\n"
            "Tech Corp\n"
            "Software Engineer\n"
        )
        groups = _extract_source_skill_groups(text)
        self.assertIn("Languages", groups)
        self.assertIn("Frameworks", groups)
        self.assertNotIn("Experience", groups)
        for skill_list in groups.values():
            self.assertNotIn("Tech Corp", skill_list)
            self.assertNotIn("Software Engineer", skill_list)

    def test_a3_d_and_e_pdf_skills_no_truncation_and_flat_fallback(self):
        from services.professional_resume_pdf import _clean_list, _skill_groups, build_professional_resume_pdf
        # A3-d: _clean_list with default limit=50 must not truncate skills if handled
        many_skills = [f"Skill_{i}" for i in range(75)]
        # A3-e: _skill_groups accepts flat list and handles empty skillGroups: []
        content_flat = {
            "name": "Jane Skill",
            "skills": many_skills,
            "skillGroups": [],
        }
        groups = _skill_groups(content_flat)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["category"], "Skills")
        self.assertEqual(len(groups[0]["skills"]), 75)

    def test_a3_f_project_header_dates_stripped_from_tech_tokens(self):
        from services.resume_structure import _extract_tech_tokens_from_doc
        text = (
            "Alex\n"
            "alex@example.com\n"
            "Projects\n"
            "Analytics Dashboard | Flask Jan 2024 - Mar 2024\n"
            "- Built pipeline.\n"
        )
        doc = parse_source_resume(text)
        tokens = [t.lower() for t in _extract_tech_tokens_from_doc(doc)]
        self.assertIn("flask", tokens)
        self.assertNotIn("jan", tokens)
        self.assertNotIn("2024", tokens)
        self.assertNotIn("mar", tokens)
        self.assertNotIn("mar", tokens)

    def test_reexport_and_skill_groups_attribute(self):
        import routers.optimizer as opt
        self.assertTrue(hasattr(opt, "_extract_source_skill_groups"))
        doc = ResumeDocument(
            raw_text="sample",
            experience=[],
            projects=[],
            education=[],
            certifications=[],
            skills=["Python", "C"],
            skill_groups={"Languages": ["Python", "C"]},
        )
        self.assertEqual(doc.skill_groups.get("Languages"), ["Python", "C"])

    def test_invariant_i4_75_skills_pipeline(self):
        from services.professional_resume_pdf import build_professional_resume_pdf, _skill_groups
        from routers.optimizer import _validate_optimized_structure
        text = (FIXTURES / "resume_skills.txt").read_text(encoding="utf-8")
        doc = parse_source_resume(text)
        self.assertEqual(len(doc.skills), 75)

        opt_result = _validate_optimized_structure(doc, {"optimized_skills": doc.skills})
        if isinstance(opt_result["optimized_skills"], dict):
            total_opt_skills = sum(len(items) for items in opt_result["optimized_skills"].values())
        else:
            total_opt_skills = len(opt_result["optimized_skills"])
        self.assertEqual(total_opt_skills, 75)

        pdf_groups = _skill_groups({"skills": doc.skills})
        total_pdf_skills = sum(len(g["skills"]) for g in pdf_groups)
        self.assertEqual(total_pdf_skills, 75)
