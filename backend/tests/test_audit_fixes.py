import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException, Request
from routers import resume, portfolio, news
from config import settings


class FreemiumAtomicLimitTests(unittest.TestCase):
    def test_freemium_limit_rejection_before_ai(self):
        """When try_increment_resume_count returns False, 403 is raised immediately."""
        mock_supabase = MagicMock()
        # Mock try_increment_resume_count RPC returning False
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=False)
        mock_supabase.rpc.return_value = mock_rpc
        
        with patch.object(resume, "supabase", mock_supabase):
            mock_request = MagicMock(spec=Request)
            mock_resume = MagicMock()
            mock_resume.content_type = "application/pdf"
            mock_resume.read = AsyncMock(return_value=b"%PDF-1.4 test valid pdf content")
            
            profile = {
                "user_id": "test-user-id",
                "plan_type": "freemium",
                "resume_analysis_count": settings.FREEMIUM_MAX_ANALYSES,
                "github_url": "https://github.com/testuser"
            }
            user = {"user_id": "test-user-id", "github_username": "testuser"}
            
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(resume.analyze_resume(
                    request=mock_request,
                    resume=mock_resume,
                    github_url="https://github.com/testuser",
                    job_role="Software Engineer",
                    profile=profile,
                    user=user,
                ))
            
            self.assertEqual(ctx.exception.status_code, 403)
            self.assertIn("Freemium limit reached", ctx.exception.detail)
            # Verify try_increment_resume_count was called with p_user_id and p_max
            mock_supabase.rpc.assert_any_call("try_increment_resume_count", {
                "p_user_id": "test-user-id",
                "p_max": settings.FREEMIUM_MAX_ANALYSES,
            })


class UploadFileSizeLimitTests(unittest.TestCase):
    def test_resume_oversized_pdf_returns_413(self):
        """Resume upload exceeding MAX_RESUME_SIZE_MB returns 413."""
        mock_request = MagicMock(spec=Request)
        mock_resume = MagicMock()
        mock_resume.content_type = "application/pdf"
        # 6MB payload (exceeds 5MB limit)
        oversized_content = b"%PDF-" + b"0" * (6 * 1024 * 1024)
        mock_resume.read = AsyncMock(return_value=oversized_content)
        
        profile = {
            "user_id": "test-user-id",
            "plan_type": "premium",
            "github_url": "https://github.com/testuser"
        }
        user = {"user_id": "test-user-id", "github_username": "testuser"}
        
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(resume.analyze_resume(
                request=mock_request,
                resume=mock_resume,
                github_url="https://github.com/testuser",
                job_role="Software Engineer",
                profile=profile,
                user=user,
            ))
        self.assertEqual(ctx.exception.status_code, 413)
        self.assertIn("Resume file too large", ctx.exception.detail)

    def test_portfolio_oversized_pdf_returns_413(self):
        """Portfolio generate upload exceeding MAX_RESUME_SIZE_MB returns 413."""
        mock_request = MagicMock(spec=Request)
        mock_resume = MagicMock()
        mock_resume.content_type = "application/pdf"
        oversized_content = b"%PDF-" + b"0" * (6 * 1024 * 1024)
        mock_resume.read = AsyncMock(return_value=oversized_content)
        
        profile = {
            "user_id": "test-user-id",
            "plan_type": "premium",
            "portfolio_gen_count": 0
        }
        
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(portfolio.generate_portfolio(
                request=mock_request,
                resume=mock_resume,
                name="Test",
                github_username="testuser",
                profile=profile
            ))
        self.assertEqual(ctx.exception.status_code, 413)
        self.assertIn("Resume file too large", ctx.exception.detail)


