import unittest
from services.professional_resume_pdf import (
    build_professional_resume_pdf,
    _has_held_title,
    _clean_pdf_text,
    _extract_source_contact_and_certs,
    assert_pdf_text_extractable,
)

class DefectFixesGroup5Tests(unittest.TestCase):

    def test_d1_wrapped_experience_and_project_headers(self):
        """D1: Experience and project header lines use wrapped(), extracting full text without truncation."""
        long_title = "Principal Distributed Systems and Cloud Infrastructure Architect Specialist"
        long_org = "Acme Global International Technologies and Systems Corporation Limited"
        long_dates = "January 2020 - December 2023"
        long_loc = "San Francisco Bay Area, California, United States"

        content = {
            "name": "Jane Doe",
            "experience": [
                {
                    "title": long_title,
                    "organization": long_org,
                    "dates": long_dates,
                    "location": long_loc,
                    "bullets": ["Led core architecture for platform."],
                }
            ],
            "projects": [
                {
                    "name": "Enterprise Multi-Region Data Migration and Synchronization Platform",
                    "technologies": "Python, Go, Kafka, Cassandra, Kubernetes, Terraform",
                    "dates": "2022 - 2023",
                    "bullets": ["Migrated 10PB of database records."],
                }
            ],
        }
        pdf = build_professional_resume_pdf(name="Jane Doe", content=content)
        self.assertIn("Principal Distributed Systems", pdf.extracted_text)
        self.assertIn("Enterprise Multi-Region", pdf.extracted_text)

    def test_d2_placeholders_never_printed(self):
        """D2: Never print 'No summary generated.' or 'Your Name'. Omit summary if empty."""
        content = {
            "name": "",
            "summary": "",
            "skills": ["Python", "FastAPI"],
            "experience": [
                {
                    "title": "Backend Engineer",
                    "organization": "Acme",
                    "bullets": ["Built APIs."],
                }
            ],
        }
        # Router passes name="Your Name" as fallback, but build_professional_resume_pdf should not print "Your Name"
        pdf = build_professional_resume_pdf(name="Your Name", content=content)
        self.assertNotIn("Your Name", pdf.extracted_text)
        self.assertNotIn("No summary generated", pdf.extracted_text)
        # Omit Summary heading when summary is empty
        self.assertNotIn("Summary\n", pdf.extracted_text)

    def test_d2_name_precedence_and_summary_fallback(self):
        """D2: content name and reconstructed summary have precedence over placeholder."""
        content = {
            "name": "Alice Smith",
            "reconstructed_resume": {
                "summary": "Experienced engineer with a focus on reliability.",
                "skills": ["Go", "Docker"],
            },
        }
        pdf = build_professional_resume_pdf(name="Your Name", content=content)
        self.assertIn("Alice Smith", pdf.extracted_text)
        self.assertIn("Experienced engineer with a focus on reliability.", pdf.extracted_text)

    def test_d3_unicode_and_code_brackets_preserved(self):
        """D3: Special unicode (José, ₹) and code syntax (List<String>, <stdio.h>) survive."""
        cleaned_brackets = _clean_pdf_text("Uses List<String>, vector<int>, and #include <stdio.h>.")
        self.assertIn("<String>", cleaned_brackets)
        self.assertIn("<int>", cleaned_brackets)
        self.assertIn("<stdio.h>", cleaned_brackets)

        content = {
            "name": "José García",
            "summary": "Generated ₹50M in efficiency with List<String> and <stdio.h>.",
            "skills": ["C++", "Java"],
        }
        pdf = build_professional_resume_pdf(name="José García", content=content)
        self.assertIn("José", pdf.extracted_text)
        self.assertIn("₹", pdf.extracted_text)
        self.assertIn("<stdio.h>", pdf.extracted_text)

    def test_d4_exact_title_boundary_match(self):
        """D4: 'Software Engineer' is NOT held by 'Software Engineer Intern'."""
        intern_entries = [{"title": "Software Engineer Intern", "organization": "Acme"}]
        self.assertFalse(_has_held_title("Software Engineer", intern_entries))
        self.assertTrue(_has_held_title("Software Engineer Intern", intern_entries))

        engineer_entries = [{"title": "Software Engineer", "organization": "Acme"}]
        self.assertTrue(_has_held_title("Software Engineer", engineer_entries))

    def test_d5_certifications_stops_at_recognized_heading(self):
        """D5: Certifications stops at recognized headings and does not duplicate."""
        resume = (
            "CERTIFICATIONS\n"
            "- AWS Certified Solutions Architect\n"
            "- CKA Certified Kubernetes Administrator\n"
            "ACHIEVEMENTS\n"
            "- Won first place in university hackathon\n"
            "PROJECTS\n"
            "- Project 1\n"
        )
        parsed = _extract_source_contact_and_certs(resume)
        certs = parsed.get("certifications", [])
        self.assertEqual(len(certs), 2)
        self.assertIn("AWS Certified Solutions Architect", certs)
        self.assertIn("CKA Certified Kubernetes Administrator", certs)
        self.assertNotIn("Won first place in university hackathon", certs)

    def test_d6_all_caps_name_extracted_and_location_found(self):
        """D6: First non-empty line as ALL-CAPS name is extracted; header continues for location."""
        resume = (
            "JOHN DOE\n"
            "john.doe@example.com | +1 555-0199 | Austin, TX\n"
            "EXPERIENCE\n"
            "Software Engineer  Acme Corp\n"
        )
        parsed = _extract_source_contact_and_certs(resume)
        self.assertEqual(parsed.get("name"), "JOHN DOE")
        self.assertEqual(parsed.get("location"), "Austin, TX")
        self.assertEqual(parsed.get("email"), "john.doe@example.com")

    def test_d7_assert_pdf_text_extractable_completeness(self):
        """D7: Token completeness check passes on normal generation."""
        content = {
            "name": "Jane Doe",
            "skills": ["Python", "FastAPI"],
            "experience": [
                {
                    "title": "Backend Developer",
                    "organization": "Acme Labs",
                    "bullets": ["Engineered high throughput services."],
                }
            ],
        }
        pdf = build_professional_resume_pdf(name="Jane Doe", content=content)
        self.assertGreater(len(pdf.extracted_text), 50)


if __name__ == "__main__":
    unittest.main()
