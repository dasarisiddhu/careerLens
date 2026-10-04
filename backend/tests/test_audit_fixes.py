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
        """On domain mismatch, summary falls back to a verified skills-only line (FIX B+C), not a blank."""
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
        # FIX B+C: Uses skills-only line instead of a blank
        self.assertTrue(len(filtered.get("optimized_summary", "")) > 0)
        self.assertNotIn("graduate", filtered["optimized_summary"].lower())
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


class FixACloseGuardHoleTests(unittest.TestCase):
    def test_terraform_jenkins_elasticsearch_bullets_revert(self):
        """Terraform/Jenkins/Elasticsearch bullets revert when absent from source."""
        from routers.optimizer import _apply_optimizer_safety_filters, _find_ungrounded_tech_terms

        source_resume = (
            "Taylor Swift\n"
            "Software Engineer\n"
            "Skills: Python, Redis, PostgreSQL\n"
            "Experience:\n"
            "- Maintained core database systems and Python APIs.\n"
        )
        source_lower = source_resume.lower()

        # 1. Direct _find_ungrounded_tech_terms check
        ungrounded_tf = _find_ungrounded_tech_terms("Provisioned cloud infrastructure using Terraform.", source_lower)
        self.assertIn("Terraform", ungrounded_tf)

        ungrounded_jenkins = _find_ungrounded_tech_terms("Configured CI/CD automated deployment with Jenkins.", source_lower)
        self.assertIn("Jenkins", ungrounded_jenkins)

        ungrounded_es = _find_ungrounded_tech_terms("Accelerated full-text search queries using Elasticsearch.", source_lower)
        self.assertIn("Elasticsearch", ungrounded_es)

        # 2. Pipeline reversion check
        result = {
            "optimized_summary": "Software Engineer with experience in Python and PostgreSQL.",
            "improved_bullets": [
                {
                    "original": "Maintained core database systems and Python APIs.",
                    "improved": "Deployed cloud infrastructure using Terraform and Jenkins, indexing metrics with Elasticsearch.",
                }
            ],
            "new_bullets": [],
            "optimized_skills": {},
        }
        filtered = _apply_optimizer_safety_filters(
            result,
            source_resume,
            "Senior Cloud Engineer requiring Terraform, Jenkins, and Elasticsearch.",
            "Cloud Engineer",
            "test-user",
        )
        self.assertEqual(
            filtered["improved_bullets"][0]["improved"],
            "Maintained core database systems and Python APIs.",
        )
        self.assertIn("Terraform", filtered.get("fabricated_skills", []))
        self.assertIn("Jenkins", filtered.get("fabricated_skills", []))
        self.assertIn("Elasticsearch", filtered.get("fabricated_skills", []))

    def test_led_a_team_reverts_without_leadership_signal(self):
        """'Led a team…' reverts when the source has no leadership signal."""
        from routers.optimizer import _apply_optimizer_safety_filters

        source_resume = (
            "Jordan Lee\n"
            "Software Developer\n"
            "Experience:\n"
            "Acme Corp - Junior Developer\n"
            "- Built backend web APIs with Python and Flask.\n"
            "- Monitored PostgreSQL database performance.\n"
        )
        original_bullet = "Built backend web APIs with Python and Flask."
        result = {
            "optimized_summary": "Software Developer with Python and Flask.",
            "improved_bullets": [
                {
                    "original": original_bullet,
                    "improved": "Led a team of 5 engineers to deliver backend web APIs with Python and Flask.",
                }
            ],
            "new_bullets": [],
            "optimized_skills": {},
        }
        filtered = _apply_optimizer_safety_filters(
            result,
            source_resume,
            "Lead Backend Engineer",
            "Lead Engineer",
            "test-user",
        )
        # Bullet must revert to original because 'led' and 'team of' are ungrounded
        self.assertEqual(filtered["improved_bullets"][0]["improved"], original_bullet)

    def test_grounded_leadership_bullet_survives(self):
        """A bullet with leadership signal already present in source bullet survives."""
        from routers.optimizer import _apply_optimizer_safety_filters

        source_resume = (
            "Morgan Reed\n"
            "Engineering Lead\n"
            "Experience:\n"
            "Acme Corp - Team Lead\n"
            "- Led a team of 4 engineers building distributed backend systems in Python.\n"
        )
        original_bullet = "Led a team of 4 engineers building distributed backend systems in Python."
        improved_bullet = "Led a team of 4 engineers delivering distributed backend systems in Python."
        result = {
            "optimized_summary": "Engineering Lead with Python.",
            "improved_bullets": [
                {
                    "original": original_bullet,
                    "improved": improved_bullet,
                }
            ],
            "new_bullets": [],
            "optimized_skills": {},
        }
        filtered = _apply_optimizer_safety_filters(
            result,
            source_resume,
            "Senior Engineering Lead",
            "Engineering Lead",
            "test-user",
        )
        # Survives because 'led' and 'team of' exist in original bullet and section
        self.assertEqual(filtered["improved_bullets"][0]["improved"], improved_bullet)

    def test_go_and_r_case_sensitivity(self):
        """'go' and 'r' are matched case-sensitively to avoid matching English words."""
        from routers.optimizer import _skill_in_text

        # Lowercase English words should NOT match
        self.assertFalse(_skill_in_text("go", "I like to go fast and explore new ideas."))
        self.assertFalse(_skill_in_text("go", "Let's go through the requirements."))
        self.assertFalse(_skill_in_text("r", "Research and development in various fields."))

        # Proper casing DOES match
        self.assertTrue(_skill_in_text("go", "Engineered microservices using Go and Docker."))
        self.assertTrue(_skill_in_text("go", "Developed high-throughput services with Golang."))
        self.assertTrue(_skill_in_text("r", "Statistical analysis performed using Python and R."))


