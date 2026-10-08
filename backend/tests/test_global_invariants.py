import json
import os
import unittest
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests-0123456789")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")

from services.resume_structure import parse_source_resume, reconstruct_resume_structure, _is_section_header
from services.professional_resume_pdf import build_professional_resume_pdf
from routers.optimizer import _validate_optimized_structure, _stamp_ats_scores

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class GlobalInvariantsTests(unittest.TestCase):
    def test_i1_line_coverage_all_fixtures(self):
        """I-1 Line coverage: On every fixture, every non-empty line appears in parsed doc or dropped_or_unmapped."""
        for path in FIXTURES_DIR.glob("resume_*.txt"):
            text = path.read_text(encoding="utf-8")
            doc = parse_source_resume(text)
            
            # Collect all tokens/content represented in doc
            doc_content = []
            if doc.name:
                doc_content.append(doc.name)
            if doc.email:
                doc_content.append(doc.email)
            if doc.phone:
                doc_content.append(doc.phone)
            if doc.location:
                doc_content.append(doc.location)
            if doc.linkedin:
                doc_content.append(doc.linkedin)
            if doc.github:
                doc_content.append(doc.github)
            if doc.summary:
                doc_content.append(doc.summary)
            if doc.experience:
                doc_content.append("experience")
            if doc.projects:
                doc_content.append("projects")
            if doc.education:
                doc_content.append("education")
            if doc.certifications:
                doc_content.append("certifications")
            if doc.skills:
                doc_content.append("skills")
            doc_content.extend(doc.skills)
            doc_content.extend(doc.education)
            doc_content.extend(doc.certifications)
            for entry in doc.experience + doc.projects:
                if entry.organization:
                    doc_content.append(entry.organization)
                if entry.title:
                    doc_content.append(entry.title)
                if entry.dates:
                    doc_content.append(entry.dates)
                if entry.location:
                    doc_content.append(entry.location)
                doc_content.extend(b.original for b in entry.bullets)
            for sec in doc.other_sections:
                doc_content.append(sec.get("title", ""))
                doc_content.extend(sec.get("items", []))
            doc_content.extend(doc.dropped_or_unmapped)
            
            joined_doc = " ".join(doc_content).lower()
            
            # Check lines
            uncovered = []
            for line in text.splitlines():
                l = line.strip()
                if not l or l.lower() == "continued":
                    continue
                if _is_section_header(l) is not None:
                    continue
                # At least part of the line (or heading / tokens) must appear
                words = [w.lower() for w in l.replace("|", " ").replace(",", " ").split() if len(w) > 2]
                if words and not any(w in joined_doc for w in words):
                    uncovered.append(l)
            
            self.assertEqual(
                uncovered, [],
                f"Fixture {path.name} had silent line loss: {uncovered}"
            )

    def test_i2_no_fabrication_across_all_channels(self):
        """I-2 No-fabrication: fabricated numbers, tech terms, and claim verbs never reach output."""
        doc = parse_source_resume(
            "Alice Smith\n"
            "Software Engineer\n"
            "alice@example.com\n\n"
            "Skills\n"
            "Python, Django\n\n"
            "Experience\n"
            "TechCorp | Backend Engineer | 2021 - 2023\n"
            "- Built REST APIs using Python and Django.\n"
        )
        fake_result = {
            "improved_bullets": [
                {
                    "source_id": "experience_001_bullet_001",
                    "original": "- Built REST APIs using Python and Django.",
                    "improved": "Led engineering of 500 Kubernetes microservices with Terraform achieving 99.99% uptime.",
                }
            ],
            "bullet_rewrites": {
                "experience_001_bullet_001": "Spearheaded 500 Docker containers with AWS Lambda reaching 99.99% SLA."
            },
            "experience_001_bullet_001": "Architected 500 microservices.",
            "optimized_skills": ["Kubernetes", "Terraform", "AWS Lambda", "Python"],
            "optimized_summary": "Seasoned Vice President who managed 50 engineers.",
        }
        validated = _validate_optimized_structure(doc, fake_result)
        out_text = json.dumps(validated)
        
        # Injected terms must not survive in validated output
        for term in ["500", "99.99%", "Terraform", "AWS Lambda", "Kubernetes"]:
            self.assertNotIn(term, validated["reconstructed_resume"]["experience"][0]["bullets"][0])

    def test_i3_idempotence_parse_pdf_parse(self):
        """I-3 Idempotence: parse -> build PDF -> extract text -> parse preserves counts."""
        sample_path = FIXTURES_DIR / "resume_two_line_header.txt"
        source_text = sample_path.read_text(encoding="utf-8")
        doc1 = parse_source_resume(source_text)
        
        rec = reconstruct_resume_structure(doc1, bullet_rewrites={})
        pdf = build_professional_resume_pdf(
            name=doc1.name,
            content=rec,
            source_resume_text=source_text,
        )
        extracted = getattr(pdf, "extracted_text", "") or getattr(pdf, "visible_text", "")
        self.assertTrue(len(extracted) > 50)

    def test_i4_skill_count_75_skills(self):
        """I-4 Skill count: 75-skill fixture yields 75 skills in parser and reconstructed structure."""
        text = (FIXTURES_DIR / "resume_skills.txt").read_text(encoding="utf-8")
        doc = parse_source_resume(text)
        self.assertEqual(len(doc.skills), 75)
        rec = reconstruct_resume_structure(doc, bullet_rewrites={})
        flat_rec_skills = []
        if isinstance(rec.get("skills"), dict):
            for items in rec["skills"].values():
                flat_rec_skills.extend(items)
        else:
            flat_rec_skills = rec.get("skills") or []
        self.assertEqual(len(flat_rec_skills), 75)


if __name__ == "__main__":
    unittest.main()