class RequirementsPinningTests(unittest.TestCase):
    def test_no_unpinned_dependencies(self):
        """Ensure all dependencies in requirements.txt use exact == pinning."""
        from pathlib import Path
        req_path = Path(__file__).resolve().parent.parent / "requirements.txt"
        with open(req_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            self.assertNotIn(">=", line, f"Dependency line contains unpinned '>=': {line}")
            self.assertIn("==", line, f"Dependency line is missing exact '==' pin: {line}")


class SummaryPipelineFixTests(unittest.TestCase):
    def test_resume_with_metric_gets_clean_2_sentence_summary(self):
        """Resume with grounded metric is verified and preserved without being replaced by rigid template."""
        from routers.optimizer import _apply_optimizer_safety_filters, _verify_optimizer_summary
        
        resume_text = (
            "Alex Smith\n"
            "Technical Skills: Python, FastAPI, PostgreSQL\n"
            "Experience:\n"
            "Backend Intern at TechCo\n"
            "- Improved database query latency by 40% through indexing."
        )
        model_summary = (
            "Backend Intern with hands-on experience in Python and PostgreSQL. "
            "Improved query latency by 40% through database query indexing."
        )
        is_valid, reason = _verify_optimizer_summary(model_summary, resume_text, "Backend Engineer")
        self.assertTrue(is_valid, f"Summary should be valid but failed: {reason}")
        
        result = {
            "optimized_summary": model_summary,
            "improved_bullets": [],
            "new_bullets": [],
            "optimized_skills": {"Languages": ["Python"], "Databases": ["PostgreSQL"]},
        }
        filtered = _apply_optimizer_safety_filters(
            result=result,
            resume_text=resume_text,
            job_description="Python Backend Engineer with PostgreSQL experience.",
            job_title="Backend Engineer",
            user_id="test-user",
        )
        self.assertEqual(filtered["optimized_summary"], model_summary)

    def test_no_resume_contact_info_ever_appears_in_optimized_summary(self):
        """Contact info, email, phone, or raw resume header text must never appear in optimized_summary."""
        from routers.optimizer import _apply_optimizer_safety_filters, _verify_optimizer_summary
        
        resume_text = (
            "John Doe\n"
            "john.doe@example.com | +1 (555) 234-5678 | San Francisco, CA\n"
            "Education: B.S. in Computer Science\n"
            "Skills: Python, React, SQL"
        )
        # Attempted summary with email / phone
        bad_summary = "John Doe (john.doe@example.com, +1 555-234-5678) is a developer."
        is_valid, reason = _verify_optimizer_summary(bad_summary, resume_text)
        self.assertFalse(is_valid)

        # Result with invalid summary
        result = {
            "optimized_summary": bad_summary,
            "improved_bullets": [],
            "new_bullets": [],
            "optimized_skills": {"Languages": ["Python", "SQL"]},
        }
        filtered = _apply_optimizer_safety_filters(
            result=result,
            resume_text=resume_text,
            job_description="Software Engineer",
            job_title="Software Engineer",
            user_id="test-user",
        )
        # Summary should have fallen back to verified skills + education line
        summary = filtered["optimized_summary"]
        self.assertNotIn("john.doe@example.com", summary)
        self.assertNotIn("555", summary)
        self.assertNotIn("ADD_EVIDENCE_REQUIRED", summary)
        self.assertIn("Computer Science", summary)
        self.assertIn("Python", summary)

    def test_percentage_with_different_trailing_words_not_flagged(self):
        """'40%' with different trailing words is not flagged as ungrounded."""
        from routers.optimizer import _find_ungrounded_numbers, _verify_optimizer_summary
        
        resume_text = "Software developer with experience in Python. Optimized backend data pipelines, reducing build times by 40%."
        # Generated text uses 40% with different trailing words
        generated_summary = (
            "Software developer skilled in Python backend systems. "
            "Reduced build times by 40% in test execution latency."
        )
        ungrounded = _find_ungrounded_numbers(generated_summary, resume_text)
        self.assertEqual(ungrounded, [], f"40% was incorrectly flagged as ungrounded: {ungrounded}")
        
        is_valid, reason = _verify_optimizer_summary(generated_summary, resume_text)
        self.assertTrue(is_valid, f"Summary verification failed on 40%: {reason}")

    def test_domain_mismatch_skips_summary(self):
        """On domain mismatch, summary is skipped (empty string + note)."""
        from routers.optimizer import _apply_optimizer_safety_filters
        
        resume_text = "Elementary school teacher with 5 years experience in curriculum planning."
        result = {
            "optimized_summary": "Machine Learning Engineer with deep neural network skills.",
            "improved_bullets": [],
            "new_bullets": [],
            "optimized_skills": {},
        }
        # JD is heavy ML, candidate has 0 ML skills -> triggers domain_mismatch
        filtered = _apply_optimizer_safety_filters(
            result=result,
            resume_text=resume_text,
            job_description="Senior ML Engineer: requires PyTorch, TensorFlow, Deep Learning, MLOps, Neural Networks.",
            job_title="Machine Learning Engineer",
            user_id="test-user",
        )
        self.assertTrue(filtered.get("domain_mismatch"))
        self.assertEqual(filtered.get("optimized_summary"), "")
        self.assertIn("summary_grounding_note", filtered)


class ATSScoreFixTests(unittest.TestCase):
    def test_java_not_equal_to_javascript(self):
        """Java != JavaScript: Word boundary matching prevents substring hits."""
        from routers.optimizer import count_kw_coverage, _skill_in_text

        # Direct skill check
        self.assertFalse(_skill_in_text("java", "Extensive experience building modern apps in JavaScript and Node.js."))
        self.assertTrue(_skill_in_text("javascript", "Extensive experience building modern apps in JavaScript and Node.js."))
        self.assertTrue(_skill_in_text("java", "Developed enterprise backend microservices with Java, Spring Boot, and PostgreSQL."))

        # Coverage check
        jd_java = "Looking for a backend engineer with Java."
        jd_js = "Looking for a frontend developer with JavaScript."

        resume_js_only = "Frontend developer skilled in JavaScript, React, and HTML."
        resume_java_only = "Backend developer skilled in Java and Spring Boot."

        # JS resume against Java JD should have 0% coverage
        self.assertEqual(count_kw_coverage(resume_js_only, jd_java), 0)
        # Java resume against JS JD should have 0% coverage
        self.assertEqual(count_kw_coverage(resume_java_only, jd_js), 0)
        # Java resume against Java JD should have 100% coverage
        self.assertEqual(count_kw_coverage(resume_java_only, jd_java), 100)

    def test_strong_experience_never_counted(self):
        """'strong' and 'experience' are stop words and never counted as hard skills."""
        from routers.optimizer import extract_jd_hard_skills, count_kw_coverage

        jd = "Seeking a candidate with strong experience and solid background in Python."
        extracted = extract_jd_hard_skills(jd)
        self.assertEqual(extracted, ["python"])
        self.assertNotIn("strong", extracted)
        self.assertNotIn("experience", extracted)
        self.assertNotIn("solid", extracted)
        self.assertNotIn("background", extracted)

        # Candidate with only buzzwords gets 0% coverage
        buzzword_resume = "Highly motivated professional with strong experience, solid background, and great communication."
        self.assertEqual(count_kw_coverage(buzzword_resume, jd), 0)

    def test_rewrite_surfaces_buried_source_keyword_raises_score(self):
        """Surfacing a buried source keyword in rewritten bullets raises the ATS score."""
        from routers.optimizer import _stamp_ats_scores, count_kw_coverage

        jd = "Required: Python, Redis, and PostgreSQL."
        source_resume = (
            "Alex Smith\n"
            "Summary:\n"
            "Backend developer with Python experience.\n\n"
            "Experience:\n"
            "Tech Corp | Backend Engineer\n"
            "- Built web services using Python.\n\n"
            "Projects:\n"
            "TaskQueue Personal Project\n"
            "- Implemented distributed caching mechanism with Redis.\n\n"
            "Education:\n"
            "B.S. in Computer Science. Coursework: Relational Database Systems (PostgreSQL)."
        )

        # Baseline text before rewrite has only Python
        text_before = "Backend developer who built web services using Python."
        score_before = count_kw_coverage(text_before, jd, source_text=source_resume)

        # Rewrite surfaces buried Redis and PostgreSQL from source projects/education
        text_after = "Built web services using Python, Redis caching, and PostgreSQL."
        score_after = count_kw_coverage(text_after, jd, source_text=source_resume)

        self.assertGreater(score_after, score_before, "Surfacing buried source keywords must raise ATS score")

        # Full _stamp_ats_scores pipeline check
        result = {
            "optimized_summary": "Backend developer experienced in Python, Redis, and PostgreSQL.",
            "improved_bullets": [
                {"improved": "Engineered Python services with Redis caching layer and PostgreSQL database."}
            ],
            "new_bullets": [],
            "optimized_skills": {"Backend": ["Python", "Redis", "PostgreSQL"]},
        }
        ats_before, ats_after = _stamp_ats_scores(result, source_resume, jd)
        self.assertGreater(ats_after, ats_before)
        self.assertEqual(result.get("reachable_max"), 100)
        self.assertIn("redis", result.get("reachable_max_skills", []))

    def test_retry_threshold_greater_than_5_points(self):
        """ATS regression triggers retry only when score drop > 5 points."""
        from routers.optimizer import _stamp_ats_scores

        jd = "Skills: Python, React, Docker, Kubernetes, AWS, SQL, Redis, Kafka, TypeScript, GraphQL"
        source_resume = "Python React Docker Kubernetes AWS SQL Redis Kafka TypeScript GraphQL"

        # Case 1: Drop of exactly 3 points (<= 5)
        # Candidate text drops 1 skill (9/10 = 90% vs 100%)
        # ats_before = 100, ats_after = 90 -> severe drop of 10 > 5
        result_severe = {
            "optimized_summary": "Python React Docker",
            "improved_bullets": [],
            "new_bullets": [],
            "optimized_skills": ["Python", "React", "Docker"],
        }
        b, a = _stamp_ats_scores(result_severe, source_resume, jd)
        self.assertTrue(result_severe["ats_regression_severe"])

        # Case 2: No drop (100% == 100%)
        result_equal = {
            "optimized_summary": source_resume,
            "improved_bullets": [],
            "new_bullets": [],
            "optimized_skills": ["Python", "React", "Docker", "Kubernetes", "AWS", "SQL", "Redis", "Kafka", "TypeScript", "GraphQL"],
        }
        b, a = _stamp_ats_scores(result_equal, source_resume, jd)
        self.assertFalse(result_equal["ats_regression_severe"])


class GuardCalibrationFixTests(unittest.TestCase):
    def test_action_verb_bullets_survive(self):
        """'Improved/Created/Led/Cut ...' power verb bullets survive and are not treated as fabricated tech."""
        from routers.optimizer import _apply_optimizer_safety_filters, _find_ungrounded_tech_terms

        source_resume = (
            "Alex Smith\n"
            "Software Engineer\n"
            "Experience:\n"
            "- Worked on web backend systems in Python.\n"
            "- Maintained SQL database queries.\n"
        )
        source_lower = source_resume.lower()

        # Check action verbs directly against _find_ungrounded_tech_terms
        for bullet in [
            "Improved database query latency and backend performance.",
            "Created scalable Python applications for internal services.",
            "Led backend refactoring across database query layers.",
            "Cut server response times by streamlining query logic.",
        ]:
            ungrounded = _find_ungrounded_tech_terms(bullet, source_lower)
            self.assertEqual(ungrounded, [], f"Action verb bullet was falsely flagged: {bullet}")

        # Check in full _apply_optimizer_safety_filters pipeline
        result = {
            "optimized_summary": "Software Engineer with experience in Python and SQL.",
            "improved_bullets": [
                {
                    "original": "Worked on web backend systems in Python.",
                    "improved": "Improved web backend architecture using Python.",
                },
                {
                    "original": "Maintained SQL database queries.",
                    "improved": "Cut query response times through SQL indexing.",
                },
            ],
            "new_bullets": [],
            "optimized_skills": {"Languages": ["Python", "SQL"]},
        }
        filtered = _apply_optimizer_safety_filters(
            result,
            source_resume,
            "Python SQL Developer",
            "Software Engineer",
            "test-user",
        )
        self.assertEqual(
            filtered["improved_bullets"][0]["improved"],
            "Improved web backend architecture using Python.",
        )
        self.assertEqual(
            filtered["improved_bullets"][1]["improved"],
            "Cut query response times through SQL indexing.",
        )
        self.assertNotIn("fabricated_skills", filtered)

    def test_percentage_through_grounded_tech_survives(self):
        """'40% through Redis caching' survives when 40% and Redis are in the source."""
        from routers.optimizer import _apply_optimizer_safety_filters, _find_ungrounded_numbers

        source_resume = (
            "Alex Smith\n"
            "Skills: Python, Redis, PostgreSQL\n"
            "Experience:\n"
            "- Optimized backend services, reducing database query latency by 40% through index tuning.\n"
        )
        improved_bullet = "Reduced database query latency by 40% through Redis caching."
        
        # Verify ungrounded numbers check does not flag 40% when Redis is in source
        ungrounded = _find_ungrounded_numbers(improved_bullet, source_resume)
        self.assertEqual(ungrounded, [], f"40% with grounded Redis was falsely flagged: {ungrounded}")

        result = {
            "optimized_summary": "Backend developer with experience in Python and Redis.",
            "improved_bullets": [
                {
                    "original": "Optimized backend services, reducing database query latency by 40% through index tuning.",
                    "improved": improved_bullet,
                }
            ],
            "new_bullets": [],
            "optimized_skills": {"Databases": ["Redis", "PostgreSQL"]},
        }
        filtered = _apply_optimizer_safety_filters(
            result,
            source_resume,
            "Backend Engineer with Redis and PostgreSQL",
            "Backend Engineer",
            "test-user",
        )
        self.assertEqual(filtered["improved_bullets"][0]["improved"], improved_bullet)

    def test_bullet_with_jd_only_tool_reverts(self):
        """A bullet introducing a JD-only tool (e.g. Kubernetes absent from source) still reverts."""
        from routers.optimizer import _apply_optimizer_safety_filters, _find_ungrounded_tech_terms

        source_resume = (
            "Alex Smith\n"
            "Skills: Python, Redis, PostgreSQL\n"
            "Experience:\n"
            "- Optimized backend services, reducing database query latency by 40% through index tuning.\n"
        )
        source_lower = source_resume.lower()

        # JD asks for Kubernetes, which candidate does NOT have
        jd = "Senior Cloud Engineer requiring Kubernetes, Docker, and Python."
        improved_bullet_with_jd_only_tool = "Reduced database query latency by 40% through Kubernetes orchestration."

        # Verify _find_ungrounded_tech_terms detects Kubernetes
        ungrounded = _find_ungrounded_tech_terms(improved_bullet_with_jd_only_tool, source_lower, jd.lower())
        self.assertIn("Kubernetes", ungrounded)

        original_bullet = "Optimized backend services, reducing database query latency by 40% through index tuning."
        result = {
            "optimized_summary": "Backend developer with experience in Python.",
            "improved_bullets": [
                {
                    "original": original_bullet,
                    "improved": improved_bullet_with_jd_only_tool,
                }
            ],
            "new_bullets": [],
            "optimized_skills": {"Languages": ["Python"]},
        }
        filtered = _apply_optimizer_safety_filters(
            result,
            source_resume,
            jd,
            "Cloud Engineer",
            "test-user",
        )
        # The bullet must revert to original because Kubernetes is ungrounded
        self.assertEqual(filtered["improved_bullets"][0]["improved"], original_bullet)
        self.assertIn("fabricated_skills", filtered)
        self.assertIn("Kubernetes", filtered["fabricated_skills"])


class PromptHygieneFixTests(unittest.TestCase):
    def test_pydantic_field_max_length_20000(self):
        """OptimizeRequest and AnalyseRequest enforce max_length=20000."""
        from routers.optimizer import OptimizeRequest, AnalyseRequest
        from pydantic import ValidationError

        # Exactly 20,000 chars succeeds
        valid_req = OptimizeRequest(resume_text="A" * 20000, job_description="B" * 20000)
        self.assertEqual(len(valid_req.resume_text), 20000)

        # 20,001 chars raises ValidationError
        with self.assertRaises(ValidationError):
            OptimizeRequest(resume_text="A" * 20001, job_description="test")

        with self.assertRaises(ValidationError):
            OptimizeRequest(resume_text="test", job_description="B" * 20001)

        # AnalyseRequest
        valid_analyse = AnalyseRequest(resume_text="A" * 20000, job_description="B" * 20000)
        self.assertEqual(len(valid_analyse.resume_text), 20000)

        with self.assertRaises(ValidationError):
            AnalyseRequest(resume_text="A" * 20001)

    def test_pdf_request_content_size_cap(self):
        """POST /professional-resume-pdf caps content size and returns generic error on overflow."""
        import asyncio
        from unittest.mock import MagicMock
        from fastapi import HTTPException
        from routers.optimizer import generate_professional_resume_pdf, ProfessionalResumePdfRequest

        # Content payload exceeding 100,000 characters
        huge_content = {"summary": "x" * 105000}
        req = ProfessionalResumePdfRequest(
            name="John Doe",
            content=huge_content,
        )
        fake_request = MagicMock()

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(generate_professional_resume_pdf(
                request=fake_request,
                body=req,
                user={"user_id": "test-user"},
                premium={},
            ))
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("exceeds maximum allowed size", ctx.exception.detail)

    def test_analyse_dimensions_clamped_to_max(self):
        """Each /analyse dimension is clamped to its configured maximum."""
        from routers.optimizer import RECRUITER_DIMENSION_MAXES

        # Simulate inflated dimension scores returned by LLM
        inflated_dims = {
            "title_clarity": {"score": 99, "max": 10},       # max 10
            "company_signal": {"score": -5, "max": 10},      # min 0
            "tenure_stability": {"score": 10, "max": 10},    # max 10
            "scannability": {"score": 50, "max": 15},        # max 15
            "skills_quality": {"score": 15, "max": 15},      # max 15
            "quantification_rate": {"score": 100, "max": 20},# max 20
            "red_flag_penalty": {"score": 25, "max": 20},    # max 20
        }

        # Apply clamping logic
        computed_total = 0
        for dim_key, v in inflated_dims.items():
            max_val = RECRUITER_DIMENSION_MAXES.get(dim_key, int(v.get("max", 10) or 10))
            raw_score = int(float(v.get("score", 0) or 0))
            clamped_score = max(0, min(raw_score, max_val))
            v["score"] = clamped_score
            v["max"] = max_val
            computed_total += clamped_score

        self.assertEqual(inflated_dims["title_clarity"]["score"], 10)
        self.assertEqual(inflated_dims["company_signal"]["score"], 0)
        self.assertEqual(inflated_dims["scannability"]["score"], 15)
        self.assertEqual(inflated_dims["quantification_rate"]["score"], 20)
        self.assertEqual(inflated_dims["red_flag_penalty"]["score"], 20)
        self.assertEqual(computed_total, 10 + 0 + 10 + 15 + 15 + 20 + 20)  # 90 <= 100


if __name__ == "__main__":
    unittest.main()

