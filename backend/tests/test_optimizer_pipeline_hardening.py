# ============================================================
# CareerLens - Optimizer Pipeline Hardening Regression Tests
# File: backend/tests/test_optimizer_pipeline_hardening.py
# ============================================================

import asyncio
import json
import unittest
from unittest.mock import patch, MagicMock

from routers.optimizer import (
    _validate_against_source,
    _validate_optimized_structure,
    _apply_optimizer_safety_filters,
    _enforce_source_number_grounding,
    _stamp_ats_scores,
    count_kw_coverage,
    optimize_resume,
    OptimizeRequest,
    generate_structured_summary,
    SUMMARY_NOT_SUPPORTED,
)
from services.resume_structure import (
    parse_source_resume,
    build_source_items_for_prompt,
    reconstruct_resume_structure,
)
from services.professional_resume_pdf import build_professional_resume_pdf


class OptimizerPipelineHardeningTests(unittest.TestCase):
    def setUp(self):
        self.sample_resume = (
            "Alex Smith\n"
            "alex.smith@example.com | +1 555-123-4567 | San Francisco, CA | linkedin.com/in/alexsmith | github.com/alexsmith\n\n"
            "Summary\n"
            "Full stack engineer with experience in Python and PostgreSQL.\n\n"
            "Technical Skills\n"
            "Languages: Python, JavaScript, SQL\n"
            "Frameworks: FastAPI, React\n"
            "Databases: PostgreSQL, Redis\n\n"
            "Experience\n"
            "Acme Corp | Senior Backend Engineer | Jan 2021 - Present\n"
            "- Designed RESTful APIs handling 2M+ records with Python and PostgreSQL.\n"
            "- Improved database query latency by 42% through query optimization.\n\n"
            "Beta Tech | Software Engineer | Jun 2019 - Dec 2020\n"
            "- Built data synchronization pipeline processing 10k daily requests.\n\n"
            "Projects\n"
            "CareerLens Tool | Personal Project | Jan 2023 - May 2023\n"
            "- Developed full-stack resume analysis platform using FastAPI and React.\n\n"
            "TaskFlow | Open Source Project | Sep 2022 - Dec 2022\n"
            "- Implemented distributed task queue using Redis and Python.\n\n"
            "Education\n"
            "B.S. in Computer Science, Stanford University, 2019\n"
        )
        self.doc = parse_source_resume(self.sample_resume)

    # ------------------------------------------------------------
    # TEST 1: 2 experience entries + 2 projects remain 2 experience entries + 2 projects
    # ------------------------------------------------------------
    def test_1_entry_counts_preserved(self):
        self.assertEqual(self.doc.experience_count, 2)
        self.assertEqual(self.doc.project_count, 2)

        # Mock optimization output
        model_result = {
            "improved_bullets": [
                {
                    "source_id": "experience_001_bullet_001",
                    "original": "- Designed RESTful APIs handling 2M+ records with Python and PostgreSQL.",
                    "improved": "Architected high-throughput REST APIs processing 2M+ records with Python and PostgreSQL.",
                },
                {
                    "source_id": "experience_001_bullet_002",
                    "original": "- Improved database query latency by 42% through query optimization.",
                    "improved": "Optimized database query performance, reducing latency by 42%.",
                },
                {
                    "source_id": "experience_002_bullet_001",
                    "original": "- Built data synchronization pipeline processing 10k daily requests.",
                    "improved": "Engineered real-time data pipeline processing 10k daily requests.",
                },
                {
                    "source_id": "project_001_bullet_001",
                    "original": "- Developed full-stack resume analysis platform using FastAPI and React.",
                    "improved": "Engineered full-stack resume analysis platform using FastAPI and React.",
                },
                {
                    "source_id": "project_002_bullet_001",
                    "original": "- Implemented distributed task queue using Redis and Python.",
                    "improved": "Built asynchronous task processing system using Redis and Python.",
                },
            ]
        }
        validated = _validate_optimized_structure(self.doc, model_result)
        self.assertEqual(validated["optimized_experience_count"], 2)
        self.assertEqual(validated["optimized_project_count"], 2)
        self.assertEqual(len(validated["reconstructed_resume"]["experience"]), 2)
        self.assertEqual(len(validated["reconstructed_resume"]["projects"]), 2)

    # ------------------------------------------------------------
    # TEST 2: Experience bullet cannot become Project bullet
    # ------------------------------------------------------------
    def test_2_experience_bullet_cannot_become_project_bullet(self):
        # Attempt to claim an experience bullet as project
        model_result = {
            "improved_bullets": [
                {
                    "source_id": "experience_001_bullet_001",
                    "section": "projects",  # Corrupted section
                    "original": "Designed RESTful APIs handling 2M+ records with Python and PostgreSQL.",
                    "improved": "Optimized REST APIs handling 2M+ records with Python and PostgreSQL.",
                }
            ]
        }
        validated = _validate_optimized_structure(self.doc, model_result)
        bullet = next(b for b in validated["improved_bullets"] if b["source_id"] == "experience_001_bullet_001")
        self.assertEqual(bullet["section"], "experience")

        # In reconstructed resume, it must appear under experience, NOT projects
        exp_bullets = [
            b for entry in validated["reconstructed_resume"]["experience"]
            for b in entry["bullets"]
        ]
        proj_bullets = [
            b for entry in validated["reconstructed_resume"]["projects"]
            for b in entry["bullets"]
        ]
        self.assertIn("Optimized REST APIs handling 2M+ records with Python and PostgreSQL.", exp_bullets)
        self.assertNotIn("Optimized REST APIs handling 2M+ records with Python and PostgreSQL.", proj_bullets)

    # ------------------------------------------------------------
    # TEST 3: Project bullet cannot become Experience bullet
    # ------------------------------------------------------------
    def test_3_project_bullet_cannot_become_experience_bullet(self):
        # Attempt to claim a project bullet as experience
        model_result = {
            "improved_bullets": [
                {
                    "source_id": "project_001_bullet_001",
                    "section": "experience",  # Corrupted section
                    "original": "Developed full-stack resume analysis platform using FastAPI and React.",
                    "improved": "Engineered full-stack resume analysis platform using FastAPI and React.",
                }
            ]
        }
        validated = _validate_optimized_structure(self.doc, model_result)
        bullet = next(b for b in validated["improved_bullets"] if b["source_id"] == "project_001_bullet_001")
        self.assertEqual(bullet["section"], "projects")

        exp_bullets = [
            b for entry in validated["reconstructed_resume"]["experience"]
            for b in entry["bullets"]
        ]
        proj_bullets = [
            b for entry in validated["reconstructed_resume"]["projects"]
            for b in entry["bullets"]
        ]
        self.assertIn("Engineered full-stack resume analysis platform using FastAPI and React.", proj_bullets)
        self.assertNotIn("Engineered full-stack resume analysis platform using FastAPI and React.", exp_bullets)

    # ------------------------------------------------------------
    # TEST 4: JD contains Kubernetes. Resume does not. Kubernetes must NOT enter optimized_skills.
    # ------------------------------------------------------------
    def test_4_jd_only_skill_rejected_from_optimized_skills(self):
        result = {
            "optimized_skills": {
                "Cloud & DevOps": ["Kubernetes", "PostgreSQL"],
                "Languages": ["Python"],
            },
            "skills_to_highlight": ["Kubernetes", "Python"],
            "added_keywords": ["Kubernetes", "PostgreSQL"],
        }
        jd = "Senior Backend Engineer with Kubernetes microservices orchestration."
        validated = _validate_against_source(result, self.sample_resume, jd)

        self.assertNotIn("Kubernetes", validated["optimized_skills"]["Cloud & DevOps"])
        self.assertIn("PostgreSQL", validated["optimized_skills"]["Cloud & DevOps"])
        self.assertNotIn("Kubernetes", validated["skills_to_highlight"])
        self.assertNotIn("Kubernetes", validated["added_keywords"])
        self.assertIn("Kubernetes", validated["missing_keywords"])

    # ------------------------------------------------------------
    # TEST 5: JD contains Kubernetes. Resume does not. Kubernetes must NOT enter optimized bullet text.
    # ------------------------------------------------------------
    def test_5_jd_only_tech_rejected_from_bullet_text(self):
        model_result = {
            "improved_bullets": [
                {
                    "source_id": "experience_001_bullet_001",
                    "original": "Designed RESTful APIs handling 2M+ records with Python and PostgreSQL.",
                    "improved": "Orchestrated backend services using Kubernetes and Docker.",
                }
            ]
        }
        validated = _validate_optimized_structure(self.doc, model_result)
        # Bullet must be reverted to original because Kubernetes is ungrounded
        self.assertEqual(
            validated["improved_bullets"][0]["improved"],
            "Designed RESTful APIs handling 2M+ records with Python and PostgreSQL.",
        )
        self.assertNotIn("Kubernetes", validated["improved_bullets"][0]["improved"])

    # ------------------------------------------------------------
    # TEST 6: JD contains 99.9% uptime. Resume does not. 99.9% must NOT enter optimized resume.
    # ------------------------------------------------------------
    def test_6_jd_metric_cannot_enter_optimized_resume(self):
        result = {
            "improved_bullets": [
                {
                    "original": "Designed RESTful APIs handling 2M+ records with Python and PostgreSQL.",
                    "improved": "Maintained 99.9% uptime across production backend systems.",
                }
            ]
        }
        enforced = _enforce_source_number_grounding(result, self.sample_resume, "test-user")
        self.assertEqual(
            enforced["improved_bullets"][0]["improved"],
            "Designed RESTful APIs handling 2M+ records with Python and PostgreSQL.",
        )
        self.assertNotIn("99.9%", enforced["improved_bullets"][0]["improved"])

    # ------------------------------------------------------------
    # TEST 7: Source contains 2M+ records. Generated output says 10M+ records. Revert.
    # ------------------------------------------------------------
    def test_7_inflated_count_reverted(self):
        result = {
            "improved_bullets": [
                {
                    "original": "Designed RESTful APIs handling 2M+ records with Python and PostgreSQL.",
                    "improved": "Engineered REST APIs handling 10M+ records with Python and PostgreSQL.",
                }
            ]
        }
        enforced = _enforce_source_number_grounding(result, self.sample_resume, "test-user")
        self.assertEqual(
            enforced["improved_bullets"][0]["improved"],
            "Designed RESTful APIs handling 2M+ records with Python and PostgreSQL.",
        )

    # ------------------------------------------------------------
    # TEST 8: Source contains 42%. Generated output says 52%. Revert.
    # ------------------------------------------------------------
    def test_8_inflated_percentage_reverted(self):
        result = {
            "improved_bullets": [
                {
                    "original": "Improved database query latency by 42% through query optimization.",
                    "improved": "Reduced database latency by 52% through optimized indexing.",
                }
            ]
        }
        enforced = _enforce_source_number_grounding(result, self.sample_resume, "test-user")
        self.assertEqual(
            enforced["improved_bullets"][0]["improved"],
            "Improved database query latency by 42% through query optimization.",
        )

    # ------------------------------------------------------------
    # TEST 9: Source contains Python/Pandas. JD contains TensorFlow. Classified as gap.
    # ------------------------------------------------------------
    def test_9_skill_gap_classification(self):
        resume = "Skills: Python, Pandas\nExperience: Data analysis with Python."
        jd = "Machine Learning Engineer requiring TensorFlow and PyTorch."
        result = {
            "optimized_skills": ["Python", "TensorFlow"],
            "skills_to_highlight": ["TensorFlow"],
            "added_keywords": ["TensorFlow"],
        }
        validated = _validate_against_source(result, resume, jd)
        self.assertNotIn("TensorFlow", validated["optimized_skills"])
        self.assertNotIn("TensorFlow", validated["skills_to_highlight"])
        self.assertIn("TensorFlow", validated["missing_keywords"])

    # ------------------------------------------------------------
    # TEST 10: LLM returns unknown source_id. Generated item must be rejected.
    # ------------------------------------------------------------
    def test_10_unknown_source_id_rejected(self):
        model_result = {
            "improved_bullets": [
                {
                    "source_id": "non_existent_bullet_999",
                    "original": "Fabricated original",
                    "improved": "Fabricated improved bullet",
                }
            ]
        }
        validated = _validate_optimized_structure(self.doc, model_result)
        improved_texts = [b["improved"] for b in validated["improved_bullets"]]
        self.assertNotIn("Fabricated improved bullet", improved_texts)

    # ------------------------------------------------------------
    # TEST 11: LLM omits an original project. Original project must be restored.
    # ------------------------------------------------------------
    def test_11_omitted_project_restored(self):
        # Model returns bullets only for experience, completely omitting projects
        model_result = {
            "improved_bullets": [
                {
                    "source_id": "experience_001_bullet_001",
                    "original": "Designed RESTful APIs handling 2M+ records with Python and PostgreSQL.",
                    "improved": "Architected high-throughput REST APIs handling 2M+ records with Python and PostgreSQL.",
                }
            ]
        }
        validated = _validate_optimized_structure(self.doc, model_result)
        self.assertEqual(len(validated["reconstructed_resume"]["projects"]), 2)
        proj_names = [p["name"] for p in validated["reconstructed_resume"]["projects"]]
        self.assertIn("CareerLens Tool", proj_names)
        self.assertIn("TaskFlow", proj_names)

    # ------------------------------------------------------------
    # TEST 12: LLM changes company name. Reconstructed result preserves original.
    # ------------------------------------------------------------
    def test_12_company_name_preserved(self):
        model_result = {
            "improved_bullets": [],
            "new_bullets": [
                {"is_new_entry": True, "new_company": "Google", "text": "Invented Google job"}
            ]
        }
        validated = _validate_optimized_structure(self.doc, model_result)
        exp_orgs = [e["organization"] for e in validated["reconstructed_resume"]["experience"]]
        self.assertEqual(exp_orgs, ["Acme Corp", "Beta Tech"])
        self.assertNotIn("Google", exp_orgs)

    # ------------------------------------------------------------
    # TEST 13: LLM changes job dates. Reconstructed result preserves original.
    # ------------------------------------------------------------
    def test_13_job_dates_preserved(self):
        model_result = {"improved_bullets": []}
        validated = _validate_optimized_structure(self.doc, model_result)
        exp_dates = [e["dates"] for e in validated["reconstructed_resume"]["experience"]]
        self.assertEqual(exp_dates, ["Jan 2021 - Present", "Jun 2019 - Dec 2020"])

    # ------------------------------------------------------------
    # TEST 14: LLM creates a new project. Reconstructed result rejects it.
    # ------------------------------------------------------------
    def test_14_invented_project_rejected(self):
        model_result = {
            "improved_bullets": [],
            "new_bullets": [
                {"new_project": True, "text": "Invented blockchain protocol"}
            ]
        }
        validated = _validate_optimized_structure(self.doc, model_result)
        self.assertEqual(len(validated["reconstructed_resume"]["projects"]), 2)
        self.assertEqual(len(validated["new_bullets"]), 0)

    # ------------------------------------------------------------
    # TEST 15: Generated summary contains unsupported metric. Falls back safely.
    # ------------------------------------------------------------
    def test_15_unsupported_metric_in_summary_falls_back(self):
        result = {
            "optimized_summary": "Engineered systems achieving 99.9% uptime and $5M in revenue.",
            "original_summary": "Full stack engineer with experience in Python and PostgreSQL.",
        }
        enforced = _enforce_source_number_grounding(result, self.sample_resume, "test-user")
        self.assertNotIn("99.9%", enforced["optimized_summary"])
        self.assertNotIn("$5M", enforced["optimized_summary"])
        self.assertEqual(enforced["optimized_summary"], "Full stack engineer with experience in Python and PostgreSQL.")

    # ------------------------------------------------------------
    # TEST 16: Existing valid optimization output continues to render in frontend format.
    # ------------------------------------------------------------
    def test_16_frontend_contract_compatibility(self):
        model_result = {
            "improved_bullets": [
                {
                    "source_id": "experience_001_bullet_001",
                    "original": "Designed RESTful APIs handling 2M+ records with Python and PostgreSQL.",
                    "improved": "Architected high-throughput REST APIs handling 2M+ records with Python and PostgreSQL.",
                }
            ],
            "optimized_skills": ["Python", "FastAPI"],
            "optimized_summary": "Full stack engineer specializing in Python and PostgreSQL.",
            "added_keywords": ["FastAPI"],
            "missing_keywords": ["Kubernetes"],
            "ats_tips": ["Add microservices context"],
            "overall_improvement": "Enhanced API design descriptions.",
        }
        validated = _validate_optimized_structure(self.doc, model_result)

        # Frontend expects these keys to exist and be accessible:
        self.assertIn("improved_bullets", validated)
        self.assertIn("new_bullets", validated)
        self.assertIn("optimized_skills", validated)
        self.assertIn("optimized_summary", validated)
        self.assertIn("added_keywords", validated)
        self.assertIn("missing_keywords", validated)
        self.assertIn("experience_entries", validated)
        self.assertIn("project_entries", validated)
        self.assertIn("reconstructed_resume", validated)

    # ------------------------------------------------------------
    # TEST 17: Existing valid optimization output continues to generate a PDF.
    # ------------------------------------------------------------
    def test_17_pdf_generation_compatibility(self):
        model_result = {
            "improved_bullets": [
                {
                    "source_id": "experience_001_bullet_001",
                    "original": "Designed RESTful APIs handling 2M+ records with Python and PostgreSQL.",
                    "improved": "Architected high-throughput REST APIs handling 2M+ records with Python and PostgreSQL.",
                }
            ],
            "optimized_skills": ["Python", "PostgreSQL"],
            "optimized_summary": "Software engineer specializing in backend systems.",
        }
        validated = _validate_optimized_structure(self.doc, model_result)

        pdf = build_professional_resume_pdf(
            name="Alex Smith",
            email="alex.smith@example.com",
            phone="+1 555-123-4567",
            linkedin="linkedin.com/in/alexsmith",
            github="github.com/alexsmith",
            location="San Francisco, CA",
            content=validated,
            source_resume_text=self.sample_resume,
        )
        self.assertIsNotNone(pdf)
        self.assertGreater(len(pdf.pdf_bytes), 1000)
        self.assertIn("Alex Smith", pdf.visible_text)
        self.assertIn("EXPERIENCE", pdf.visible_text.upper())
        self.assertIn("PROJECTS", pdf.visible_text.upper())

    # ------------------------------------------------------------
    # TEST 18: Existing authentication and premium checks continue working.
    # ------------------------------------------------------------
    def test_18_auth_and_premium_dependencies(self):
        from middleware.auth import get_authenticated_user, require_premium
        from fastapi import HTTPException

        # Mock request without authorization header
        mock_request = MagicMock()
        mock_request.headers = {}
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(get_authenticated_user(mock_request))
        self.assertEqual(ctx.exception.status_code, 401)

        # Mock non-premium user profile
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(require_premium(profile={"plan_type": "free"}))
        self.assertEqual(ctx.exception.status_code, 403)

    # ------------------------------------------------------------
    # TEST 19: Existing rate limiting continues working.
    # ------------------------------------------------------------
    def test_19_rate_limiting_configured(self):
        from rate_limit import limiter
        self.assertIsNotNone(limiter)
        self.assertTrue(hasattr(limiter, "limit"))


if __name__ == "__main__":
    unittest.main()
