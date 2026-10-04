import re
import unittest
from services.resume_structure import (
    parse_source_resume,
    reconstruct_resume_structure,
)
from services.professional_resume_pdf import (
    build_professional_resume_pdf,
    _wrap_text,
    CONTENT_WIDTH,
)
from routers.optimizer import (
    _build_deduped_summary,
    _build_skills_education_summary,
    _clean_quantifiers,
    _restore_n_plus_forms,
    _mark_ungrounded_metrics,
    _validate_against_source,
    _flatten_skills,
)


class FixF2D3HE3GTests(unittest.TestCase):
    def setUp(self):
        # Rohan Verma Fixture with CI/CD included
        self.resume_text = (
            "Rohan Verma\n"
            "ML Engineer\n"
            "rohan.verma@example.com | +91 98765 00000 | Hyderabad, India | linkedin.com/in/rohan-verma-demo | github.com/rohanverma-demo\n\n"
            "SUMMARY\n"
            "Computer Science graduate with ML internship experience building and deploying ML models using Python, PyTorch, scikit-learn, and FastAPI.\n\n"
            "SKILLS\n"
            "Languages: Python, SQL, C++\n"
            "ML & Data: PyTorch, scikit-learn, XGBoost, Pandas, NumPy, Hugging Face Transformers\n"
            "Tools & Platforms: Docker, Git, CI/CD, MLflow, FastAPI, AWS, Linux\n\n"
            "EXPERIENCE\n"
            "Machine Learning Intern | Nimbus Analytics Pvt Ltd, Hyderabad | Jan 2025 - Jun 2025\n"
            "• Built a customer churn model with XGBoost on 500K+ customer records, reaching an F1-score of 0.87 on a held-out\n"
            "test set.\n"
            "• Reduced model inference latency by 38% by exporting the model to ONNX and batching requests in a FastAPI\n"
            "service.\n"
            "• Containerized the prediction service with Docker and served 40K+ daily predictions to the analytics dashboard.\n"
            "• Tracked 60+ experiments with MLflow and documented feature pipelines so the team could reproduce results.\n\n"
            "PROJECTS\n"
            "Resume Skill Extractor (NLP) | Python, Hugging Face Transformers, FastAPI\n"
            "• Fine-tuned a BERT-based named entity model on 8,000 annotated resumes, improving skill extraction F1 from 0.71\n"
            "to 0.84.\n"
            "(continued)\n"
            "• Deployed the model as a REST API with FastAPI and Docker, returning predictions in under 200 ms.\n\n"
            "Plant Disease Detector (Computer Vision) | PyTorch, OpenCV, AWS (S3, EC2)\n"
            "• Trained a ResNet-50 classifier on 54,000 leaf images across 38 classes, achieving 96% validation accuracy.\n"
            "• Hosted the model on an AWS EC2 instance with a Flask front end used by 120+ students during a college demo.\n\n"
            "Credit Risk Scoring | Python, scikit-learn, SQL\n"
            "• Engineered 25 features from loan data and compared logistic regression, random forest and gradient boosting,\n"
            "selecting the best model by ROC-AUC of 0.91.\n\n"
            "EDUCATION\n"
            "B.Tech, Computer Science and Engineering | Example Institute of Technology, Hyderabad | 2021 - 2025 | CGPA 8.4/10\n\n"
            "CERTIFICATIONS\n"
            "• Deep Learning Specialization (online course certificate)\n"
            "• AWS Certified Cloud Practitioner\n"
        )
        self.doc = parse_source_resume(self.resume_text)
        self.jd = (
            "We are looking for a Machine Learning Engineer proficient in Python, PyTorch, XGBoost, SQL, Pandas, NumPy, "
            "FastAPI, Docker, CI/CD, AWS and MLflow. Experience with computer vision and NLP is a plus."
        )

    # ─────────────────────────────────────────────────────────────
    # [FIX F2: Summary fallback]
    # ─────────────────────────────────────────────────────────────
    def test_fix_f2_grounded_source_summary_returned_unchanged(self):
        """If the source summary exists and passes grounding, return it unchanged."""
        result = {
            "optimized_summary": "LLM synthesized text that shouldn't override source summary",
            "original_summary": self.doc.summary,
            "improved_bullets": [],
            "new_bullets": [],
        }
        summary = _build_deduped_summary(
            candidate_summary=result["optimized_summary"],
            resume_text=self.resume_text,
            doc=self.doc,
            result=result,
            job_title="Machine Learning Engineer",
        )
        self.assertEqual(summary, self.doc.summary.strip())
        # ACCEPT: [ ] this fixture's summary contains "graduate" and "internship"
        self.assertIn("graduate", summary.lower())
        self.assertIn("internship", summary.lower())

    def test_fix_f2_never_emit_technical_background_with_core_proficiencies(self):
        """Never emit 'Technical background with core proficiencies in ...'."""
        fallback = _build_skills_education_summary(
            resume_text="Skills: Python, SQL\nExperience: ML Intern",
            result=None,
            doc=None,
        )
        self.assertNotIn("technical background with core proficiencies in", fallback.lower())
        self.assertNotIn("core proficiencies in", fallback.lower())

    def test_fix_f2_no_summary_consisting_only_of_a_skills_list(self):
        """ACCEPT: [ ] no summary consisting only of a skills list."""
        fallback = _build_skills_education_summary(
            resume_text="Skills: Python, SQL\nExperience: ML Intern",
            result=None,
            doc=None,
        )
        # Should be a structured sentence with identity/internship/background, not just comma-separated skills
        self.assertRegex(fallback, r"\b(graduate|internship|foundation|background)\b", "Summary should not be only a raw skills list")
        self.assertTrue(fallback.endswith("."), "Summary should end with a period as a full sentence")

    # ─────────────────────────────────────────────────────────────
    # [FIX D3: Skills structure]
    # ─────────────────────────────────────────────────────────────
    def test_fix_d3_three_groups_preserved_and_aws_merged_opencv_present(self):
        """
        ACCEPT: [ ] three groups preserved
                [ ] AWS appears once
                [ ] OpenCV present
        """
        result = {
            "optimized_skills": {
                "Languages": ["Python", "SQL"],
                "ML & Data": ["PyTorch", "scikit-learn"],
                "Tools & Platforms": ["Docker", "AWS"],
            }
        }
        val_res = _validate_against_source(result, self.resume_text, self.jd)
        opt_skills = val_res["optimized_skills"]

        # [ ] three groups preserved
        self.assertEqual(len(opt_skills), 3, f"Expected 3 groups preserved, got: {list(opt_skills.keys())}")
        self.assertEqual(list(opt_skills.keys()), ["Languages", "ML & Data", "Tools & Platforms"])

        # [ ] OpenCV present (added to matching group ML & Data from project stack line)
        ml_skills = [s.lower() for s in opt_skills["ML & Data"]]
        self.assertTrue(any("opencv" in s for s in ml_skills), f"OpenCV must be in ML & Data, found: {opt_skills['ML & Data']}")

        # [ ] AWS appears once (plain AWS merged with detailed AWS (S3, EC2))
        flat_skills = _flatten_skills(opt_skills)
        aws_matches = [s for s in flat_skills if "aws" in s.lower()]
        self.assertEqual(len(aws_matches), 1, f"AWS should appear exactly once, got: {aws_matches}")
        self.assertIn("AWS (S3, EC2)", aws_matches[0], f"Detailed parenthetical AWS form must be kept: {aws_matches}")

    # ─────────────────────────────────────────────────────────────
    # [FIX H: Quantifier fidelity]
    # ─────────────────────────────────────────────────────────────
    def test_fix_h_quantifier_fidelity_500k_plus_survives(self):
        """ACCEPT: [ ] '500K+' survives as written."""
        text = "Built a customer churn model with XGBoost on 500K+ customer records."
        cleaned = _clean_quantifiers(text)
        self.assertIn("500K+", cleaned)

        # Ensure _mark_ungrounded_metrics does not strip + or prepend ~
        marked, _ = _mark_ungrounded_metrics(text, self.resume_text, self.jd.lower())
        self.assertIn("500K+", marked)

    def test_fix_h_regex_over_approx_matches_nothing(self):
        """ACCEPT: [ ] regex /over ~|~\\d/ matches nothing."""
        bullets = [
            "Served over ~40K predictions daily.",
            "Handled approximately 500K+ records.",
            "Trained on ~54,000 leaf images.",
            "Hosted model used by ~120 students.",
        ]
        banned_pattern = re.compile(r"over\s*~|~\d")
        for b in bullets:
            cleaned = _clean_quantifiers(b)
            self.assertIsNone(
                banned_pattern.search(cleaned),
                f"Regex /over ~|~\\d/ matched text after cleaning: '{cleaned}'",
            )
            self.assertNotIn("approximately", cleaned.lower())

    # ─────────────────────────────────────────────────────────────
    # [FIX E3: Header, third time]
    # ─────────────────────────────────────────────────────────────
    def test_fix_e3_github_rohanverma_demo_in_full(self):
        """ACCEPT: [ ] output contains 'github.com/rohanverma-demo' in full."""
        rec = reconstruct_resume_structure(self.doc, {})
        pdf = build_professional_resume_pdf(
            name=self.doc.name,
            email=self.doc.email,
            content=rec,
            source_resume_text=self.resume_text,
        )
        self.assertIn(
            "github.com/rohanverma-demo",
            pdf.visible_text,
            "Visible text must contain github.com/rohanverma-demo in full",
        )
        self.assertIn(
            "linkedin.com/in/rohan-verma-demo",
            pdf.visible_text,
            "Visible text must contain linkedin.com/in/rohan-verma-demo in full",
        )

    # ─────────────────────────────────────────────────────────────
    # [FIX G: Entry order + CGPA]
    # ─────────────────────────────────────────────────────────────
    def test_fix_g_role_company_order_and_cgpa_non_breaking_space(self):
        """Keep Role | Company order. Join 'CGPA 8.4/10' with a non-breaking space."""
        rec = reconstruct_resume_structure(self.doc, {})

        # Education CGPA check
        edu_entries = rec.get("education", [])
        self.assertTrue(len(edu_entries) > 0)
        found_cgpa = False
        for entry in edu_entries:
            if "CGPA" in entry:
                self.assertIn("CGPA\u00a08.4/10", entry, "CGPA 8.4/10 must be joined with a non-breaking space (\\u00a0)")
                found_cgpa = True
        self.assertTrue(found_cgpa, "Education must contain CGPA entry")

        # Role | Company order check in PDF output
        pdf = build_professional_resume_pdf(
            name=self.doc.name,
            email=self.doc.email,
            content=rec,
            source_resume_text=self.resume_text,
        )
        role_lines = [l for l in pdf.visible_text.splitlines() if "Machine Learning Intern" in l and "Nimbus Analytics" in l]
        self.assertEqual(len(role_lines), 1, f"Expected 1 role line, found: {role_lines}")
        role_line = role_lines[0]
        role_pos = role_line.find("Machine Learning Intern")
        comp_pos = role_line.find("Nimbus Analytics")
        self.assertLess(role_pos, comp_pos, f"Expected Role before Company in: '{role_line}'")


if __name__ == "__main__":
    unittest.main()
