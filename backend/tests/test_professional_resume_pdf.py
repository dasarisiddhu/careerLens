import unittest

from services.professional_resume_pdf import build_professional_resume_pdf


class ProfessionalResumePdfTests(unittest.TestCase):
    def test_generated_pdf_has_extractable_text(self):
        source_resume = (
            "Karthik Rao\n"
            "karthik@example.com | 555-123-4567\n"
            "Skills: Python, Flask, SQLite\n"
            "Built a parking management system for college operations.\n"
        )
        content = {
            "headline": "Software Engineer",
            "summary": "Software Engineer specializing in backend APIs and data pipelines.",
            "skillGroups": [
                {"category": "Languages", "skills": ["Python"]},
                {"category": "Frameworks", "skills": ["Flask"]},
                {"category": "Databases", "skills": ["SQLite"]},
            ],
            "educationLines": ["B.Tech Computer Science"],
            "improvedBullets": [
                "Built Flask parking management workflows with SQLite-backed vehicle records."
            ],
            "newBullets": [],
            "bullets": [],
            "githubProjects": [],
        }

        generated = build_professional_resume_pdf(
            name="Karthik Rao",
            email="karthik@example.com",
            phone="555-123-4567",
            content=content,
            source_resume_text=source_resume,
        )

        self.assertGreater(len(generated.pdf_bytes), 500)
        self.assertIn("Karthik Rao", generated.extracted_text)
        self.assertIn("Flask", generated.extracted_text)
        self.assertGreater(generated.extraction_ratio, 0.2)


if __name__ == "__main__":
    unittest.main()
