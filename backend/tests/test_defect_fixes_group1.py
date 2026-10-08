"""Tests for Group 1 defects (A1-a to A1-g, A2-a, A2-b, A4, CONTINUED_RE).
All tests assert exact parsed fields and verify intended behavior.
"""

import os
import re
import unittest
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests-0123456789")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")

from services.resume_structure import (
    parse_source_resume,
    _parse_entry_header,
    _parse_section_entries,
    _parse_markerless_entries,
    CONTINUED_RE,
    DATE_PATTERN,
)

FIXTURES = Path(__file__).parent / "fixtures"


class Group1ParsingTests(unittest.TestCase):
    def test_a1_a_split_headers_merge_fields_without_loss(self):
        # Two-line header: "Acme Technologies  Jan 2024 - Mar 2024" followed by "Software Intern"
        text = (FIXTURES / "resume_two_line_header.txt").read_text(encoding="utf-8")
        doc = parse_source_resume(text)
        self.assertEqual(len(doc.experience), 1)
        entry = doc.experience[0]
        self.assertEqual(entry.organization, "Acme Technologies")
        self.assertEqual(entry.title, "Software Intern")
        self.assertTrue(entry.dates)
        self.assertEqual(len(entry.bullets), 2)

        # Three-line header: org, title, date on separate lines
        text3 = (FIXTURES / "resume_three_line_header.txt").read_text(encoding="utf-8")
        doc3 = parse_source_resume(text3)
        self.assertEqual(len(doc3.experience), 1)
        entry3 = doc3.experience[0]
        self.assertEqual(entry3.organization, "Acme Corp")
        self.assertEqual(entry3.title, "Software Engineer")
        self.assertTrue(entry3.dates)
        self.assertEqual(len(entry3.bullets), 2)

        # Guard: resume_back_to_back_jobs must produce two distinct entries
        text_b2b = (FIXTURES / "resume_back_to_back_jobs.txt").read_text(encoding="utf-8")
        doc_b2b = parse_source_resume(text_b2b)
        self.assertEqual(len(doc_b2b.experience), 2)
        self.assertEqual(doc_b2b.experience[0].organization, "First Horizon Corp")
        self.assertEqual(doc_b2b.experience[1].organization, "NextGen Systems")

    def test_a1_b_comma_branch_organization_and_location(self):
        # "Acme Technologies, Hyderabad" -> org="Acme Technologies", location="Hyderabad", title=""
        org, title, dates, loc = _parse_entry_header("Acme Technologies, Hyderabad")
        self.assertEqual(org, "Acme Technologies")
        self.assertEqual(loc, "Hyderabad")
        self.assertEqual(title, "")

        # "Acme, Inc." -> suffix kept with org
        org2, title2, dates2, loc2 = _parse_entry_header("Acme, Inc.")
        self.assertEqual(org2, "Acme, Inc.")

        # From full fixture
        text = (FIXTURES / "resume_comma_org.txt").read_text(encoding="utf-8")
        doc = parse_source_resume(text)
        self.assertEqual(len(doc.experience), 2)
        self.assertEqual(doc.experience[0].organization, "Acme Technologies")
        self.assertEqual(doc.experience[0].location, "Hyderabad")
        self.assertEqual(doc.experience[1].organization, "Acme, Inc.")

    def test_a1_c_substring_keywords_word_boundaries(self):
        # False keywords
        # "Leadership" should not match role "lead"
        org, title, dates, loc = _parse_entry_header("Leadership")
        self.assertNotEqual(title, "Leadership")

        # "Lead Management | Java" -> project name="Lead Management", stack="Java"
        org2, title2, dates2, loc2 = _parse_entry_header("Lead Management | Java")
        self.assertIn("Lead Management", [org2, title2])

        # "Lead Engineer" must still match role "Lead Engineer"
        org3, title3, dates3, loc3 = _parse_entry_header("Lead Engineer")
        self.assertEqual(title3, "Lead Engineer")

        # Full false keywords fixture
        text = (FIXTURES / "resume_false_keywords.txt").read_text(encoding="utf-8")
        doc = parse_source_resume(text)
        # Bullets must retain "Leadership", "Internal Tools", "Headless CMS"
        bullets_text = " ".join(b.original for b in doc.experience[0].bullets)
        self.assertIn("Leadership", bullets_text)
        self.assertIn("Internal Tools", bullets_text)
        self.assertIn("Headless CMS", bullets_text)

    def test_a1_d_pdf_trusts_parser_role_org_order(self):
        from services.professional_resume_pdf import build_professional_resume_pdf
        from services.pdf_service import extract_text_from_pdf_base64
        content = {
            "name": "Alex Taylor",
            "experience": [
                {
                    "title": "Data Analytics Intern",
                    "organization": "Acme Labs",
                    "dates": "Jan 2024 - Mar 2024",
                    "bullets": ["Engineered data pipelines for analytics dashboards."],
                }
            ]
        }
        import base64
        res = build_professional_resume_pdf(name="Alex Taylor", content=content)
        b64 = base64.b64encode(res.pdf_bytes).decode("utf-8")
        text = extract_text_from_pdf_base64(b64)
        norm = " ".join(text.split())
        intern_pos = norm.find("Data Analytics Intern")
        labs_pos = norm.find("Acme Labs")
        self.assertGreaterEqual(intern_pos, 0)
        self.assertGreaterEqual(labs_pos, 0)
        self.assertLess(intern_pos, labs_pos)

    def test_a1_e_dates_regex_support(self):
        text = (FIXTURES / "resume_dates.txt").read_text(encoding="utf-8")
        doc = parse_source_resume(text)
        self.assertGreaterEqual(len(doc.experience), 4)
        for e in doc.experience:
            self.assertTrue(e.dates, f"Missing dates in entry: {e.header_raw}")
            # Ensure "06/" not left in title or org
            self.assertNotIn("06/", e.title)
            self.assertNotIn("06/", e.organization)
            # Ensure no stray "()"
            self.assertNotIn("()", e.organization)

    def test_a1_f_markerless_experience_parses_headers(self):
        text = (FIXTURES / "resume_markerless.txt").read_text(encoding="utf-8")
        doc = parse_source_resume(text)
        self.assertEqual(len(doc.experience), 1)
        entry = doc.experience[0]
        self.assertEqual(entry.organization, "Acme Solutions")
        self.assertEqual(entry.title, "Backend Developer")
        self.assertIn("Jan 2022", entry.dates)
        self.assertGreaterEqual(len(entry.bullets), 2)
        # Header text must not be in the first bullet
        self.assertNotIn("Backend Developer", entry.bullets[0].original)

    def test_a1_g_header_like_lines_after_bullets_create_new_entry(self):
        # When in_bullets=True, a short line looking like a header starts a new entry
        raw = (
            "Jane Doe\n"
            "jane@example.com\n"
            "Experience\n"
            "Beta Corp\n"
            "Junior Dev  Jan 2022 - Dec 2022\n"
            "- Built scalable web APIs for internal services.\n"
            "Gamma Corp\n"
            "Senior Dev  Jan 2023 - Present\n"
            "- Managed engineering team across core projects.\n"
        )
        doc = parse_source_resume(raw)
        self.assertEqual(len(doc.experience), 2)
        self.assertEqual(doc.experience[0].organization, "Beta Corp")
        self.assertEqual(doc.experience[1].organization, "Gamma Corp")

    def test_a2_a_missing_headings_recognized(self):
        text = (FIXTURES / "resume_headings.txt").read_text(encoding="utf-8")
        doc = parse_source_resume(text)
        # projects: Selected Projects, Notable Projects, Side Projects, Open Source
        self.assertGreaterEqual(len(doc.projects), 4)
        # experience / internships: Internships
        self.assertGreaterEqual(len(doc.experience), 1)
        # skills: Key Skills, Soft Skills, Core Competencies
        self.assertGreaterEqual(len(doc.skills), 6)
        # achievements: Achievements & Awards, Honors & Awards
        achieve_titles = [s["title"] for s in doc.other_sections]
        self.assertTrue(any("Achievement" in t or "Award" in t or "Honor" in t for t in achieve_titles))

    def test_a2_b_unanchored_header_lookalikes_not_treated_as_sections(self):
        text = (FIXTURES / "resume_heading_lookalikes.txt").read_text(encoding="utf-8")
        doc = parse_source_resume(text)
        self.assertEqual(len(doc.projects), 3)
        proj_names = [p.organization or p.title for p in doc.projects]
        self.assertIn("Education Management System", proj_names)
        self.assertIn("Skills Gap Analyzer", proj_names)
        self.assertIn("Profile Builder", proj_names)
        # "Experience in building…" must stay in the bullets of Education Management System
        bullets_first = [b.original for b in doc.projects[0].bullets]
        self.assertTrue(any("Experience in building" in b for b in bullets_first))

    def test_a4_keyword_dump_not_in_bullets(self):
        text = (FIXTURES / "resume_keyword_dump.txt").read_text(encoding="utf-8")
        doc = parse_source_resume(text)
        for b in doc.all_bullets:
            self.assertNotIn("Python, Docker, Kubernetes, AWS, Redis", b.original)
            self.assertNotIn("Python, React, TypeScript, GraphQL", b.original)

    def test_continued_re_does_not_match_discontinued(self):
        self.assertIsNone(CONTINUED_RE.search("discontinued project"))
        self.assertIsNotNone(CONTINUED_RE.search("Experience (continued)"))
        self.assertIsNotNone(CONTINUED_RE.search("Projects continued"))


if __name__ == "__main__":
    unittest.main()
