# ============================================================
# CareerLens - Resume Optimizer (Fixed - No Hallucination)
# File: backend/routers/optimizer.py
# ============================================================

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from middleware.auth import get_authenticated_user
from database import supabase
from services.gemini_service import call_groq, _extract_json
import logging

logger = logging.getLogger("careerlens.optimizer")


def count_kw_coverage(text: str, jd: str) -> int:
    import re
    stopwords = {
        "the", "and", "for", "with", "that", "this", "will", "have",
        "from", "you", "are", "your", "our", "they", "can", "has", "was",
        "were", "been", "their", "into", "about", "which", "when", "who",
        "what", "how", "all", "also", "both", "each", "more", "other",
        "some", "such", "than", "then", "them", "these", "those", "very",
        "shall", "should", "could", "would", "may", "might", "must",
        "have", "had", "its", "his", "her", "their", "our", "we", "is",
        "a", "an", "of", "to", "in", "on", "at", "by", "or", "not", "be"
    }
    words = set(re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#.]*\b', jd.lower()))
    keywords = [w for w in words if len(w) > 3 and w not in stopwords]
    if not keywords:
        return 30
    matches = sum(1 for k in keywords if k in text.lower())
    return min(int((matches / len(keywords)) * 100), 99)


router = APIRouter()


class OptimizeRequest(BaseModel):
    resume_text: str
    job_description: str
    job_title: Optional[str] = ""


@router.post("/")
async def optimize_resume(body: OptimizeRequest, user=Depends(get_authenticated_user)):
    if not body.resume_text.strip() or not body.job_description.strip():
        raise HTTPException(status_code=400, detail="Resume and job description required.")

    system = (
        "You are an elite ATS optimization specialist and resume writer. "
        "Your ONLY job is to maximize keyword density and ATS score. "
        "You inject EVERY technical keyword from the job description "
        "into the resume. You rewrite EVERY bullet point to include "
        "job keywords plus quantified metrics. You respond ONLY in "
        "valid JSON with no markdown, no code fences, no extra text."
    )

    user_msg = (
        # ── EXISTING CONTENT: Keep everything below unchanged ─────
        "You are an elite technical resume writer. Your output must be "
        "specific, credible, ATS-optimized, and indistinguishable from "
        "a real engineer's resume. Generic or AI-sounding content is a "
        "failure. Every word must sound like a real engineer wrote it.\n\n"
        
        f"TARGET JOB TITLE: {body.job_title or 'Software Developer'}\n\n"
        f"JOB DESCRIPTION:\n{body.job_description[:2500]}\n\n"
        f"ORIGINAL RESUME:\n{body.resume_text[:3000]}\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 0 — PRESERVE REALITY (NON-NEGOTIABLE)\n"
        "════════════════════════════════════════════════════════\n"
        "- Never invent job titles, companies, or degrees not in original\n"
        "- Never add experience at companies not mentioned\n"
        "- Only enhance what exists — never fabricate what doesn't\n"
        "- If original has 2 experience entries → output has exactly 2\n"
        "- If original has 3 project entries → output has exactly 3\n"
        "- Do NOT merge, split, or reorder existing entries\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 1 — REALISM OVER IMPRESSIVENESS\n"
        "════════════════════════════════════════════════════════\n"
        "- Never fabricate unrealistic achievements\n"
        "- Never claim revenue or business impact unless explicitly\n"
        "  stated in the original resume\n"
        "- Never exceed realistic scale for experience level:\n"
        "    Fresher/student : 100 – 5K users max\n"
        "    1–2 years exp   : 1K – 50K users max\n"
        "    3+ years exp    : larger numbers acceptable\n"
        "- Never claim >60% improvement metrics for freshers\n"
        "- If no metric exists → use system/output metrics:\n"
        "    'processing 10K records per batch'\n"
        "    'reducing query time from 800ms to 200ms'\n"
        "    'achieving 89% accuracy on validation set'\n"
        "- Conservative + specific > impressive + vague\n"
        "- If resume lacks sufficient data to produce quality output:\n"
        "  set insufficient_data: true and return minimal safe output\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 2 — SUMMARY (STRICT)\n"
        "════════════════════════════════════════════════════════\n"
        "- EXACTLY 3 sentences, no more, no less\n"
        "- Sentence 1: [Job Title] with [experience level] in\n"
        "              [2 specific technical domains from JD]\n"
        "- Sentence 2: Skilled in [3 exact JD technologies] with\n"
        "              focus on [specific outcome from JD]\n"
        "- Sentence 3: Delivered [specific system] handling\n"
        "              [realistic scale metric] with measurable result\n"
        "- NEVER include email, phone, location, city, country\n"
        "- NEVER use: passionate, motivated, hardworking, dynamic,\n"
        "             enthusiastic, detail-oriented, self-starter\n"
        "- NEVER start with 'I' or 'My'\n"
        "- NEVER repeat the job title anywhere else in the resume\n"
        "  body — experience entries must show their own specific\n"
        "  position title, not the global target job title\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 3 — SKILLS (GROUPED BY DOMAIN)\n"
        "════════════════════════════════════════════════════════\n"
        "Return optimized_skills as a grouped object ONLY.\n"
        "Choose the correct group set based on candidate domain:\n\n"
        "ML / Data Science roles:\n"
        "  { Languages, ML & Data, Tools & Platforms, Concepts }\n\n"
        "Web Development roles:\n"
        "  { Languages, Frameworks, Databases, DevOps }\n\n"
        "Data Engineering roles:\n"
        "  { Languages, Data Tools, Cloud & Platforms, Concepts }\n\n"
        "Backend / Systems roles:\n"
        "  { Languages, Frameworks, Databases, Tools & DevOps }\n\n"
        "Rules for all groups:\n"
        "- Maximum 6 items per group\n"
        "- No duplicates across groups\n"
        "- Most JD-relevant items listed first within each group\n"
        "- Never mix group name sets across a single response\n"
        "- Pick one domain set and apply it consistently\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 4 — BULLETS (STRICT STRUCTURE)\n"
        "════════════════════════════════════════════════════════\n"
        "Each bullet MUST follow this exact formula:\n"
        "[Power Verb] + [Specific Technology] + "
        "[System Behavior] + [**Metric**]\n\n"
        "Hard constraints:\n"
        "- Maximum 25 words per bullet\n"
        "- All bullets in past tense\n"
        "- No vague phrases: 'scalable', 'robust', 'efficient',\n"
        "  'various', 'multiple', 'several', 'significant'\n"
        "- No filler words\n"
        "- No same keyword repeated more than twice across\n"
        "  the entire resume\n\n"
        "GOOD examples:\n"
        "'Engineered Java-based Hospital Management System using\n"
        " JDBC and MySQL, reducing query latency by **30%** for\n"
        " **500+ daily users**'\n"
        "'Built React dashboard with JWT authentication, serving\n"
        " **1K+ monthly users** with **<2s** average load time'\n"
        "'Trained XGBoost classifier on **50K samples**, improving\n"
        " accuracy from **71%** to **89%** on validation set'\n\n"
        "BAD examples — NEVER generate these:\n"
        "'Engineered a scalable system' ← vague, no specifics\n"
        "'Achieved 95% accuracy' ← no context, sounds fabricated\n"
        "'Increased business revenue by 20%' ← unverifiable,\n"
        " destroys recruiter trust instantly\n"
        "'Worked on backend development' ← banned verb, no detail\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 5 — BANNED VERBS (ABSOLUTE)\n"
        "════════════════════════════════════════════════════════\n"
        "NEVER use:\n"
        "worked, helped, assisted, involved, responsible,\n"
        "participated, supported, contributed, handled\n\n"
        "Exception: 'Managed' is allowed ONLY when referring\n"
        "to people or teams. Never use for tasks or systems.\n\n"
        "USE THESE INSTEAD — each verb used MAX ONCE per resume:\n"
        "Engineered, Architected, Built, Developed, Designed,\n"
        "Implemented, Deployed, Optimized, Automated, Integrated,\n"
        "Migrated, Launched, Streamlined, Trained, Evaluated,\n"
        "Constructed, Delivered, Established, Reduced, Accelerated,\n"
        "Spearheaded, Orchestrated, Reconstructed, Configured\n\n"
        "ANTI-REPETITION RULE:\n"
        "Never open two bullets with the same verb anywhere\n"
        "in the entire resume. Every bullet must start with\n"
        "a different verb. Scan all bullets before finalizing.\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 6 — JD EXACT PHRASE MATCHING\n"
        "════════════════════════════════════════════════════════\n"
        "- Copy technical terms VERBATIM from JD — ATS matches\n"
        "  exact strings, not paraphrases\n"
        "- 'microservices architecture' → use those exact words\n"
        "- 'CI/CD pipelines' → use those exact words\n"
        "- 'cross-functional teams' → use those exact words\n"
        "- Never substitute a synonym for a technical term\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 7 — NEW BULLETS FOR JD GAPS\n"
        "════════════════════════════════════════════════════════\n"
        "- Identify 2–4 JD requirements absent from original\n"
        "- Write bullets plausible for this candidate's background\n"
        "- Do NOT introduce technologies from a different domain\n"
        "- Fewer believable bullets > more fabricated ones\n"
        "- If fewer than 2 genuine gaps exist, write fewer bullets\n"
        "- Each new bullet must cite which JD phrase it covers\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 8 — METRIC FORMATTING\n"
        "════════════════════════════════════════════════════════\n"
        "Wrap ALL numbers and metrics in **double asterisks**:\n"
        "  'reducing latency by **30%** for **500+ users**'\n"
        "  'processing **10K+ records** per batch'\n"
        "  'achieving **89%** accuracy on **50K** test samples'\n"
        "Apply to: improved_bullets, new_bullets, summary\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 9 — ANTI-HALLUCINATION FILTER\n"
        "════════════════════════════════════════════════════════\n"
        "Before finalizing each bullet, ask internally:\n"
        "  1. Is this metric realistic for this experience level?\n"
        "  2. Is this technology actually in the original resume\n"
        "     or explicitly in the JD?\n"
        "  3. Would a real recruiter believe this?\n"
        "If any answer is NO → rewrite or lower the claim\n"
        "Never guess company-scale business impact\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "RULE 10 — MATCH SCORE (HONEST FORMULA)\n"
        "════════════════════════════════════════════════════════\n"
        "score =\n"
        "  (JD keywords in output / total JD keywords) * 40\n"
        "  + (JD skills covered / total JD skills) * 30\n"
        "  + (experience alignment score 0-20)\n"
        "  + (bullet quality score 0-10)\n"
        "  - (5 points per critical missing keyword)\n"
        "Confidence level rules:\n"
        "  score >= 75 → High\n"
        "  score 50-74 → Medium\n"
        "  score < 50  → Low\n"
        "Do NOT inflate — an honest 65 is better than a fake 90\n\n"
        
        "════════════════════════════════════════════════════════\n"
        "OUTPUT FORMAT — STRICT JSON ONLY\n"
        "No markdown, no backticks, no explanation outside JSON\n"
        "════════════════════════════════════════════════════════\n"
        
        "{\n"
        '  "insufficient_data": false,\n'
        
        '  "optimized_summary": "exactly 3 sentences, no contact info",\n'
        
        '  "optimized_skills": {\n'
        '    "Languages": ["Python", "Java"],\n'
        '    "ML & Data": ["Machine Learning", "Feature Engineering"],\n'
        '    "Tools & Platforms": ["Docker", "Kubernetes"],\n'
        '    "Concepts": ["Data Pipelines", "Model Training"]\n'
        '  },\n'
        
        '  "improved_bullets": [\n'
        '    {\n'
        '      "original": "exact original bullet text",\n'
        '      "improved": "verb + technology + behavior + **metric**",\n'
        '      "keywords_added": ["kw1", "kw2"],\n'
        '      "verb_upgrade": {"from": "worked", "to": "Engineered"},\n'
        '      "metric_added": "**30%** reduction for **500+** users",\n'
        '      "improvement_reason": "plain English one sentence"\n'
        '    }\n'
        '  ],\n'
        
        '  "new_bullets": [\n'
        '    {\n'
        '      "text": "verb + technology + **metric**",\n'
        '      "reason": "JD requires X, missing from original",\n'
        '      "jd_requirement": "exact JD phrase this addresses"\n'
        '    }\n'
        '  ],\n'
        
        '  "added_keywords": ["every JD keyword present in output"],\n'
        '  "missing_keywords": ["JD keywords still not coverable"],\n'
        
        '  "improvement_explanation": {\n'
        '    "keywords_added": ["REST API", "Docker", "Microservices"],\n'
        '    "verbs_upgraded": [\n'
        '      {"from": "worked", "to": "Engineered"},\n'
        '      {"from": "helped", "to": "Implemented"}\n'
        '    ],\n'
        '    "metrics_added": [\n'
        '      "**30%** latency reduction added to bullet 1",\n'
        '      "**500+ users** scale added to bullet 2"\n'
        '    ],\n'
        '    "sections_improved": [\n'
        '      "Summary rewritten with JD-specific technologies",\n'
        '      "Skills grouped by domain category",\n'
        '      "All bullets rewritten with power verbs and metrics"\n'
        '    ]\n'
        '  },\n'
        
        '  "ats_tips": [\n'
        '    "Add microservices to summary sentence 2",\n'
        '    "Mention CI/CD in experience bullet 3"\n'
        '  ],\n'
        
        '  "match_score_estimate": 72,\n'
        '  "confidence_level": "Medium",\n'
        '  "overall_improvement": "one specific sentence not generic"\n'
        "}"
    )

    try:
        text = await call_groq([
            {"role": "system", "content": system},
            {"role": "user",   "content": user_msg}
        ])
        result = _extract_json(text)

        # Compute real keyword-based ATS scores
        ats_before = count_kw_coverage(body.resume_text, body.job_description)

        optimized_text = " ".join([
            result.get("optimized_summary", ""),
            " ".join(b.get("improved", "") for b in result.get("improved_bullets", [])),
            " ".join(b.get("text", "") for b in result.get("new_bullets", [])),
            " ".join(result.get("optimized_skills", [])),
            " ".join(result.get("added_keywords", [])),
        ])
        ats_after = count_kw_coverage(optimized_text, body.job_description)
        result["ats_before"] = ats_before
        result["ats_after"] = ats_after

        try:
            supabase.table("resume_optimizations").insert({
                "user_id":         user["user_id"],
                "job_title":       body.job_title or "",
                "job_description": body.job_description[:500],
                "result_json":     result,
            }).execute()
        except Exception as e:
            logger.warning(f"DB save failed: {e}")

        return {
            "success": True,
            "optimization": result,
            "ats_before": ats_before,
            "ats_after": ats_after,
        }

    except Exception as e:
        logger.error(f"Optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_optimization_history(user=Depends(get_authenticated_user)):
    result = supabase.table("resume_optimizations") \
        .select("id,job_title,job_description,created_at") \
        .eq("user_id", user["user_id"]) \
        .order("created_at", desc=True) \
        .limit(10) \
        .execute()
    return {"success": True, "history": result.data}
