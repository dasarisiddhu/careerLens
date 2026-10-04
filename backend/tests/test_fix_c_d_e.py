import unittest
from services.resume_structure import parse_source_resume
from services.professional_resume_pdf import (
    build_professional_resume_pdf,
    _extract_source_contact_and_certs,
    _has_held_title,
    _wrap_text,
    _text_width,
    CONTENT_WIDTH,
)
from routers.optimizer import (
    _verify_optimizer_summary,
    _apply_optimizer_safety_filters,
    _validate_against_source,
    _extract_source_skills,
    _extract_source_skill_groups,
    _split_preserving_parens,
    _contains_grounded_term,
)


class TestFixCSummary(unittest.TestCase):
    def test_target_job_title_as_identity_rejected(self):
        """Never use the JD title as candidate identity if not held."""
        source_text = (
            "Alex Smith\n"
            "alex@example.com | 1234567890 | Bangalore, India\n"
            "Summary\n"
            "Computer Science graduate with ML internship experience.\n"
            "Education\n"
            "B.Tech Computer Science, 2024\n"
            "Experience\n"
            "Software Engineering Intern, TechCorp | 2023 - 2024\n"
            "- Built backend services with Python.\n"
            "Skills: Python, FastAPI, Docker\n"
        )
        # LLM tries to claim identity as target title "Senior ML Architect"
        bad_summary = "Senior ML Architect with extensive expertise in production systems."
        is_valid, reason = _verify_optimizer_summary(bad_summary, source_text, "Senior ML Architect")
        self.assertFalse(is_valid)
        self.assertEqual(reason, "target_job_title_as_identity")

    def test_retains_original_summary_when_llm_summary_fails(self):
        """If the LLM summary fails verification, keep the original summary rather than a template."""
        source_text = (
            "Alex Smith\n"
            "alex@example.com | 1234567890 | Bangalore, India\n"
            "Summary\n"
            "Computer Science graduate with ML internship experience.\n"
            "Experience\n"
            "Software Engineering Intern, TechCorp | 2023 - 2024\n"
            "- Built backend services with Python.\n"
            "Skills: Python, FastAPI\n"
        )
        doc = parse_source_resume(source_text)
        result = {
            "optimized_summary": "Senior ML Architect with 99.9% uptime and 10M users.",
            "original_summary": "Computer Science graduate with ML internship experience.",
            "improved_bullets": [],
            "new_bullets": [],
        }
        filtered = _apply_optimizer_safety_filters(
            result, source_text, "Senior ML Architect", user_id="test", doc=doc
        )
        self.assertEqual(
            filtered["optimized_summary"],
            "Computer Science graduate with ML internship experience.",
        )
        self.assertIn("original resume summary", filtered.get("summary_grounding_note", ""))

    def test_headline_removed_unless_actually_held(self):
        """Remove the header title line unless the person has actually held that title."""
        source_text = (
            "Alex Smith\n"
            "alex@example.com\n"
            "Experience\n"
            "Junior Developer, Startup Inc | 2022 - 2024\n"
            "- Built REST APIs.\n"
        )
        doc = parse_source_resume(source_text)
        # Target title is "Machine Learning Engineer" which was never held
        self.assertFalse(_has_held_title("Machine Learning Engineer", doc.experience, source_text))
        # Title "Junior Developer" was held
        self.assertTrue(_has_held_title("Junior Developer", doc.experience, source_text))