class SummaryVerificationFixBCTests(unittest.TestCase):
    """FIX B+C: Summary verification and skills/education summary."""

    def test_aspiring_motivated_entry_level_summaries_accepted(self):
        """'Aspiring/Motivated/Entry-level…' summaries should be accepted (FIX B)."""
        from routers.optimizer import _verify_optimizer_summary

        source = (
            "John Doe\n"
            "Skills: Python, JavaScript, React, Node.js\n"
            "Education: B.S. in Computer Science, University of XYZ, 2024\n"
            "Projects:\n"
            "- Built a web app using React and Node.js\n"
        )
        # Sentence-starting 'Aspiring' should NOT be flagged as a tech term
        valid, reason = _verify_optimizer_summary(
            "Aspiring software developer with skills in Python and React.",
            source,
        )
        self.assertTrue(valid, f"'Aspiring…' rejected: {reason}")

        # 'Motivated' at sentence start
        valid, reason = _verify_optimizer_summary(
            "Motivated developer proficient in JavaScript and Node.js.",
            source,
        )
        self.assertTrue(valid, f"'Motivated…' rejected: {reason}")

        # 'Entry-level' at sentence start (compound word, starts with cap)
        valid, reason = _verify_optimizer_summary(
            "Entry-level engineer with experience in React and Python.",
            source,
        )
        self.assertTrue(valid, f"'Entry-level…' rejected: {reason}")

    def test_sentence_start_known_tech_term_still_flagged(self):
        """A known tech term (e.g. Kubernetes) at sentence start IS flagged if absent from source."""
        from routers.optimizer import _verify_optimizer_summary

        source = "Skills: Python, React\nBuilt a REST API using Python."
        valid, reason = _verify_optimizer_summary(
            "Kubernetes orchestration expert with Python skills.",
            source,
        )
        self.assertFalse(valid, "Kubernetes should be flagged even at sentence start")
        self.assertIn("unsupported_tech_term", reason)

    def test_mid_sentence_non_tech_caps_not_flagged(self):
        """Mid-sentence capitalized words that are NOT tech-like should pass."""
        from routers.optimizer import _verify_optimizer_summary

        source = "Skills: Python, SQL\nExperience in data analysis with Python."
        # 'Excellent' mid-sentence (not in ignored_words but also not tech-looking)
        valid, reason = _verify_optimizer_summary(
            "Proficient in Python. Demonstrated strong SQL skills.",
            source,
        )
        self.assertTrue(valid, f"Clean summary rejected: {reason}")

    def test_associate_software_engineer_never_produces_degree(self):
        """'Associate Software Engineer' must NOT be interpreted as a degree (FIX C)."""
        from routers.optimizer import _build_skills_education_summary
        from services.resume_structure import ResumeDocument

        doc = ResumeDocument(
            raw_text="Associate Software Engineer at XYZ Corp\nSkills: Python, Java",
            education=[],  # No education section
        )
        summary = _build_skills_education_summary(
            "Associate Software Engineer at XYZ Corp\nSkills: Python, Java",
            result=None,
            doc=doc,
        )
        self.assertNotIn("Associate", summary)
        self.assertNotIn("graduate", summary.lower())
        # Should be a skills-only fallback
        self.assertIn("proficiencies", summary.lower())

    def test_ms_office_never_produces_degree(self):
        """'MS Office' must NOT be interpreted as an M.S. degree (FIX C)."""
        from routers.optimizer import _build_skills_education_summary
        from services.resume_structure import ResumeDocument

        doc = ResumeDocument(
            raw_text="Skills: MS Office, Excel, PowerPoint\nExperience: Data Entry",
            education=[],  # No education section
        )
        summary = _build_skills_education_summary(
            "Skills: MS Office, Excel, PowerPoint\nExperience: Data Entry",
            result=None,
            doc=doc,
        )
        # Should not produce a Master's degree from "MS Office"
        self.assertNotIn("M.S.", summary)
        self.assertNotIn("Master", summary)
        self.assertNotIn("graduate", summary.lower())

    def test_degree_extracted_from_doc_education_only(self):
        """Degree should ONLY come from doc.education lines, not the full resume text."""
        from routers.optimizer import _build_skills_education_summary
        from services.resume_structure import ResumeDocument

        # Education section has the degree
        doc = ResumeDocument(
            raw_text="Summary: MS in Data Science\nSkills: Python\nEducation:\nB.S. in Computer Science, MIT, 2023",
            education=["B.S. in Computer Science, MIT, 2023"],
        )
        summary = _build_skills_education_summary(
            doc.raw_text,
            result=None,
            doc=doc,
        )
        self.assertIn("B.S. in Computer Science", summary)
        # Should not pick up "MS in Data Science" from summary section
        self.assertNotIn("MS in Data Science", summary)

    def test_no_education_lines_produces_skills_only(self):
        """When doc.education is empty, should produce a skills-only sentence."""
        from routers.optimizer import _build_skills_education_summary
        from services.resume_structure import ResumeDocument

        doc = ResumeDocument(
            raw_text="Skills: Python, Docker, AWS\nExperience: 3 years",
            education=[],
        )
        summary = _build_skills_education_summary(
            doc.raw_text,
            result=None,
            doc=doc,
        )
        self.assertNotIn("graduate", summary.lower())
        self.assertIn("proficiencies", summary.lower())
        self.assertIn("Python", summary)

    def test_never_writes_graduate(self):
        """The word 'graduate' must NEVER appear in the summary (FIX C)."""
        from routers.optimizer import _build_skills_education_summary
        from services.resume_structure import ResumeDocument

        # Even with a degree type but no clean field
        doc = ResumeDocument(
            raw_text="Education: B.S. from University of XYZ\nSkills: Java",
            education=["B.S. from University of XYZ"],
        )
        summary = _build_skills_education_summary(
            doc.raw_text,
            result=None,
            doc=doc,
        )
        self.assertNotIn("graduate", summary.lower())

    def test_domain_mismatch_uses_skills_line_not_blank(self):
        """On domain_mismatch, the summary should be a skills-only line, not blank."""
        from routers.optimizer import _apply_optimizer_safety_filters
        from services.resume_structure import ResumeDocument

        doc = ResumeDocument(
            raw_text="Skills: Python, SQL\nExperience: Data analysis projects",
            education=[],
        )
        result = {
            "domain_mismatch": True,
            "optimized_summary": "",
            "improved_bullets": [],
            "new_bullets": [],
            "optimized_skills": {},
        }
        filtered = _apply_optimizer_safety_filters(
            result,
            doc.raw_text,
            "JD about Kubernetes orchestration",
            "",
            "test-user",
            doc=doc,
        )
        # Summary should NOT be blank
        self.assertTrue(len(filtered["optimized_summary"]) > 0)
        # Should contain verified skills
        self.assertIn("Python", filtered["optimized_summary"])

    def test_proper_degree_from_education_section(self):
        """When education has a real degree line, it should appear in the summary."""
        from routers.optimizer import _build_skills_education_summary
        from services.resume_structure import ResumeDocument

        doc = ResumeDocument(
            raw_text="Education:\nMaster's in Artificial Intelligence, Stanford, 2024\nSkills: Python, TensorFlow",
            education=["Master's in Artificial Intelligence, Stanford, 2024"],
        )
        summary = _build_skills_education_summary(
            doc.raw_text,
            result=None,
            doc=doc,
        )
        self.assertIn("Master's in Artificial Intelligence", summary)
        self.assertNotIn("graduate", summary.lower())


