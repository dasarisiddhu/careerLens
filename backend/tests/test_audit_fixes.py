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


if __name__ == "__main__":
    unittest.main()