class TestFixDSkills(unittest.TestCase):
    def test_split_preserving_parens_and_cicd(self):
        """Preserve parenthetical details like 'AWS (S3, EC2)' and preserve 'CI/CD'."""
        text = "Python, CI/CD, AWS (S3, EC2), Docker | Kubernetes; Feature Engineering"
        items = _split_preserving_parens(text)
        self.assertIn("CI/CD", items)
        self.assertIn("AWS (S3, EC2)", items)
        self.assertIn("Feature Engineering", items)
        self.assertNotIn("CI", items)
        self.assertNotIn("CD", items)
        self.assertNotIn("AWS (S3", items)

    def test_contains_grounded_term_cicd_and_parens(self):
        """_contains_grounded_term matches 'CI/CD' and 'AWS (S3, EC2)'."""
        haystack = "proficient in python, ci/cd pipelines, and aws (s3, ec2) cloud deployment"
        self.assertTrue(_contains_grounded_term(haystack, "CI/CD"))
        self.assertTrue(_contains_grounded_term(haystack, "AWS (S3, EC2)"))

    def test_feature_engineering_under_ml_and_data_and_output_skills_superset(self):
        """Feature Engineering remains under ML & Data, and output skills ⊇ source skills."""
        source_text = (
            "Jane Doe\n"
            "Skills\n"
            "Languages: Python, SQL\n"
            "ML & Data: PyTorch, Pandas, Feature Engineering\n"
            "Tools: Docker, CI/CD, AWS (S3, EC2)\n"
            "Experience\n"
            "- Worked on ML models.\n"
        )
        result = {
            "optimized_skills": {
                "Languages": ["Python"],
                "ML & Data": ["PyTorch"],
                "Tools & Platforms": ["Docker"],
            }
        }
        validated = _validate_against_source(result, source_text, "ML Engineer")
        opt = validated["optimized_skills"]

        # [ ] CI/CD present
        tools_list = opt.get("Tools & Platforms", [])
        self.assertIn("CI/CD", tools_list)
        self.assertIn("AWS (S3, EC2)", tools_list)

        # [ ] Feature Engineering still under ML & Data
        ml_list = opt.get("ML & Data", [])
        self.assertIn("Feature Engineering", ml_list)

        # [ ] output skills ⊇ source skills
        source_skills = _extract_source_skills(source_text)
        flat_opt = [s for sublist in opt.values() for s in sublist]
        for src in source_skills:
            self.assertTrue(
                any(src.lower() == out.lower() for out in flat_opt),
                f"Source skill '{src}' missing from output skills {flat_opt}",
            )

    def test_no_per_group_cap_of_six(self):
        """Ensure skills per group are not truncated to 6."""
        source_text = (
            "John Doe\n"
            "Skills\n"
            "Languages: Python, Go, Rust, C++, Java, JavaScript, TypeScript, Ruby, Kotlin\n"
            "Experience\n"
            "- Backend development.\n"
        )
        result = {
            "optimized_skills": {
                "Languages": ["Python", "Go", "Rust", "C++", "Java", "JavaScript", "TypeScript", "Ruby", "Kotlin"],
            }
        }
        validated = _validate_against_source(result, source_text, "Software Engineer")
        self.assertGreater(len(validated["optimized_skills"]["Languages"]), 6)
        self.assertEqual(len(validated["optimized_skills"]["Languages"]), 9)


class TestFixERenderer(unittest.TestCase):
    def test_cgpa_kept_on_one_line(self):
        """CGPA 8.4/10 is bound and never broken across lines."""
        text = "B.Tech, Computer Science and Engineering | Example Institute of Technology, Hyderabad | 2021 - 2025 | CGPA 8.4/10"
        lines = _wrap_text(text, max_width=350, font="helv", size=9.2)
        # Check that no line ends with "CGPA" or begins with "8.4/10"
        for line in lines:
            self.assertFalse(line.endswith("CGPA"), f"Line broke after CGPA: {line}")
            self.assertFalse(line.startswith("8.4/10"), f"Line broke before 8.4/10: {line}")
            if "CGPA" in line:
                self.assertIn("CGPA 8.4/10", line)

    def test_certifications_split_per_line(self):
        """Put each certification on its own line."""
        source_text = (
            "Candidate Name\n"
            "candidate@example.com\n"
            "Certifications\n"
            "- AWS Certified Solutions Architect • CompTIA Security+ | HashiCorp Terraform Associate\n"
            "- Microsoft Certified: Azure Fundamentals; Certified Kubernetes Administrator\n"
        )
        parsed = _extract_source_contact_and_certs(source_text)
        certs = parsed.get("certifications", [])
        self.assertIn("AWS Certified Solutions Architect", certs)
        self.assertIn("CompTIA Security+", certs)
        self.assertIn("HashiCorp Terraform Associate", certs)
        self.assertIn("Microsoft Certified: Azure Fundamentals", certs)
        self.assertIn("Certified Kubernetes Administrator", certs)
        self.assertEqual(len(certs), 5)

    def test_header_contact_line_not_clipped(self):
        """Contact items wrap cleanly on separators without clipping."""
        content = {
            "headline": "",
            "summary": "Experienced engineer.",
            "skills": ["Python", "Docker"],
            "educationLines": ["B.Tech CSE | Top Institute | 2024 | CGPA 8.5/10"],
            "certifications": ["AWS Certified Solutions Architect"],
        }
        pdf_res = build_professional_resume_pdf(
            name="Alexander Jonathan Featherstonehaugh",
            email="alexander.jonathan.featherstonehaugh@verylonguniversitydomainname.edu",
            phone="+91 9876543210 / +91 9123456780",
            content=content,
            location="Hyderabad, Telangana, India - 500081",
            linkedin="https://linkedin.com/in/alexander-jonathan-featherstonehaugh-long-url",
            github="https://github.com/alexander-featherstonehaugh-developer-profile",
        )
        self.assertIsNotNone(pdf_res.pdf_bytes)
        self.assertTrue(len(pdf_res.pdf_bytes) > 500)


if __name__ == "__main__":
    unittest.main()