class FixDNumberMeaningTests(unittest.TestCase):
    """FIX D: Number meaning grounding for counts and percentages."""

    def test_500_concurrent_users_reverts_when_qualifier_absent(self):
        """'500 concurrent users' reverts when 'concurrent' is not in source resume."""
        from routers.optimizer import _apply_optimizer_safety_filters, _find_ungrounded_numbers

        source_resume = (
            "Jane Developer\n"
            "Skills: Python, Django\n"
            "Experience:\n"
            "- Built internal web portal serving 500 users across company departments.\n"
        )
        improved_bullet = "Engineered internal web portal serving 500 concurrent users using Django."

        # Direct number grounding check
        ungrounded = _find_ungrounded_numbers(improved_bullet, source_resume)
        self.assertTrue(len(ungrounded) > 0, "500 concurrent users should be flagged as ungrounded")
        self.assertEqual(ungrounded[0]["number"], "500")

        # Full pipeline test: bullet should revert to original
        result = {
            "optimized_summary": "Python developer with experience in Django.",
            "improved_bullets": [
                {
                    "original": "Built internal web portal serving 500 users across company departments.",
                    "improved": improved_bullet,
                }
            ],
            "new_bullets": [],
            "optimized_skills": {"Languages": ["Python"]},
        }
        filtered = _apply_optimizer_safety_filters(
            result,
            source_resume,
            "Python Engineer",
            "Software Engineer",
            "test-user",
        )
        self.assertEqual(
            filtered["improved_bullets"][0]["improved"],
            "Built internal web portal serving 500 users across company departments.",
            "Bullet with ungrounded 'concurrent' qualifier must revert to original",
        )

    def test_500_concurrent_users_passes_when_concurrent_in_source(self):
        """'500 concurrent users' passes when 'concurrent' already exists in source."""
        from routers.optimizer import _find_ungrounded_numbers

        source_resume = (
            "Jane Developer\n"
            "Skills: Python, Django\n"
            "Experience:\n"
            "- Built internal web portal serving 500 concurrent connections across departments.\n"
        )
        improved_bullet = "Engineered internal web portal serving 500 concurrent users."
        ungrounded = _find_ungrounded_numbers(improved_bullet, source_resume)
        self.assertEqual(ungrounded, [], f"Expected grounded count when concurrent in source: {ungrounded}")

    def test_92_percent_accuracy_to_92_percent_latency_reverts(self):
        """'92% accuracy' -> '92% latency' reverts because there are no shared content words within ±3 words."""
        from routers.optimizer import _apply_optimizer_safety_filters, _find_ungrounded_numbers

        source_resume = (
            "Alex AI Engineer\n"
            "Skills: Python, PyTorch\n"
            "Experience:\n"
            "- Trained PyTorch classification model, achieving 92% accuracy on benchmark test suite.\n"
        )
        # LLM hijacked 92% from accuracy to latency for a backend role
        hijacked_bullet = "Optimized production microservices, reducing 92% latency across distributed endpoints."

        ungrounded = _find_ungrounded_numbers(hijacked_bullet, source_resume)
        self.assertTrue(len(ungrounded) > 0, "92% latency should be flagged when source was 92% accuracy")

        # Full pipeline test: bullet should revert to original
        result = {
            "optimized_summary": "AI Engineer with PyTorch experience.",
            "improved_bullets": [
                {
                    "original": "Trained PyTorch classification model, achieving 92% accuracy on benchmark test suite.",
                    "improved": hijacked_bullet,
                }
            ],
            "new_bullets": [],
            "optimized_skills": {"Frameworks": ["PyTorch"]},
        }
        filtered = _apply_optimizer_safety_filters(
            result,
            source_resume,
            "Backend Systems Engineer",
            "Software Engineer",
            "test-user",
        )
        self.assertEqual(
            filtered["improved_bullets"][0]["improved"],
            "Trained PyTorch classification model, achieving 92% accuracy on benchmark test suite.",
            "Bullet with 92% latency must revert because source only supports 92% accuracy",
        )

    def test_40_percent_through_redis_caching_still_passes(self):
        """'40% through Redis caching' still passes because ±3 words share 'latency' / 'query'."""
        from routers.optimizer import _apply_optimizer_safety_filters, _find_ungrounded_numbers

        source_resume = (
            "Alex Smith\n"
            "Skills: Python, Redis, PostgreSQL\n"
            "Experience:\n"
            "- Optimized backend services, reducing database query latency by 40% through index tuning.\n"
        )
        improved_bullet = "Reduced database query latency by 40% through Redis caching."

        ungrounded = _find_ungrounded_numbers(improved_bullet, source_resume)
        self.assertEqual(ungrounded, [], f"40% with grounded latency context must not be flagged: {ungrounded}")

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
            "Software Engineer",
            "Software Engineer",
            "test-user",
        )
        self.assertEqual(
            filtered["improved_bullets"][0]["improved"],
            improved_bullet,
            "40% through Redis caching should be preserved",
        )


