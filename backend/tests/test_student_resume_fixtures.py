"""Regression fixtures built from real student resumes (extracted with the app's own PDF reader).

student_markerless_resume.txt: no bullet markers, wrapped lines, an ACHIEVEMENTS section, 3 education
entries. This is what real fresher uploads look like, and it broke the parser (sections fused,
achievements absorbed into projects, invented "Relevant Experience" block).
ml_intern_resume.txt: clean marker-based resume, kept to prove the marker path is unchanged.
"""
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests-0123456789")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")

from services.professional_resume_pdf import build_professional_resume_pdf
from services.resume_structure import parse_source_resume, reconstruct_resume_structure

FIX = Path(__file__).parent / "fixtures"


def _load(name):
    return parse_source_resume((FIX / name).read_text(encoding="utf-8"))


class MarkerlessStudentResume(unittest.TestCase):
    def setUp(self):
        self.doc = _load("student_markerless_resume.txt")

    def test_no_experience_section_is_invented(self):
        self.assertEqual(self.doc.experience, [])

    def test_two_projects_with_bullets_not_one_fused_blob(self):
        names = [p.organization for p in self.doc.projects]
        self.assertEqual(names, ["AI-powered Gmail automation project using Python and Google Gemini",
                                 "Parking Management System"])
        self.assertEqual([len(p.bullets) for p in self.doc.projects], [4, 3])
        for p in self.doc.projects:
            for b in p.bullets:
                self.assertLessEqual(len(b.original.split()), 40)

    def test_achievements_preserved_verbatim_and_not_inside_projects(self):
        self.assertEqual([(s["title"], len(s["items"])) for s in self.doc.other_sections], [("Achievements", 3)])
        all_project_text = " ".join(b.original for p in self.doc.projects for b in p.bullets)
        self.assertNotIn("ACHIEVEMENTS", all_project_text)
        self.assertNotIn("Recognized for", all_project_text)

    def test_all_education_entries_and_grades_kept(self):
        joined = " ".join(self.doc.education)
        for token in ("6.5", "87%", "98%", "Alphores", "SPR School"):
            self.assertIn(token, joined)

    def test_rendered_pdf_has_no_invented_sections_and_keeps_everything(self):
        rec = reconstruct_resume_structure(doc=self.doc, bullet_rewrites={})
        pdf = build_professional_resume_pdf(
            name=self.doc.name, content={"reconstructed_resume": rec, "summary": self.doc.summary,
                                         "improvedBullets": ["Recognized for problem-solving"]},
            source_resume_text=self.doc.raw_text)
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(pdf.pdf_bytes if hasattr(pdf, "pdf_bytes") else pdf.content)
            f.flush()
            try:
                text = subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True).stdout
            except (FileNotFoundError, Exception):
                text = ""
        if not text:
            text = getattr(pdf, "extracted_text", "") or getattr(pdf, "visible_text", "")
        self.assertNotIn("Relevant Experience", text)
        self.assertNotRegex(text, r"Entry \d+")
        self.assertIsNone(re.search(r"^\s*EXPERIENCE\s*$", text, re.M | re.I))
        for token in ("Achievements", "Parking Management System", "6.5", "87%", "98%"):
            self.assertIn(token.lower(), text.lower())


class MarkerBasedResumeUnchanged(unittest.TestCase):
    def test_structure_and_skills_and_github(self):
        doc = _load("ml_intern_resume.txt")
        self.assertEqual([len(e.bullets) for e in doc.experience], [4])
        self.assertEqual([len(e.bullets) for e in doc.projects], [2, 2, 1])
        self.assertEqual(len(doc.skills), 17)  # a "Languages:" skills label must not split the section
        self.assertEqual(doc.github, "github.com/rohanverma-demo")
        self.assertEqual(doc.other_sections, [])


if __name__ == "__main__":
    unittest.main()
