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


if __name__ == "__main__":
    unittest.main()