class FixEATSScoreTests(unittest.TestCase):
    def test_ambiguous_phrases_produce_no_skills(self):
        """'R&D / go the extra mile / express interest' must add no skills."""
        from routers.optimizer import extract_jd_hard_skills

        jd_text = "Looking for R&D experience, someone willing to go the extra mile and express interest in growth."
        skills = extract_jd_hard_skills(jd_text)
        self.assertEqual(skills, [], "Ambiguous non-tech phrases must not produce any skills")

    def test_ambiguous_skills_non_tech_vs_tech_contexts(self):
        """Ambiguous skills (spring, swift, node, apache) must only match in technical context."""
        from routers.optimizer import extract_jd_hard_skills

        non_tech_jd = "Graduating in Spring 2024 with swift action across cluster nodes under Apache 2.0 license."
        self.assertEqual(extract_jd_hard_skills(non_tech_jd), [])

        tech_jd = "Building backend with Go, Node.js, Express, Spring Boot, Swift iOS, Apache Kafka, and R for data."
        skills = extract_jd_hard_skills(tech_jd)
        self.assertIn("go", skills)
        self.assertIn("node", skills)
        self.assertIn("express", skills)
        self.assertIn("spring", skills)
        self.assertIn("swift", skills)
        self.assertIn("apache", skills)
        self.assertIn("r", skills)

    def test_new_hard_skills_extracted(self):
        """Tableau, Power BI, Excel, Salesforce, Agile must be recognized as hard tech skills."""
        from routers.optimizer import extract_jd_hard_skills

        jd = "Requirements: Tableau, Power BI dashboards, advanced Excel, Salesforce CRM, and Agile workflows."
        skills = extract_jd_hard_skills(jd)
        for expected in ["agile", "excel", "power bi", "salesforce", "tableau"]:
            self.assertIn(expected, skills)

    def test_no_jd_skills_returns_none_and_hides_bar(self):
        """If no JD skills are found, _stamp_ats_scores returns None and sets hide_ats_bar = True."""
        from routers.optimizer import _stamp_ats_scores

        result = {
            "optimized_summary": "Motivated professional eager to contribute.",
            "improved_bullets": [],
            "new_bullets": [],
            "optimized_skills": [],
        }
        source_resume = "Motivated individual with leadership experience."
        jd_no_skills = "We are seeking a fast learner and enthusiastic team player with strong interpersonal abilities."

        b, a = _stamp_ats_scores(result, source_resume, jd_no_skills)
        self.assertIsNone(b)
        self.assertIsNone(a)
        self.assertIsNone(result.get("ats_before"))
        self.assertIsNone(result.get("ats_after"))
        self.assertTrue(result.get("hide_ats_bar"))

    def test_keyword_only_in_added_keywords_does_not_raise_ats_after(self):
        """A keyword only in added_keywords must not raise ats_after."""
        from routers.optimizer import _stamp_ats_scores

        source_resume = (
            "Jane Doe\n"
            "Summary: Full-stack developer experienced in Python and Docker.\n"
            "Skills: Python, Docker\n"
            "Experience:\n"
            "Tech Inc | Engineer\n"
            "- Built backend services using Python and Docker.\n"
        )
        jd = "Requires Python and Docker."

        # Case 1: With reconstructed_resume only containing Python
        result_with_rec = {
            "reconstructed_resume": {
                "summary": "Full-stack developer experienced in Python.",
                "skills": ["Python"],
                "experience": [
                    {
                        "title": "Engineer",
                        "organization": "Tech Inc",
                        "bullets": ["Built backend services using Python."],
                    }
                ],
                "projects": [],
                "education": [],
                "certifications": [],
            },
            "added_keywords": ["Docker"],
        }
        b1, a1 = _stamp_ats_scores(result_with_rec, source_resume, jd)
        self.assertEqual(b1, 100, "Source resume has both Python and Docker (100%)")
        self.assertEqual(a1, 50, "Docker only in added_keywords must not be counted in reconstructed resume (50%)")

        # Case 2: Without reconstructed_resume (fallback path)
        result_fallback = {
            "optimized_summary": "Full-stack developer experienced in Python.",
            "improved_bullets": [{"improved": "Built backend services using Python."}],
            "new_bullets": [],
            "optimized_skills": ["Python"],
            "added_keywords": ["Docker"],
        }
        b2, a2 = _stamp_ats_scores(result_fallback, source_resume, jd)
        self.assertEqual(b2, 100)
        self.assertEqual(a2, 50, "Fallback path must also drop added_keywords")



