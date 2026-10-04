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
    _sentence_shares_over_60_percent_with_any_bullet,
    _validate_against_source,
    _validate_optimized_structure,
    _preserve_domain_nouns,
    _apply_optimizer_safety_filters,
    _flatten_skills,
)


class FixFD2E2GTests(unittest.TestCase):
    def setUp(self):
        # Rohan Verma Fixture with CI/CD included
        self.resume_text = (
            "Rohan Verma\n"
            "ML Engineer\n"
            "rohan.verma@example.com | +91 98765 00000 | Hyderabad, India | linkedin.com/in/rohan-verma-demo | github.com/rohanverma-demo\n\n"
            "SUMMARY\n"
            "Machine Learning Engineer with hands-on experience building and deploying ML models using Python, PyTorch, scikit-learn, and FastAPI.\n\n"
            "SKILLS\n"
            "Languages: Python, SQL, C++\n"
            "ML & Data: PyTorch, scikit-learn, XGBoost, Pandas, NumPy, Hugging Face Transformers\n"
            "Tools & Platforms: Docker, Git, CI/CD, MLflow, FastAPI, AWS, Linux\n"
            "Concepts: Feature Engineering, Model Inference\n\n"
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
            "Plant Disease Detector (Computer Vision) | PyTorch, OpenCV, AWS\n"
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
    # FIX F: Summary dedup
    # ─────────────────────────────────────────────────────────────
    def test_fix_f_grounded_source_summary_kept_verbatim(self):
        """If source summary exists and is grounded, keep it verbatim."""
        result = {
            "optimized_summary": "Synthesized summary with borrowed bullet content.",
            "improved_bullets": [],
            "new_bullets": [],
        }
        deduped = _build_deduped_summary(
            candidate_summary=result["optimized_summary"],
            resume_text=self.resume_text,
            doc=self.doc,
            result=result,
            job_title="Machine Learning Engineer",
        )
        self.assertEqual(deduped, self.doc.summary.strip())

    def test_fix_f_extra_sentence_only_if_unused_metric(self):
        """Add at most ONE extra sentence (<=25 words) and ONLY if it contains a metric NOT in any bullet."""
        all_bullet_texts = [b.original for b in self.doc.all_bullets]

        # Case 1: Extra sentence uses metric already in a bullet (e.g. 500K+, 0.87)
        cand_with_used_metric = (
            f"{self.doc.summary} Built customer churn model on 500K+ records with 0.87 F1-score."
        )
        result1 = {"improved_bullets": [], "new_bullets": []}
        deduped1 = _build_deduped_summary(
            candidate_summary=cand_with_used_metric,
            resume_text=self.resume_text,
            doc=self.doc,
            result=result1,
            job_title="Machine Learning Engineer",
        )
        # Should NOT add the second sentence
        self.assertEqual(deduped1, self.doc.summary.strip())

        # Case 2: Resume with an education metric (CGPA 8.4) not in any bullet
        cand_with_unused_metric = (
            f"{self.doc.summary} Graduated with CGPA 8.4 in computer science."
        )
        deduped2 = _build_deduped_summary(
            candidate_summary=cand_with_unused_metric,
            resume_text=self.resume_text,
            doc=self.doc,
            result=result1,
            job_title="Machine Learning Engineer",
        )
        self.assertIn("CGPA 8.4", deduped2)
        # Hard cap: <= 2 sentences, <= 50 words
        sents = [s for s in re.split(r"(?<=[.!?])\s+", deduped2) if s.strip()]
        self.assertLessEqual(len(sents), 2)
        self.assertLessEqual(len(deduped2.split()), 50)

    def test_fix_f_no_summary_sentence_shares_over_60_percent_tokens_with_any_bullet(self):
        """ACCEPT: [ ] no summary sentence shares >60% of its tokens with any bullet."""
        all_bullets = [b.original for b in self.doc.all_bullets]
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", self.doc.summary) if s.strip()]
        for sent in sents:
            self.assertFalse(
                _sentence_shares_over_60_percent_with_any_bullet(sent, all_bullets),
                f"Summary sentence '{sent}' shared >60% tokens with a bullet",
            )

    def test_fix_f_summary_under_3_rendered_lines_for_fixture(self):
        """ACCEPT: [ ] summary <= 3 rendered lines for this fixture."""
        rec = reconstruct_resume_structure(self.doc, {})
        pdf = build_professional_resume_pdf(
            name=self.doc.name,
            email=self.doc.email,
            content=rec,
            source_resume_text=self.resume_text,
        )
        # Check rendered lines of summary
        wrapped = _wrap_text(rec["summary"], CONTENT_WIDTH, "helv", 9.8)
        self.assertLessEqual(
            len(wrapped),
            3,
            f"Expected summary to render in <= 3 lines, got {len(wrapped)}: {wrapped}",
        )

    # ─────────────────────────────────────────────────────────────
    # FIX D2: Skills superset invariant
    # ─────────────────────────────────────────────────────────────
    def test_fix_d2_skills_superset_invariant(self):
        """ACCEPT: [ ] set(source_skills) ⊆ set(output_skills)."""
        result = {
            "optimized_skills": {
                "Languages": ["Python"],
                "ML & Data": ["PyTorch", "XGBoost"],
                "Tools & Platforms": ["Docker", "AWS"],
            }
        }
        val_res = _validate_against_source(result, self.resume_text, self.jd)
        output_skills = _flatten_skills(val_res["optimized_skills"])
        source_skills = self.doc.skills

        output_set = {s.lower() for s in output_skills}
        source_set = {s.lower() for s in source_skills}
        self.assertTrue(
            source_set.issubset(output_set),
            f"Output skills must be superset of source skills. Missing: {source_set - output_set}",
        )

    def test_fix_d2_all_required_skills_present(self):
        """ACCEPT: [ ] XGBoost, SQL, CI/CD, Pandas, NumPy all present for this fixture."""
        rec = reconstruct_resume_structure(self.doc, {})
        flat_skills = _flatten_skills(rec["skills"])
        flat_lower = {s.lower() for s in flat_skills}

        for req in ["XGBoost", "SQL", "CI/CD", "Pandas", "NumPy"]:
            self.assertIn(
                req.lower(),
                flat_lower,
                f"Required skill '{req}' missing from reconstructed skills: {flat_skills}",
            )

    def test_fix_d2_preserve_parentheticals_and_jd_relevance_reorder(self):
        """Preserve parentheticals ('AWS (S3, EC2)') and reorder by JD relevance only."""
        custom_resume = (
            "Jane Doe\n"
            "jane@example.com\n\n"
            "SKILLS\n"
            "Languages: Python, Go, C++\n"
            "Tools: Docker, AWS (S3, EC2), CI/CD, Kubernetes\n"
        )
        custom_jd = "Looking for AWS and Kubernetes expert with Docker experience."
        result = {
            "optimized_skills": {
                "Languages": ["Python", "Go", "C++"],
                "Tools": ["Docker", "AWS (S3, EC2)", "CI/CD", "Kubernetes"],
            }
        }
        val_res = _validate_against_source(result, custom_resume, custom_jd)
        tools = val_res["optimized_skills"]["Tools"]
        # AWS (S3, EC2) preserved without truncation
        self.assertTrue(any("AWS (S3, EC2)" in t for t in tools))
        # JD mentions AWS and Kubernetes, so AWS and Kubernetes should come before CI/CD
        aws_idx = next(i for i, t in enumerate(tools) if "AWS" in t)
        cicd_idx = next(i for i, t in enumerate(tools) if "CI/CD" in t)
        self.assertLess(aws_idx, cicd_idx, "AWS should precede CI/CD due to higher JD relevance")

    # ─────────────────────────────────────────────────────────────
    # FIX E2: Header clipping
    # ─────────────────────────────────────────────────────────────
    def test_fix_e2_header_contact_wrapping_no_url_truncation(self):
        """
        ACCEPT: [ ] output text contains "github.com/rohanverma-demo" in full
                [ ] same for the linkedin URL
        """
        rec = reconstruct_resume_structure(self.doc, {})
        pdf = build_professional_resume_pdf(
            name=self.doc.name,
            email=self.doc.email,
            content=rec,
            source_resume_text=self.resume_text,
        )
        visible_text = pdf.visible_text

        self.assertIn(
            "github.com/rohanverma-demo",
            visible_text,
            "Full GitHub URL must be present in visible text without truncation",
        )
        self.assertIn(
            "linkedin.com/in/rohan-verma-demo",
            visible_text,
            "Full LinkedIn URL must be present in visible text without truncation",
        )

    # ─────────────────────────────────────────────────────────────
    # FIX G: Small fidelity items
    # ─────────────────────────────────────────────────────────────
    def test_fix_g_role_company_source_order_preserved(self):
        """Keep source entry order (Role | Company)."""
        rec = reconstruct_resume_structure(self.doc, {})
        pdf = build_professional_resume_pdf(
            name=self.doc.name,
            email=self.doc.email,
            content=rec,
            source_resume_text=self.resume_text,
        )
        visible_lines = pdf.visible_text.splitlines()
        role_lines = [
            l for l in visible_lines
            if "Nimbus Analytics" in l or "Machine Learning Intern" in l
        ]
        self.assertEqual(len(role_lines), 1, f"Expected 1 role line, found: {role_lines}")
        role_line = role_lines[0]
        # Role must precede company
        role_pos = role_line.find("Machine Learning Intern")
        company_pos = role_line.find("Nimbus Analytics")
        self.assertNotEqual(role_pos, -1)
        self.assertNotEqual(company_pos, -1)
        self.assertLess(
            role_pos,
            company_pos,
            f"Expected Role | Company order, but got: '{role_line}'",
        )

    def test_fix_g_domain_nouns_preserved_when_shortening(self):
        """Don't drop domain nouns ('leaf images', 'customer records') when shortening bullets."""
        orig_bullet = "Trained a ResNet-50 classifier on 54,000 leaf images across 38 classes, achieving 96% validation accuracy."
        shortened_bullet = "Trained a ResNet-50 classifier on 54,000 images across 38 classes, achieving 96% validation accuracy."

        preserved = _preserve_domain_nouns(shortened_bullet, orig_bullet)
        self.assertIn(
            "leaf images",
            preserved,
            f"Domain noun 'leaf images' must be restored, got: '{preserved}'",
        )

        customer_orig = "Built churn model on 500K+ customer records."
        customer_short = "Built churn model on 500K+ records."
        preserved_customer = _preserve_domain_nouns(customer_short, customer_orig)
        self.assertIn("customer records", preserved_customer)


if __name__ == "__main__":
    unittest.main()
