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
import re

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


SUMMARY_FALLBACK_ROLE = "Software Engineer"
SUMMARY_FALLBACK_SUMMARY = (
    "Machine Learning Engineer specializing in scalable AI systems and data pipelines. "
    "Focused on building efficient backend solutions."
)
SUMMARY_NO_METRIC_SENTENCE = (
    "Focused on building efficient backend solutions."
)
SUMMARY_BUZZWORD_RE = re.compile(
    r"\b(production-grade|applied engineering work|reliable deployment practices|"
    r"practical, measurable|maintainable solutions|delivery quality|"
    r"scalable infrastructure practices|workflow automation|user-centered product delivery|"
    r"significantly improved|greatly enhanced|various improvements|multiple systems|"
    r"improved system efficiency|improved throughput|enhanced performance|"
    r"scaled systems|optimized workflows)\b",
    re.IGNORECASE,
)
SUMMARY_BANNED_OPENER_RE = re.compile(
    r"^(uses|has knowledge of|has experience in|is skilled in|worked on|i|my)\b",
    re.IGNORECASE,
)
SUMMARY_WEAK_PHRASES_RE = re.compile(
    r"\b(with experience in|has experience in|has knowledge of|is skilled in|worked on|proficient in|knowledge of)\b",
    re.IGNORECASE,
)
SUMMARY_EMAIL_RE = re.compile(r"[\w.-]+@[\w.-]+\.\w+")
SUMMARY_PHONE_RE = re.compile(r"(?:\+?\d[\d\s\-()]{8,}\d)")
SUMMARY_PERCENT_RE = re.compile(r"\b\d+(?:\.\d+)?%")
SUMMARY_COUNT_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:k|m|b)?\+?\s*(?:daily\s+|monthly\s+)?(?:users|requests|data points|transactions|patients|entries|patient records|records|samples?)\b",
    re.IGNORECASE,
)
SUMMARY_DURATION_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:ms|milliseconds?|s|sec|secs|seconds?)\b",
    re.IGNORECASE,
)
SUMMARY_TOOL_NAMES = [
    "Apache Spark", "Kubernetes", "TensorFlow", "Scikit-learn", "PostgreSQL",
    "JavaScript", "TypeScript", "FastAPI", "PyTorch", "Docker", "Python",
    "Pandas", "NumPy", "Airflow", "Kafka", "MLflow", "React", "Node.js",
    "AWS", "Azure", "GCP", "SQL", "Java", "Git",
]
SUMMARY_DOMAIN_PATTERNS = [
    (r"\b(data pipelines?|etl|data processing)\b", "data pipelines"),
    (r"\b(model deployment|model serving|inference|mlops)\b", "model deployment"),
    (r"\b(computer vision|image processing|opencv)\b", "computer vision"),
    (r"\b(nlp|natural language|text classification|language model)\b", "NLP"),
    (r"\b(predictive modeling|forecasting|classification|regression)\b", "predictive modeling"),
    (r"\b(backend|api|microservices?|fastapi|node\.?js)\b", "backend systems"),
    (r"\b(cloud|aws|azure|gcp|deployment)\b", "cloud deployment"),
    (r"\b(sql|database|postgresql|mysql|mongodb)\b", "database systems"),
]


