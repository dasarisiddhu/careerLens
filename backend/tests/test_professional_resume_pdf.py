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

    def test_certifications_and_contact_preserved_in_pdf(self):
        source_resume = (
            "Jane Doe\n"
            "jane@example.com | +1 555-987-6543 | New York, NY\n"
            "linkedin.com/in/janedoe | github.com/janedoe\n"
            "Skills: Python, AWS, Docker\n"
            "Experience:\n"
            "- Built cloud microservices using Python and Docker.\n"
            "Certifications:\n"
            "- AWS Certified Solutions Architect - Associate\n"
            "- Certified Kubernetes Administrator (CKA)\n"
        )
        content = {
            "headline": "Cloud Engineer",
            "summary": "Cloud Engineer with experience in AWS and containerization.",
            "skills": ["Python", "AWS", "Docker"],
            "educationLines": ["B.S. in Computer Science"],
            "improvedBullets": ["Engineered cloud microservices using Python and Docker on AWS."],
            "newBullets": [],
            "bullets": [],
        }

        generated = build_professional_resume_pdf(
            name="Jane Doe",
            content=content,
            source_resume_text=source_resume,
        )

        self.assertIn("jane@example.com", generated.extracted_text)
        self.assertIn("janedoe", generated.extracted_text)
        self.assertIn("AWS Certified Solutions Architect", generated.extracted_text)
        self.assertIn("Certified Kubernetes Administrator", generated.extracted_text)

    def test_contact_header_does_not_pull_education_institution(self):
        source_resume = (
            "Sai Siddhartha Raj\n"
            "siddhu@example.com | +91 98765 43210 | linkedin.com/in/siddhu\n"
            "Bengaluru, Karnataka\n"
            "EDUCATION\n"
            "Vellore Institute of Technology, Chennai\n"
            "Bachelor of Technology, Computer Science\n"
            "EXPERIENCE\n"
            "- Developed AI workflows with Python and FastAPI.\n"
        )
        content = {
            "headline": "AI Engineer",
            "summary": "AI Engineer specializing in LLM systems.",
            "skills": ["Python", "FastAPI"],
            "educationLines": ["Vellore Institute of Technology, Chennai", "Bachelor of Technology, Computer Science"],
            "improvedBullets": ["Developed high-throughput AI workflows with Python and FastAPI."],
            "newBullets": [],
            "bullets": [],
        }

        generated = build_professional_resume_pdf(
            name="Sai Siddhartha Raj",
            content=content,
            source_resume_text=source_resume,
        )

        # Phone number must survive
        self.assertIn("+91 98765 43210", generated.extracted_text)
        self.assertIn("siddhu@example.com", generated.extracted_text)
        self.assertIn("Bengaluru, Karnataka", generated.extracted_text)

        # Confirm the contact line does NOT have the education institution
        lines = [line.strip() for line in generated.extracted_text.splitlines() if line.strip()]
        # First 3 lines should contain name, headline, contact line
        contact_header_candidates = lines[1:4]
        for header_cand in contact_header_candidates:
            if "siddhu@example.com" in header_cand:
                self.assertNotIn("Vellore Institute of Technology", header_cand)
                self.assertNotIn("Bachelor of Technology", header_cand)

    def test_location_sanitizes_education_text_if_passed_explicitly(self):
        content = {
            "headline": "Software Engineer",
            "summary": "Software Engineer with backend experience.",
            "skills": ["Python"],
            "educationLines": ["UC Berkeley"],
            "improvedBullets": ["Engineered core backend systems in Python."],
            "newBullets": [],
            "bullets": [],
        }

        generated = build_professional_resume_pdf(
            name="Alex Smith",
            email="alex@example.com",
            phone="555-123-4567",
            location="University of California, Berkeley",  # Incorrect education institution passed as location
            content=content,
            source_resume_text="Alex Smith\nalex@example.com\n555-123-4567\n",
        )

        lines = [line.strip() for line in generated.extracted_text.splitlines() if line.strip()]
        for cand in lines[1:4]:
            if "alex@example.com" in cand:
                self.assertNotIn("University of California", cand)


if __name__ == "__main__":
    unittest.main()
