# ============================================================
# CareerLens – Job Match Engine
# File: backend/routers/job_match.py
# ============================================================

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from middleware.auth import get_authenticated_user
from services.gemini_service import call_groq, _extract_json
import logging

logger = logging.getLogger("careerlens.job_match")
router = APIRouter()

# Realistic job roles dataset with typical required skills
JOB_ROLES = [
    {"title": "Python Developer Intern",     "skills": ["python","django","flask","sql","git"],                              "apply_link": "https://internshala.com/internships/python-internship"},
    {"title": "Frontend Developer Intern",   "skills": ["react","javascript","html","css","tailwind","git"],                 "apply_link": "https://internshala.com/internships/web-development-internship"},
    {"title": "Data Analyst Intern",         "skills": ["python","sql","pandas","excel","data analysis"],                    "apply_link": "https://internshala.com/internships/data-science-internship"},
    {"title": "ML Engineer Intern",          "skills": ["python","machine learning","tensorflow","scikit-learn","pandas"],   "apply_link": "https://internshala.com/internships/machine-learning-internship"},
    {"title": "Full Stack Developer Intern", "skills": ["react","node.js","mongodb","sql","javascript","git"],               "apply_link": "https://internshala.com/internships/full-stack-development-internship"},
    {"title": "DevOps Intern",               "skills": ["linux","docker","aws","git","ci/cd"],                               "apply_link": "https://www.naukri.com/devops-internship-jobs"},
    {"title": "Junior Backend Developer",    "skills": ["python","fastapi","postgresql","docker","git","rest api"],          "apply_link": "https://www.naukri.com/junior-backend-developer-jobs"},
    {"title": "Junior Data Scientist",       "skills": ["python","machine learning","pandas","sql","data analysis"],         "apply_link": "https://www.naukri.com/junior-data-scientist-jobs"},
    {"title": "React Developer",             "skills": ["react","javascript","typescript","html","css","git"],               "apply_link": "https://www.naukri.com/react-developer-jobs"},
    {"title": "Cloud Engineer",              "skills": ["aws","azure","docker","kubernetes","linux","terraform"],             "apply_link": "https://www.naukri.com/cloud-engineer-jobs"},
    {"title": "AI/ML Engineer",              "skills": ["python","deep learning","tensorflow","pytorch","nlp","pandas"],     "apply_link": "https://www.naukri.com/machine-learning-jobs"},
    {"title": "Android Developer Intern",    "skills": ["kotlin","android","java","git","rest api"],                        "apply_link": "https://internshala.com/internships/android-app-development-internship"},
    {"title": "UI/UX Design Intern",         "skills": ["figma","ui/ux","prototyping","html","css"],                        "apply_link": "https://internshala.com/internships/ui-ux-internship"},
    {"title": "Cybersecurity Intern",        "skills": ["linux","python","networking","git"],                               "apply_link": "https://internshala.com/internships/cybersecurity-internship"},
    {"title": "Software Engineer",           "skills": ["python","java","data structures","algorithms","system design","git"], "apply_link": "https://www.naukri.com/software-engineer-jobs"},
]

KNOWN_SKILLS = [
    "python","javascript","typescript","java","c++","c#","go","rust","php","swift","kotlin",
    "react","vue","angular","next.js","node.js","express","django","fastapi","flask","spring",
    "sql","postgresql","mysql","mongodb","redis","firebase","supabase","elasticsearch",
    "aws","gcp","azure","docker","kubernetes","terraform","ci/cd","github actions","linux","git",
    "machine learning","deep learning","tensorflow","pytorch","pandas","numpy","scikit-learn","nlp",
    "rest api","graphql","microservices","system design","html","css","tailwind","figma",
    "agile","scrum","devops","data analysis","excel","android","ios","ui/ux","prototyping",
    "data structures","algorithms","networking","opencv","langchain"
]


class JobMatchRequest(BaseModel):
    resume_text: str
    github_skills: Optional[List[str]] = []


def extract_skills(text: str) -> List[str]:
    tl = text.lower()
    return list(set(s for s in KNOWN_SKILLS if s in tl))


def score_match(user_skills: List[str], role_skills: List[str]) -> dict:
    user_set = set(user_skills)
    role_set = set(role_skills)
    overlap  = user_set & role_set
    missing  = role_set - user_set
    if not role_set:
        return {"score": 0, "missing": [], "assessment": "0% match - there are no usable role requirements to compare."}
    score = int((len(overlap) / len(role_set)) * 100)
    if score >= 85:
        assessment = f"{score}% match - this role is realistic for you right now."
    elif score >= 70:
        assessment = f"{score}% match - you are close, but still missing requirements that recruiters will notice."
    elif score >= 50:
        assessment = f"{score}% match - you are not competitive for this role yet because too many core requirements are still missing."
    else:
        assessment = f"{score}% match - you are underqualified for this role currently."
    return {"score": score, "missing": sorted(missing), "assessment": assessment}


@router.post("/")
async def match_jobs(body: JobMatchRequest, user=Depends(get_authenticated_user)):
    if not body.resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text required.")

    all_skills = extract_skills(body.resume_text)
    if body.github_skills:
        all_skills = list(set(all_skills + body.github_skills))

    matches = []
    for role in JOB_ROLES:
        m = score_match(all_skills, role["skills"])
        matches.append({
            "job_title":      role["title"],
            "match_score":    m["score"],
            "missing_skills": m["missing"][:4],
            "assessment":     m["assessment"],
            "apply_link":     role["apply_link"],
            "realistic":      m["score"] >= 70,
        })

    # Sort by score descending, take top 8
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    top = matches[:8]

    return {
        "success":       True,
        "user_skills":   all_skills,
        "job_matches":   top,
        "best_fit":      top[0] if top else None,
    }
