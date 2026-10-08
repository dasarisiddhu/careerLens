import unittest
from services.resume_structure import (
    ResumeDocument,
    parse_source_resume,
    reconstruct_resume_structure,
)
from routers.optimizer import (
    _validate_optimized_structure,
    _verify_optimizer_summary,
    _stamp_ats_scores,
    extract_jd_hard_skills,
    _all_source_metrics_present,
    _find_ungrounded_tech_terms,
)

class DefectFixesGroup4Tests(unittest.TestCase):

    def test_c1_target_title_identity_guard_fires(self):
        """C1: target-title-as-identity guard fires when job_title passed."""
        resume = "EXPERIENCE\nSoftware Engineer with 2 years of experience in Python.\n"
        doc = parse_source_resume(resume)
        result = {
            "optimized_summary": "Senior Principal Cloud Architect with extensive Python expertise.",
            "original_summary": "Software Engineer with 2 years of experience in Python.",
            "improved_bullets": [],
        }
        validated = _validate_optimized_structure(
            doc,
            result,
            job_title="Senior Principal Cloud Architect",
            user_id="user_c1",
        )
        self.assertNotIn("Senior Principal Cloud Architect", validated.get("optimized_summary", ""))

    def test_c2_unchanged_original_summary_passes_verification(self):
        """C2: An unchanged original summary passes with no retry and no failure note."""
        resume = "Header line\n" * 50 + "SUMMARY\nExperienced developer who builds robust web apps.\nEXPERIENCE\n"
        orig_summary = "Experienced developer who builds robust web apps."
        verified, reason = _verify_optimizer_summary(
            summary=orig_summary,
            source_text=resume,
        )
        self.assertTrue(verified)
        self.assertEqual(reason, "valid")

    def test_c3_step3_preserves_explanations_and_adds_status(self):
        """C3: Preserves keywords_added, metric_added, improvement_reason, adds status and counts."""
        resume = (
            "EXPERIENCE\n"
            "Acme Corp\n"
            "Software Engineer  Jan 2023 - Present\n"
            "- Built REST APIs with Python.\n"
        )
        doc = parse_source_resume(resume)
        self.assertTrue(len(doc.all_bullets) > 0)
        bid = doc.all_bullets[0].source_id
        result = {
            "improved_bullets": [
                {
                    "source_id": bid,
                    "original": "Built REST APIs with Python.",
                    "improved": "Developed scalable REST APIs with Python.",
                    "keywords_added": ["scalable"],
                    "metric_added": "",
                    "improvement_reason": "Upgraded action verb and highlighted scale.",
                }
            ],
            "optimized_skills": ["Python"],
        }
        validated = _validate_optimized_structure(doc, result, user_id="user_c3")
        rewrites = validated.get("improved_bullets", [])
        self.assertEqual(len(rewrites), 1)
        r = rewrites[0]
        self.assertEqual(r.get("keywords_added"), ["scalable"])
        self.assertEqual(r.get("improvement_reason"), "Upgraded action verb and highlighted scale.")
        self.assertEqual(r.get("status"), "rewritten")
        counts = validated.get("rewrite_status_counts", {})
        self.assertEqual(counts.get("rewritten"), 1)

    def test_c4_bad_or_missing_source_id_matches_by_original(self):
        """C4: Bad/missing source_id falls back to original text match and reports metadata."""
        resume = (
            "EXPERIENCE\n"
            "Acme Corp\n"
            "Software Engineer  Jan 2023 - Present\n"
            "- Built REST APIs with Python.\n"
        )
        doc = parse_source_resume(resume)
        self.assertTrue(len(doc.all_bullets) > 0)
        result = {
            "improved_bullets": [
                {
                    "source_id": "invalid_or_missing_id",
                    "original": "Built REST APIs with Python.",
                    "improved": "Developed REST APIs with Python.",
                }
            ],
            "optimized_skills": ["Python"],
        }
        validated = _validate_optimized_structure(doc, result, user_id="user_c4")
        rewrites = validated.get("improved_bullets", [])
        self.assertEqual(len(rewrites), 1)
        self.assertEqual(rewrites[0]["improved"], "Developed REST APIs with Python.")
        meta = validated.get("rewrite_matching_metadata", {})
        self.assertEqual(meta.get("matched_by_original"), 1)

    def test_c5_ats_before_after_identical_on_no_optimization(self):
        """C5: ATS before/after uses same function and scope; identical on no optimization."""
        text = "Experienced Python developer with Docker and FastAPI skills."
        jd = "Looking for Python, Docker, FastAPI developer."
        doc = parse_source_resume(text)
        rec = reconstruct_resume_structure(doc, bullet_rewrites={})
        result = {"reconstructed_resume": rec}
        before, after = _stamp_ats_scores(result, text, jd)
        self.assertIsNotNone(before)
        self.assertEqual(before, after)

    def test_c7_extract_jd_hard_skills_context_rules(self):
        """C7: Exclude non-skill uses of excel, rest, agile, lambda, shell, and standalone C."""
        # Negative contexts:
        neg_jd = (
            "Candidate must excel in team communication and rest assured during on-call. "
            "Need an agile mindset and familiarity with lambda variant and egg shell colors."
        )
        neg_skills = extract_jd_hard_skills(neg_jd)
        self.assertNotIn("excel", [s.lower() for s in neg_skills])
        self.assertNotIn("rest", [s.lower() for s in neg_skills])
        self.assertNotIn("agile", [s.lower() for s in neg_skills])
        self.assertNotIn("lambda", [s.lower() for s in neg_skills])
        self.assertNotIn("shell", [s.lower() for s in neg_skills])

        # Positive contexts:
        pos_jd = (
            "Requires Microsoft Excel reporting, REST API integration, Agile/Scrum development, "
            "AWS Lambda serverless functions, Shell scripting in Bash, and C/C++ programming."
        )
        pos_skills = [s.lower() for s in extract_jd_hard_skills(pos_jd)]
        self.assertIn("excel", pos_skills)
        self.assertIn("rest", pos_skills)
        self.assertIn("agile", pos_skills)
        self.assertIn("lambda", pos_skills)
        self.assertIn("shell", pos_skills)
        self.assertTrue("c" in pos_skills or "c/c++" in pos_skills)

    def test_c9_metric_matching_numeric_tokens_not_substrings(self):
        """C9: Numbers match as whole numeric tokens; '5' must not match '2025' or '500'."""
        source = "Managed 500 servers."
        # A rewrite that only has '5' must NOT satisfy source metric '500'
        rewrite_with_five = "Managed 5 servers."
        self.assertFalse(_all_source_metrics_present(rewrite_with_five, source))

        # A rewrite with genuine 500 should match
        rewrite_with_500 = "Managed 500 servers."
        self.assertTrue(_all_source_metrics_present(rewrite_with_500, source))

    def test_c10_sentence_final_period_not_tech_term(self):
        """C10: Sentence-final 'Workflow.' must not trigger revert; Node.js is still tech."""
        source = "Built an automated internal data workflow."
        rewrite = "Automated data workflow."
        # Should not flag 'Workflow.' as ungrounded tech term
        ungrounded = _find_ungrounded_tech_terms(rewrite, source)
        self.assertEqual(ungrounded, [])

        # But genuinely ungrounded tech term like Node.js must be caught
        rewrite_nodejs = "Automated data workflow using Node.js."
        ungrounded_node = _find_ungrounded_tech_terms(rewrite_nodejs, source)
        self.assertIn("Node.js", ungrounded_node)


if __name__ == "__main__":
    unittest.main()
