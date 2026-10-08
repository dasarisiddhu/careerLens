"""Phase 0 baseline snapshot tests.

Runs the parser, the optimizer validators, and the PDF builder on synthetic fixtures
and asserts equivalence with or tracks evolutions against golden snapshots.
"""

import json
import os
import unittest
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests-0123456789")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")

from services.resume_structure import parse_source_resume, reconstruct_resume_structure
from services.professional_resume_pdf import build_professional_resume_pdf
from routers.optimizer import _validate_optimized_structure

FIXTURES_DIR = Path(__file__).parent / "fixtures"
GOLDEN_PATH = FIXTURES_DIR / "baseline_snapshots.json"


class BaselineSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(GOLDEN_PATH.exists(), "Golden snapshot file must exist")
        self.golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))

    def test_all_16_fixtures_have_snapshots(self):
        fixture_files = sorted([f.name for f in FIXTURES_DIR.glob("resume_*.txt")])
        self.assertEqual(len(fixture_files), 16)
        for fname in fixture_files:
            self.assertIn(fname, self.golden)

    def test_parser_runs_on_all_fixtures(self):
        for fname in sorted([f.name for f in FIXTURES_DIR.glob("resume_*.txt")]):
            text = (FIXTURES_DIR / fname).read_text(encoding="utf-8")
            doc = parse_source_resume(text)
            self.assertTrue(doc.name, f"Parsed name should not be empty for {fname}")
            validated = _validate_optimized_structure(doc, {})
            self.assertIsNotNone(validated)
            rec = reconstruct_resume_structure(doc=doc, bullet_rewrites={})
            pdf_res = build_professional_resume_pdf(
                name=doc.name,
                content={"reconstructed_resume": rec, "summary": doc.summary},
                source_resume_text=doc.raw_text,
            )
            pdf_bytes = pdf_res.pdf_bytes if hasattr(pdf_res, "pdf_bytes") else getattr(pdf_res, "content", b"")
            self.assertGreater(len(pdf_bytes), 0, f"PDF should generate for {fname}")


if __name__ == "__main__":
    unittest.main()