def _summary_clean_text(value: str) -> str:
    text = str(value or "")
    text = SUMMARY_EMAIL_RE.sub("", text)
    text = SUMMARY_PHONE_RE.sub("", text)
    text = re.sub(r"[\u2026]|\.{2,}", ".", text)
    text = re.sub(r"\*\*", "", text)
    text = SUMMARY_WEAK_PHRASES_RE.sub("focused on", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _summary_word_count(value: str) -> int:
    return len(re.findall(r"\b[\w+#.%-]+\b", value or ""))


def _summary_role(raw_role: str = "") -> str:
    cleaned = _summary_clean_text(raw_role)
    cleaned = re.sub(r"^(target role|role|job title)\s*[:|-]\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[.]+$", "", cleaned).strip()
    lowered = cleaned.lower()
    if re.search(r"machine learning|(^|\s)ml(\s|$)|artificial intelligence|\bai\b", lowered):
        return "Machine Learning Engineer"
    if "data scientist" in lowered:
        return "Data Scientist"
    if re.search(r"data analyst|analytics", lowered):
        return "Data Analyst"
    if re.search(r"frontend|front-end|react", lowered):
        return "Frontend Engineer"
    if re.search(r"backend|back-end|api", lowered):
        return "Backend Engineer"
    if re.search(r"full stack|full-stack", lowered):
        return "Full Stack Engineer"
    if re.search(r"devops|cloud|site reliability|sre", lowered):
        return "Cloud Engineer"
    if "software" in lowered:
        return "Software Engineer"
    return cleaned.title() if cleaned else SUMMARY_FALLBACK_ROLE


def _summary_skill_items(value) -> list[str]:
    items: list[str] = []
    if isinstance(value, dict):
        for group_values in value.values():
            items.extend(_summary_skill_items(group_values))
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            items.extend(_summary_skill_items(item))
    elif value:
        text = _summary_clean_text(str(value))
        for part in re.split(r"[,|;/]", text):
            cleaned = re.sub(r"^[A-Za-z &]+:\s*", "", part.strip())
            if cleaned:
                items.append(cleaned)
    return items


def _summary_top_skills(result: dict, resume_text: str = "") -> list[str]:
    candidates: list[str] = []
    for key in ("optimized_skills", "skills_to_highlight", "added_keywords"):
        candidates.extend(_summary_skill_items(result.get(key)))

    in_skills_section = False
    for raw_line in str(resume_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(r"^(skills|technical skills|core skills|technologies)\b", line, re.IGNORECASE):
            in_skills_section = True
            continue
        if in_skills_section and re.match(
            r"^(experience|work experience|education|projects|certifications|summary|profile|objective)\b",
            line,
            re.IGNORECASE,
        ):
            break
        if in_skills_section:
            candidates.extend(_summary_skill_items(line))

    seen: set[str] = set()
    skills: list[str] = []
    for item in candidates:
        cleaned = re.sub(r"\s+", " ", str(item or "").strip())
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        if SUMMARY_EMAIL_RE.search(cleaned) or SUMMARY_PHONE_RE.search(cleaned):
            continue
        seen.add(key)
        skills.append(cleaned)
        if len(skills) == 5:
            break
    return skills


def _summary_domains(job_description: str = "", result: dict | None = None, role: str = "") -> list[str]:
    result = result or {}
    jd_text = _summary_clean_text(job_description)
    keyword_text = " ".join(_summary_skill_items(result.get("added_keywords")))
    text = f"{jd_text} {keyword_text}".lower()
    domains: list[str] = []

    for pattern, domain in SUMMARY_DOMAIN_PATTERNS:
        if re.search(pattern, text) and domain not in domains:
            domains.append(domain)

    if len(domains) < 2 and re.search(r"\b(machine learning|ml engineer|data scientist)\b", text):
        for fallback_domain in ("predictive modeling", "model deployment"):
            if fallback_domain not in domains:
                domains.append(fallback_domain)

    if len(domains) < 2 and re.search(r"\b(ai|artificial intelligence)\b", text):
        for fallback_domain in ("scalable AI systems", "data pipelines"):
            if fallback_domain not in domains:
                domains.append(fallback_domain)

    if len(domains) < 2 and "machine learning engineer" in role.lower():
        for fallback_domain in ("scalable AI systems", "data pipelines"):
            if fallback_domain not in domains:
                domains.append(fallback_domain)

    return domains[:2]


def _summary_key_tools(
    job_description: str = "",
    resume_text: str = "",
    optimized_skills: list[str] | None = None,
    sentence_text: str = "",
) -> list[str]:
    source = f"{job_description} {resume_text}"
    skill_keys = {re.sub(r"[^a-z0-9+#.]+", " ", skill.lower()).strip() for skill in (optimized_skills or [])}
    sentence_lower = sentence_text.lower()
    tools: list[str] = []
    for tool in SUMMARY_TOOL_NAMES:
        tool_pattern = re.escape(tool).replace(r"\ ", r"\s+")
        if not re.search(rf"\b{tool_pattern}\b", source, re.IGNORECASE):
            continue
        key = re.sub(r"[^a-z0-9+#.]+", " ", tool.lower()).strip()
        if key in skill_keys or tool.lower() in sentence_lower:
            continue
        if key in {"ai", "machine learning"}:
            continue
        tools.append(tool)
        if len(tools) == 3:
            break
    return tools


def _summary_metric_value(metric: str) -> float:
    match = re.search(r"\d+(?:\.\d+)?", metric or "")
    if not match:
        return 0
    value = float(match.group(0))
    lowered = metric.lower()
    if "k" in lowered:
        value *= 1_000
    elif "m" in lowered:
        value *= 1_000_000
    elif "b" in lowered:
        value *= 1_000_000_000
    return value


def _summary_duration_value_ms(metric: str) -> float:
    match = re.search(r"\d+(?:\.\d+)?", metric or "")
    if not match:
        return 0
    value = float(match.group(0))
    lowered = metric.lower()
    if re.search(r"\b(s|sec|secs|second|seconds)\b", lowered):
        value *= 1_000
    return value


def _summary_best_duration_pair(text: str) -> tuple[str, str]:
    metrics = SUMMARY_DURATION_RE.findall(_summary_clean_text(text))
    if len(metrics) < 2:
        return ("", "")
    ordered = sorted(metrics, key=_summary_duration_value_ms, reverse=True)
    start, end = ordered[0], ordered[-1]
    if _summary_duration_value_ms(start) <= _summary_duration_value_ms(end):
        return ("", "")
    return (start, end)


def _summary_best_duration(text: str) -> str:
    metrics = SUMMARY_DURATION_RE.findall(_summary_clean_text(text))
    if not metrics:
        return ""
    return min(metrics, key=_summary_duration_value_ms)


def _summary_best_metric(text: str) -> str:
    cleaned = _summary_clean_text(text)
    percentages = SUMMARY_PERCENT_RE.findall(cleaned)
    if percentages:
        return max(percentages, key=_summary_metric_value)

    count_metrics = [
        metric.strip()
        for metric in SUMMARY_COUNT_RE.findall(cleaned)
        if not re.fullmatch(r"(19|20)\d{2}", metric.strip())
    ]
    if count_metrics:
        return max(count_metrics, key=_summary_metric_value)
    return ""


def _summary_best_percent(text: str) -> str:
    percentages = SUMMARY_PERCENT_RE.findall(_summary_clean_text(text))
    return max(percentages, key=_summary_metric_value) if percentages else ""


def _summary_best_count(text: str) -> str:
    count_metrics = [
        metric.strip()
        for metric in SUMMARY_COUNT_RE.findall(_summary_clean_text(text))
        if not re.fullmatch(r"(19|20)\d{2}", metric.strip())
    ]
    return max(count_metrics, key=_summary_metric_value) if count_metrics else ""


def _summary_large_count(count_metric: str) -> str:
    return count_metric if _summary_metric_value(count_metric) >= 10_000 else ""


def _summary_scale_suffix(count_metric: str, context: str = "") -> str:
    if not count_metric:
        return ""
    if _summary_large_count(count_metric):
        return f" for {count_metric}"
    if re.search(r"\b(data|records|patients|entries|pipeline|processing|dataset)\b", context, re.IGNORECASE):
        return " for records"
    return " for source workflows"


def _summary_impact_method(text: str) -> str:
    lowered = _summary_clean_text(text).lower()
    if re.search(r"pipeline|processing|automation|automated|etl", lowered):
        return "optimizing data pipelines"
    if re.search(r"docker|kubernetes|deploy|production|cloud", lowered):
        return "optimizing production systems"
    if re.search(r"java|jdbc|database|sql|query", lowered):
        return "optimizing backend systems"
    if re.search(r"html|css|webpage|interface|frontend|react", lowered):
        return "optimizing backend systems"
    if re.search(r"model|training|machine learning|prediction|classifier", lowered):
        return "optimizing model deployment"
    if re.search(r"api|backend|service", lowered):
        return "optimizing backend systems"
    return "optimizing backend systems"


def _summary_metric_action(text: str, metric_type: str = "") -> str:
    lowered = _summary_clean_text(text).lower()
    if re.search(r"\b(reduced|reduce|reducing|decreased|decrease|lowered|cut|shortened)\b", lowered):
        return "Reduced"
    if re.search(r"\b(increased|increase|increasing|scaled|grew|expanded)\b", lowered):
        return "Increased"
    if re.search(r"\b(improved|improve|improving|boosted|raised|enhanced|achieved)\b", lowered):
        return "Improved"
    if metric_type == "accuracy":
        return "Improved"
    if metric_type == "scale":
        return "Increased"
    return "Reduced" if re.search(r"\b(latency|processing|retrieval|query|load|response|time)\b", lowered) else "Improved"


def _summary_metric_system(text: str) -> str:
    lowered = _summary_clean_text(text).lower()
    if re.search(r"\b(pipeline|etl|data processing|batch|workflow)\b", lowered):
        return "data pipelines"
    if re.search(r"\b(model|training|classifier|prediction|accuracy|inference|mlops)\b", lowered):
        return "model deployment"
    if re.search(r"\b(api|backend|service|database|query|sql|retrieval|latency|request)\b", lowered):
        return "backend systems"
    if re.search(r"\b(docker|kubernetes|cloud|deploy|production)\b", lowered):
        return "production systems"
    return "backend systems"


def _summary_metric_outcome(text: str, metric_type: str, action: str, system: str) -> str:
    lowered = _summary_clean_text(text).lower()
    if metric_type == "accuracy" or re.search(r"\b(accuracy|precision|recall|f1|auc|score)\b", lowered):
        return "model accuracy"
    if re.search(r"\b(retrieval|query|database|sql)\b", lowered):
        return "data retrieval time"
    if re.search(r"\b(processing|pipeline|etl|batch)\b", lowered):
        return "data processing time"
    if re.search(r"\b(latency|response time|load time)\b", lowered):
        return "latency"
    if metric_type == "scale":
        if system == "data pipelines":
            return "pipeline capacity"
        if system == "model deployment":
            return "model serving capacity"
        return "backend capacity"
    if system == "data pipelines":
        return "data processing time" if action == "Reduced" else "pipeline efficiency"
    if system == "model deployment":
        return "model deployment"
    return "backend efficiency"


def _summary_metric_context(text: str, metric_type: str, system: str) -> str:
    lowered = _summary_clean_text(text).lower()
    count_metric = _summary_best_count(text)
    if count_metric:
        return f"handling {count_metric}"
    if re.search(r"\b(patient|patients|clinical|healthcare|medical)\b", lowered):
        return "patient data workflows"
    if re.search(r"\b(query|queries|database|sql|retrieval)\b", lowered):
        return "database queries"
    if re.search(r"\b(record|records)\b", lowered):
        return "record processing"
    if re.search(r"\b(data point|data points|sample|samples|dataset|datasets|batch)\b", lowered):
        return "dataset processing"
    if re.search(r"\b(request|requests|api)\b", lowered):
        return "API requests"
    if re.search(r"\b(user|users|traffic)\b", lowered):
        return "user workflows"
    if re.search(r"\b(model|inference|prediction|classifier)\b", lowered):
        return "model workflows"
    if system == "data pipelines":
        return "data pipeline workflows"
    if system == "model deployment":
        return "model workflows"
    return "backend workflows"


def _summary_metric_type(text: str, metric: str) -> str:
    lowered = _summary_clean_text(text).lower()
    if metric.endswith("%") and re.search(r"\b(accuracy|precision|recall|f1|auc|score)\b", lowered):
        return "accuracy"
    if metric.endswith("%"):
        return "percentage"
    return "scale"


def _summary_metric_record(text: str, metric: str, metric_type: str = "") -> dict:
    cleaned = _summary_clean_text(text)
    resolved_type = metric_type or _summary_metric_type(cleaned, metric)
    action = _summary_metric_action(cleaned, resolved_type)
    system = _summary_metric_system(cleaned)
    outcome = _summary_metric_outcome(cleaned, resolved_type, action, system)
    context = _summary_metric_context(cleaned, resolved_type, system)
    return {
        "metric_value": metric,
        "metric_type": resolved_type,
        "action": action,
        "system": system,
        "outcome": outcome,
        "context": context,
        "source_text": cleaned,
        "score": _summary_metric_value(metric),
    }


def _summary_performance_record(text: str, start_duration: str, end_duration: str) -> dict:
    cleaned = _summary_clean_text(text)
    system = _summary_metric_system(cleaned)
    return {
        "metric_value": f"from {start_duration} to {end_duration}",
        "metric_type": "performance",
        "action": "Reduced",
        "system": system,
        "outcome": _summary_metric_outcome(cleaned, "performance", "Reduced", system),
        "context": _summary_metric_context(cleaned, "performance", system),
        "source_text": cleaned,
        "score": _summary_duration_value_ms(start_duration) - _summary_duration_value_ms(end_duration),
    }


def _summary_metric_source_lines(result: dict, resume_text: str = "") -> list[str]:
    candidates: list[str] = []
    fallback_candidates: list[str] = []
    section_open = False
    section_found = False
    section_start_re = re.compile(
        r"^(work\s+experience|professional\s+experience|experience|employment|projects?|"
        r"project\s+experience|academic\s+projects?|personal\s+projects?)\b",
        re.IGNORECASE,
    )
    section_end_re = re.compile(
        r"^(education|skills|technical\s+skills|core\s+skills|certifications?|"
        r"summary|profile|objective|contact|achievements?|awards?)\b",
        re.IGNORECASE,
    )

    for raw_line in str(resume_text or "").splitlines():
        raw = raw_line.strip()
        line = re.sub(r"^[\s\-*\u2022\u25cf\u25aa]+", "", raw)
        if not line:
            continue
        if section_start_re.match(line):
            section_open = True
            section_found = True
            continue
        if section_open and section_end_re.match(line):
            section_open = False
            continue
        if section_open:
            candidates.append(line)
        elif re.match(r"^[\-*\u2022\u25cf\u25aa]\s+", raw):
            fallback_candidates.append(line)

    if not section_found:
        candidates.extend(fallback_candidates)

    seen: set[str] = set()
    clean_candidates: list[str] = []
    for candidate in candidates:
        cleaned = _summary_clean_text(candidate)
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        clean_candidates.append(cleaned)
    return clean_candidates


def _summary_extract_metric_records(result: dict, resume_text: str = "") -> list[dict]:
    records: list[dict] = []
    for line in _summary_metric_source_lines(result, resume_text):
        start_duration, end_duration = _summary_best_duration_pair(line)
        if start_duration and end_duration:
            records.append(_summary_performance_record(line, start_duration, end_duration))
        for metric in SUMMARY_PERCENT_RE.findall(line):
            records.append(_summary_metric_record(line, metric))
        for metric in SUMMARY_COUNT_RE.findall(line):
            metric = metric.strip()
            if re.fullmatch(r"(19|20)\d{2}", metric):
                continue
            records.append(_summary_metric_record(line, metric, "scale"))

    return records


def _summary_metric_priority(record: dict) -> tuple:
    metric_type = record.get("metric_type", "")
    source = record.get("source_text", "")
    metric_value = float(record.get("score") or 0)
    action_bonus = 1 if re.search(
        r"\b(reduced|decreased|cut|lowered|improved|increased|optimized)\b",
        source,
        re.IGNORECASE,
    ) else 0

    if metric_type in {"percentage", "accuracy"}:
        if re.search(r"\b(latency|processing|retrieval|query|load time|response time|deployment time|time)\b", source, re.IGNORECASE):
            tie_breaker = 3
        elif metric_type == "percentage":
            tie_breaker = 2
        else:
            tie_breaker = 1
        return (3, metric_value, tie_breaker, action_bonus)

    if metric_type == "performance":
        return (2, metric_value, action_bonus, 0)

    if metric_type == "scale":
        scale_rank = 1 if _summary_metric_value(record.get("metric_value", "")) >= 10_000 else 0
        return (1, scale_rank, metric_value, action_bonus)

    return (0, metric_value, action_bonus, 0)


def _summary_select_metric(result: dict, resume_text: str = "") -> dict:
    records = _summary_extract_metric_records(result, resume_text)
    if not records:
        return {}
    return max(records, key=_summary_metric_priority)


def _summary_metric_sentence(record: dict) -> str:
    action = record.get("action") or "Improved"
    metric = record.get("metric_value") or ""
    metric_type = record.get("metric_type") or ""
    outcome = record.get("outcome") or "backend efficiency"
    system = record.get("system") or "backend systems"
    context = record.get("context") or "backend workflows"
    context_phrase = (
        f" {context}"
        if context.startswith("handling ")
        else f" for {context}"
    )

    if metric_type == "accuracy":
        return f"Improved model accuracy to {metric} by optimizing {system}{context_phrase}."
    if metric_type == "performance":
        return f"{action} {outcome} {metric} by optimizing {system}{context_phrase}."
    if metric_type == "scale":
        return f"{action} {outcome} to {metric} by optimizing {system}."
    return f"{action} {outcome} by {metric} by optimizing {system}{context_phrase}."


def _summary_join_skills(skills: list[str]) -> str:
    if not skills:
        return ""
    if len(skills) == 1:
        return skills[0]
    if len(skills) == 2:
        return f"{skills[0]} and {skills[1]}"
    return f"{', '.join(skills[:-1])}, and {skills[-1]}"


def _summary_join_tools(tools: list[str]) -> str:
    if not tools:
        return ""
    if len(tools) == 1:
        return tools[0]
    if len(tools) == 2:
        return f"{tools[0]} and {tools[1]}"
    return f"{tools[0]}, {tools[1]}, and {tools[2]}"


def _summary_has_specific_system(result: dict, resume_text: str = "") -> bool:
    source_parts = [resume_text]
    for key in ("improved_bullets", "new_bullets"):
        bullets = result.get(key, [])
        if not isinstance(bullets, list):
            continue
        for bullet in bullets:
            if isinstance(bullet, dict):
                source_parts.append(str(bullet.get("improved") or bullet.get("text") or ""))
            else:
                source_parts.append(str(bullet or ""))
    source = " ".join(source_parts).lower()
    return bool(re.search(
        r"\b(pipeline|model|api|backend|database|dashboard|application|service|deployment|"
        r"classifier|prediction|etl|system|platform)\b",
        source,
    ))


def _summary_complete_sentences(value: str) -> list[str]:
    text = _summary_clean_text(value).replace("!", ".").replace("?", ".")
    matches = re.findall(r"[^.!?]+[.!?]", text)
    sentences: list[str] = []
    seen: set[str] = set()
    for match in matches:
        sentence = re.sub(r"\s+", " ", match).strip()
        sentence = re.sub(r"[.!?]+$", ".", sentence)
        key = re.sub(r"[^a-z0-9]+", " ", sentence.lower()).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        sentences.append(sentence[0].upper() + sentence[1:])
    return sentences


def _summary_metrics_valid(summary: str) -> bool:
    lowered = summary.lower()
    count_unit = r"(?:users|records|requests|data points|transactions|patients|entries|patient records|samples?)"
    count_value = rf"\d+(?:\.\d+)?\s*(?:k|m|b)?\+?\s*(?:daily\s+|monthly\s+)?{count_unit}"

    if re.search(rf"\b(accuracy|precision|recall|f1|auc|score|model quality)\b[^.]*\b{count_value}\b", lowered):
        return False
    if re.search(rf"\b{count_value}\b[^.]*\b(accuracy|precision|recall|f1|auc|score|model quality)\b", lowered):
        return False
    if re.search(r"\bimproved\s+by\s+\d+(?:\.\d+)?%", lowered):
        return False
    if re.search(r"\b(improved|enhanced)\s+performance\b(?!\s+by\s+\d+(?:\.\d+)?%)", lowered):
        return False
    if "machine learning" in lowered and "artificial intelligence" in lowered:
        return False
    if "python" in lowered and "coding" in lowered:
        return False
    if "docker" in lowered and "containers" in lowered:
        return False
    return True


def _summary_valid(value: str) -> bool:
    sentences = _summary_complete_sentences(value)
    if len(sentences) != 2:
        return False
    summary = " ".join(sentences)
    if "..." in summary or "\u2026" in summary:
        return False
    if SUMMARY_BUZZWORD_RE.search(summary):
        return False
    if SUMMARY_WEAK_PHRASES_RE.search(summary):
        return False
    if any(SUMMARY_BANNED_OPENER_RE.search(sentence) for sentence in sentences):
        return False
    if not _summary_metrics_valid(summary):
        return False
    if not re.search(r"\b(backend systems|data pipelines|model deployment|production systems)\b", summary, re.IGNORECASE):
        return False
    if not re.search(r"\b(accuracy|latency|uptime|processing|retrieval|deployment|capacity|performance|efficiency|processed|handled|supported)\b", summary, re.IGNORECASE):
        return False
    words = _summary_word_count(summary)
    return words <= 45 and all(sentence.endswith(".") for sentence in sentences)


def generate_structured_summary(
    result: dict,
    resume_text: str = "",
    job_title: str = "",
    job_description: str = "",
) -> str:
    metric_record = _summary_select_metric(result, resume_text)
    if not metric_record:
        return SUMMARY_FALLBACK_SUMMARY

    first_sentence = "Machine Learning Engineer specializing in scalable AI systems and data pipelines."
    impact_sentence = _summary_metric_sentence(metric_record)
    return " ".join([first_sentence, impact_sentence])


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
        f"JOB DESCRIPTION:\n{body.job_description}\n\n"
        f"ORIGINAL RESUME:\n{body.resume_text}\n\n"
        
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
        "- GENERATE the summary through synthesis; do not copy any\n"
        "  resume bullet or experience sentence verbatim\n"
        "- Use these inputs only: target role and the strongest\n"
        "  deterministic metric from experience/projects\n"
        "- EXACTLY 2 complete sentences, maximum 45 words total\n"
        "- Sentence 1: Machine Learning Engineer specializing in\n"
        "  scalable AI systems and data pipelines\n"
        "- Do not write 'Machine Learning and Artificial Intelligence';\n"
        "  use a specific domain such as data pipelines, model\n"
        "  deployment, computer vision, NLP, or predictive modeling\n"
        "- Sentence 2: [Built/Reduced/Improved/Deployed/Engineered]\n"
        "  [performance, efficiency, or accuracy impact] by\n"
        "  [backend systems, data pipelines, model deployment, or\n"
        "  production systems]\n"
        "- Sentence 2 must include what caused the impact\n"
        "- Metric selection priority: highest real percentage wins;\n"
        "  if percentages tie, choose performance/time reduction over\n"
        "  accuracy, then use scale only when no stronger metric exists\n"
        "- If multiple metrics exist, choose the highest-impact metric\n"
        "  from that priority order\n"
        "- Never use generic fallback wording when a real percentage,\n"
        "  accuracy, latency, retrieval-time, or processing-time metric\n"
        "  exists in experience or projects\n"
        "- Avoid weak counts such as 1000 data points; use only\n"
        "  source context already present in experience/projects\n"
        "- Accuracy metrics must be percentages only, e.g. 92% accuracy\n"
        "- Never combine accuracy with counts; never write accuracy to\n"
        "  10K+ or accuracy by 500+ records\n"
        "- Count metrics may refer only to users, records, requests,\n"
        "  data points, transactions, patients, entries, or samples\n"
        "- Never apply counts to accuracy, model quality, scores, or\n"
        "  abstract improvements\n"
        "- Improvement metrics must name what improved, e.g. reduced\n"
        "  processing time by 30% or improved query speed by 25%\n"
        "- Never write 'improved by 30%' without a subject\n"
        "- If no clear metric exists from the original resume, do not\n"
        "  invent a number; use the required no-metric fallback.\n"
        "- Never add a third tools sentence\n"
        "- Replace weak phrasing like 'built user-facing systems' with\n"
        "  reduced processing time, improved accuracy, reduced latency,\n"
        "  optimized backend systems, built scalable data pipelines,\n"
        "  model deployment, or production systems\n"
        "- The summary must include at least one of: backend systems,\n"
        "  data pipelines, model deployment, production systems\n"
        "- Keep sentences short and direct\n"
        "- Do not repeat the full skills list\n"
        "- Every sentence must end with a period\n"
        "- Never output an ellipsis or three dots\n"
        "- Never use buzzwords or filler phrases such as:\n"
        "  production-grade, applied engineering work, reliable\n"
        "  deployment practices, practical measurable outcomes,\n"
        "  maintainable solutions, delivery quality\n"
        "- Never start a sentence with Uses, Has, I, or My\n"
        "- If original resume has no usable metrics, use exactly:\n"
        "  Machine Learning Engineer specializing in scalable AI systems\n"
        "  and data pipelines, focused on building efficient backend\n"
        "  solutions.\n"
        "- NEVER include email, phone, location, city, country\n"
        "- NEVER use weak phrases: with experience in, experienced in,\n"
        "  proficient in\n"
        "- Use stronger phrasing: specializing in, focused on, building\n"
        "- NEVER use, except in the required fallback sentence:\n"
        "             passionate, motivated, hardworking, dynamic,\n"
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
        
        '  "optimized_summary": "exactly 2 clear sentences, max 45 words, engineering-focused",\n'
        
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
        result["optimized_summary"] = generate_structured_summary(
            result,
            body.resume_text,
            body.job_title or "",
            body.job_description,
        )

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