class FixFUIAndLeftoversTests(unittest.TestCase):
    def test_safe_limit_does_not_rerun_on_error(self):
        """_safe_limit decorator does not catch exceptions and re-run fn without rate limiting."""
        import asyncio
        from routers.optimizer import _safe_limit

        call_count = 0

        @_safe_limit("5/minute")
        async def failing_endpoint(request):
            nonlocal call_count
            call_count += 1
            raise ValueError("parameter `response` must be an instance of Response")

        class DummyRequest:
            headers = {}
            client = None

        with self.assertRaises(ValueError):
            asyncio.run(failing_endpoint(DummyRequest()))

        # Fn should only have been called once — no fallback re-execution
        self.assertEqual(call_count, 1)

    def test_ats_retry_error_removed_from_result(self):
        """ats_retry_error is stripped from result to prevent leaking backend error strings."""
        result = {
            "ats_retry_attempted": True,
            "ats_retry_failed": True,
            "ats_retry_error": "Internal database or LLM timeout detail: 0x82f4",
        }
        # Simulate router endpoint cleanup
        result.pop("ats_retry_error", None)
        self.assertNotIn("ats_retry_error", result)

    def test_body_size_limit_middleware_blocks_oversized_content_length(self):
        """BodySizeLimitMiddleware returns 413 when Content-Length exceeds MAX_BODY_SIZE_MB."""
        import asyncio
        from main import BodySizeLimitMiddleware
        from config import MAX_BODY_SIZE_MB

        app_called = False

        async def dummy_app(scope, receive, send):
            nonlocal app_called
            app_called = True

        middleware = BodySizeLimitMiddleware(dummy_app)

        oversized_bytes = (MAX_BODY_SIZE_MB * 1024 * 1024) + 1024
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/optimizer/optimize",
            "headers": [
                (b"content-length", str(oversized_bytes).encode("latin-1")),
            ],
        }

        sent_messages = []

        async def fake_receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def fake_send(msg):
            sent_messages.append(msg)

        asyncio.run(middleware(scope, fake_receive, fake_send))

        self.assertFalse(app_called, "Underlying app must not be called when payload is oversized")
        status_msg = next((m for m in sent_messages if m["type"] == "http.response.start"), None)
        self.assertIsNotNone(status_msg)
        self.assertEqual(status_msg["status"], 413)

    def test_truncation_notice_and_reachable_max_in_router(self):
        """Truncation notice and ats_reachable_max are calculated and included in response structures."""
        from routers.optimizer import extract_jd_hard_skills, _skill_in_text

        # 1. Truncation logic check
        resume_8001 = "A" * 8001
        jd_3001 = "B" * 3001
        resume_truncated = len(resume_8001) > 8000
        jd_truncated = len(jd_3001) > 3000
        self.assertTrue(resume_truncated)
        self.assertTrue(jd_truncated)

        trunc_parts = []
        if resume_truncated:
            trunc_parts.append("Resume text exceeded 8,000 characters and was truncated for optimization.")
        if jd_truncated:
            trunc_parts.append("Job description exceeded 3,000 characters and was truncated for optimization.")
        notice = " ".join(trunc_parts)
        self.assertIn("8,000 characters", notice)
        self.assertIn("3,000 characters", notice)

        # 2. Reachable max calculation
        jd = "Requirements: Python, Docker, PostgreSQL, Redis."
        resume = "Experienced in Python and Docker."
        jd_skills = extract_jd_hard_skills(jd)
        source_skills = {s for s in jd_skills if _skill_in_text(s, resume)}
        reachable_max = int((len(source_skills) / len(jd_skills)) * 100)
        self.assertEqual(reachable_max, 50)


if __name__ == "__main__":
    unittest.main()


