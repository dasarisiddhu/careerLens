# ============================================================
# CareerLens - CI Gate Invariant Tests: Code Owns Structure
# Fixture: rohan-verma__2_.pdf / Rohan Verma ML Engineer
# File: backend/tests/test_code_owns_structure_invariants.py
# ============================================================

import re
import unittest
from services.resume_structure import (
    parse_source_resume,
    reconstruct_resume_structure,
)
from services.professional_resume_pdf import (
    build_professional_resume_pdf,
)
from routers.optimizer import (
    _validate_optimized_structure,
    _flatten_skills,
    _extract_source_bullet_metrics,
)


class CodeOwnsStructureInvariantsTests(unittest.TestCase):
    def setUp(self):
        # Rohan Verma Fixture (matching rohan-verma__2_.pdf)
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

    # ------------------------------------------------------------
    # INVARIANT 1: Bullets per entry == source (4 / 2 / 2 / 1) and every bullet has a source_id
    # ------------------------------------------------------------
    def test_invariant_bullets_per_entry_and_source_id(self):
        doc = self.doc
        self.assertEqual(len(doc.experience), 1)
        self.assertEqual(len(doc.experience[0].bullets), 4)

        self.assertEqual(len(doc.projects), 3)
        self.assertEqual(len(doc.projects[0].bullets), 2)
        self.assertEqual(len(doc.projects[1].bullets), 2)
        self.assertEqual(len(doc.projects[2].bullets), 1)

        counts = [len(doc.experience[0].bullets)] + [len(p.bullets) for p in doc.projects]
        self.assertEqual(counts, [4, 2, 2, 1])

        # Every bullet has a source_id
        for b in doc.all_bullets:
            self.assertTrue(bool(b.source_id))
            self.assertRegex(b.source_id, r"^(experience|project)_\d{3}_bullet_\d{3}$")

        # Now test through validation
        model_result = {
            "bullet_rewrites": {
                b.source_id: f"Engineered solution preserving source metrics {b.original}"
                for b in doc.all_bullets
            },
            # Attack: model tries to inject unrequested bullet
            "invented_bullet_id": "Invented rogue bullet",
            "new_bullets": [{"text": "Rogue bullet"}],
        }
        validated = _validate_optimized_structure(doc, model_result)
        reconstructed = validated["reconstructed_resume"]

        reconstructed_counts = [len(reconstructed["experience"][0]["bullets"])] + [
            len(p["bullets"]) for p in reconstructed["projects"]
        ]
        self.assertEqual(reconstructed_counts, [4, 2, 2, 1])
        self.assertEqual(len(validated["new_bullets"]), 0)

    # ------------------------------------------------------------
    # INVARIANT 2: No heading matching /Entry \d+/ and no duplicate headings
    # ------------------------------------------------------------
    def test_invariant_no_entry_heading_and_no_duplicate_headings(self):
        doc = self.doc
        # Attempt model injection of entry placeholders and duplicate section headers
        model_result = {
            "bullet_rewrites": {b.source_id: b.original for b in doc.all_bullets},
            "new_bullets": [
                {"new_company": "Projects Entry 1", "text": "Fake bullet", "is_new_entry": True}
            ],
            "optimized_summary": doc.summary,
        }
        validated = _validate_optimized_structure(doc, model_result)

        # Check in reconstructed experience & projects
        all_titles_and_orgs = []
        for e in validated["reconstructed_resume"]["experience"]:
            all_titles_and_orgs.extend([e.get("organization", ""), e.get("title", "")])
        for p in validated["reconstructed_resume"]["projects"]:
            all_titles_and_orgs.extend([p.get("organization", ""), p.get("title", "")])

        for text in all_titles_and_orgs:
            if text:
                self.assertIsNone(re.search(r"\bentry\s+\d+\b", text, re.I))

        # Check rendered PDF headings
        pdf = build_professional_resume_pdf(
            name=doc.name,
            email=doc.contact.get("email", ""),
            phone=doc.contact.get("phone", ""),
            linkedin=doc.contact.get("linkedin", ""),
            github=doc.contact.get("github", ""),
            location=doc.contact.get("location", ""),
            content=validated,
            source_resume_text=self.resume_text,
        )
        self.assertIsNotNone(pdf)

        # Check that no heading matches /Entry \d+/
        headings = list(pdf.emitted_headings)
        for h in headings:
            self.assertIsNone(re.search(r"\bentry\s+\d+\b", h, re.I))

        # Check no duplicate headings in PDF text
        pdf_text_upper = pdf.visible_text.upper()
        for expected_h in ["SUMMARY", "SKILLS", "EXPERIENCE", "PROJECTS", "EDUCATION", "CERTIFICATIONS"]:
            # Heading should occur at most once as a standalone section header
            matches = re.findall(rf"^\s*{expected_h}\s*$", pdf_text_upper, re.MULTILINE)
            self.assertLessEqual(len(matches), 1, f"Duplicate heading found for {expected_h}")

    # ------------------------------------------------------------
    # INVARIANT 3: skills_out ⊇ skills_src
    # ------------------------------------------------------------
    def test_invariant_skills_out_superset_of_skills_src(self):
        doc = self.doc
        # Source skills including parentheticals and bullet tech
        model_result = {
            "bullet_rewrites": {b.source_id: b.original for b in doc.all_bullets},
            # Model tries to return incomplete skills
            "optimized_skills": {
                "Languages": ["Python"],
            }
        }
        validated = _validate_optimized_structure(doc, model_result)
        out_skills = _flatten_skills(validated["optimized_skills"])
        out_skills_lower = {s.lower() for s in out_skills}

        expected_skills = [
            "python", "sql", "c++", "pytorch", "scikit-learn", "xgboost",
            "pandas", "numpy", "docker", "git", "ci/cd", "mlflow", "fastapi", "aws", "linux", "opencv"
        ]
        for s in expected_skills:
            self.assertTrue(
                any(s in out_s for out_s in out_skills_lower),
                f"Expected source skill '{s}' missing from output skills: {out_skills}"
            )

        # Also verify parenthetical preservation
        self.assertTrue(any("aws (s3, ec2)" in s.lower() for s in out_skills))

    # ------------------------------------------------------------
    # INVARIANT 4: Every source metric appears in the output
    # (500K+, 0.87, 38%, 40K+, 60+, 8,000, 0.71, 0.84, 200 ms, 54,000, 96%, 120+, 25, 0.91)
    # ------------------------------------------------------------
    def test_invariant_every_source_metric_appears_in_output(self):
        doc = self.doc
        # Model rewrite attempts to omit metrics or preserve them
        # When model rewrites drop metrics, code reverts to original
        dropped_metric_rewrites = {
            # Drops 500K+ and 0.87 -> code must revert to original!
            "experience_001_bullet_001": "Built customer churn model using XGBoost on customer records.",
            # Preserves 38% -> accepted
            "experience_001_bullet_002": "Optimized inference latency by 38% by exporting model to ONNX in FastAPI service.",
            # Preserves 40K+ -> accepted
            "experience_001_bullet_003": "Containerized service with Docker, serving 40K+ daily predictions to dashboard.",
            # Preserves 60+ -> accepted
            "experience_001_bullet_004": "Tracked 60+ experiments with MLflow, documenting reproducible feature pipelines.",
        }
        model_result = {"bullet_rewrites": dropped_metric_rewrites}
        validated = _validate_optimized_structure(doc, model_result)

        # Collect all output bullet text
        all_output_bullets = []
        for e in validated["reconstructed_resume"]["experience"]:
            all_output_bullets.extend(e["bullets"])
        for p in validated["reconstructed_resume"]["projects"]:
            all_output_bullets.extend(p["bullets"])
        combined_text = " ".join(all_output_bullets)

        required_metrics = [
            "500K+", "0.87", "38%", "40K+", "60+", "8,000",
            "0.71", "0.84", "200 ms", "54,000", "96%", "120+", "25", "0.91"
        ]
        for metric in required_metrics:
            self.assertIn(metric, combined_text, f"Metric '{metric}' missing from output bullets!")

    # ------------------------------------------------------------
    # INVARIANT 5: No "~" before a number
    # ------------------------------------------------------------
    def test_invariant_no_tilde_before_number(self):
        doc = self.doc
        # Attempt rewrite with "~" and "over ~"
        tilde_rewrites = {
            "experience_001_bullet_001": "Built churn model on ~500K+ records with F1-score of over ~0.87.",
            "experience_001_bullet_002": "Reduced latency by ~38% using ONNX and FastAPI.",
        }
        model_result = {"bullet_rewrites": tilde_rewrites}
        validated = _validate_optimized_structure(doc, model_result)

        all_output_text = []
        for e in validated["reconstructed_resume"]["experience"]:
            all_output_text.extend(e["bullets"])
        for p in validated["reconstructed_resume"]["projects"]:
            all_output_text.extend(p["bullets"])
        all_output_text.append(validated.get("optimized_summary", ""))

        joined = " ".join(all_output_text)
        self.assertIsNone(re.search(r"~\s*\d", joined), f"Found '~' before a number in: {joined}")
        self.assertIsNone(re.search(r"over\s*~\s*\d", joined, re.I), f"Found 'over ~' before a number in: {joined}")

    # ------------------------------------------------------------
    # INVARIANT 6: "8.4/10" appears in the education block
    # ------------------------------------------------------------
    def test_invariant_8_4_10_in_education_block(self):
        doc = self.doc
        validated = _validate_optimized_structure(doc, {})
        edu_list = validated["reconstructed_resume"]["education"]
        self.assertGreater(len(edu_list), 0)
        edu_text = " ".join(edu_list)
        self.assertIn("8.4/10", edu_text)

        # Also verify in rendered PDF
        pdf = build_professional_resume_pdf(
            name=doc.name,
            content=validated,
            source_resume_text=self.resume_text,
        )
        self.assertIn("8.4/10", pdf.visible_text)

    # ------------------------------------------------------------
    # INVARIANT 7: "github.com/rohanverma-demo" appears in full in the header
    # ------------------------------------------------------------
    def test_invariant_github_in_header(self):
        doc = self.doc
        validated = _validate_optimized_structure(doc, {})
        contact = validated["reconstructed_resume"]["contact"]
        self.assertIn("github.com/rohanverma-demo", contact.get("github", ""))

        pdf = build_professional_resume_pdf(
            name=doc.name,
            email=doc.contact.get("email", ""),
            phone=doc.contact.get("phone", ""),
            linkedin=doc.contact.get("linkedin", ""),
            github=doc.contact.get("github", ""),
            location=doc.contact.get("location", ""),
            content=validated,
            source_resume_text=self.resume_text,
        )
        self.assertIn("github.com/rohanverma-demo", pdf.visible_text)

    # ------------------------------------------------------------
    # INVARIANT 8: Summary: keep source verbatim unless rewrite passes grounding and > 15 words
    # ------------------------------------------------------------
    def test_invariant_summary_rules(self):
        doc = self.doc
        source_summary = doc.summary

        # Case A: Model rewrite is <= 15 words -> keep source verbatim
        short_summary = "Computer Science graduate with deep learning and FastAPI experience."
        self.assertLessEqual(len(short_summary.split()), 15)
        res_a = _validate_optimized_structure(
            doc,
            {"optimized_summary": short_summary, "bullet_rewrites": {}},
        )
        self.assertEqual(res_a["optimized_summary"], source_summary)

        # Case B: Model rewrite has ungrounded metric/tech -> keep source verbatim
        ungrounded_summary = (
            "Computer Science graduate with ML internship experience at Google. "
            "Delivered 99.9% uptime with Kubernetes microservices and Kafka streaming architectures."
        )
        self.assertGreater(len(ungrounded_summary.split()), 15)
        res_b = _validate_optimized_structure(
            doc,
            {"optimized_summary": ungrounded_summary, "bullet_rewrites": {}},
        )
        self.assertEqual(res_b["optimized_summary"], source_summary)

        # Case C: Model rewrite passes grounding and > 15 words -> replaces source
        valid_summary = (
            "Computer Science graduate with ML internship experience building and deploying machine learning models. "
            "Skilled in Python, PyTorch, scikit-learn, XGBoost, and FastAPI with proven experience evaluating models."
        )
        self.assertGreater(len(valid_summary.split()), 15)
        res_c = _validate_optimized_structure(
            doc,
            {"optimized_summary": valid_summary, "bullet_rewrites": {}},
        )
        self.assertEqual(res_c["optimized_summary"], valid_summary)

    # ------------------------------------------------------------
    # INVARIANT 9: Two runs produce the same structure
    # ------------------------------------------------------------
    def test_invariant_two_runs_produce_same_structure(self):
        doc = self.doc
        model_input = {
            "bullet_rewrites": {
                b.source_id: b.original for b in doc.all_bullets
            },
            "optimized_summary": doc.summary,
        }

        run_1 = _validate_optimized_structure(doc, dict(model_input))
        run_2 = _validate_optimized_structure(doc, dict(model_input))

        # Reconstructed resume hierarchy must be identical
        self.assertEqual(
            run_1["reconstructed_resume"],
            run_2["reconstructed_resume"],
        )
        self.assertEqual(run_1["optimized_summary"], run_2["optimized_summary"])
        self.assertEqual(run_1["optimized_skills"], run_2["optimized_skills"])


if __name__ == "__main__":
    unittest.main()
