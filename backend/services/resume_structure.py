# ============================================================
# CareerLens - Resume Structure & Source-of-Truth Representation
# File: backend/services/resume_structure.py
# ============================================================

from dataclasses import dataclass, field
import logging
import re
from typing import Any, Optional

logger = logging.getLogger("careerlens.resume_structure")

DATE_PATTERN = re.compile(
    r"\b(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s*)?"
    r"(?:19|20)\d{2}\s*(?:-|–|—|to)\s*"
    r"(?:present|current|now|(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s*)?(?:19|20)\d{2})\b"
    r"|\b(?:19|20)\d{2}\b",
    re.IGNORECASE,
)

BULLET_PREFIX_RE = re.compile(r"^[\s\-*\u2022\u25cf\u25aa\u25b8\u2013\u2014\u25e6\u25ab\u25a0\u2023\u2043]+(.*)$")
CONTINUED_RE = re.compile(r"\s*\(?continued\)?\s*", re.IGNORECASE)

SECTION_PATTERNS = [
    ("summary", re.compile(r"^(summary|professional\s+summary|profile|executive\s+summary|career\s+objective|objective)\b", re.IGNORECASE)),
    ("skills", re.compile(r"^(technical\s+skills?|core\s+skills?|skills(\s+and\s+abilities)?|technologies|proficiencies)\b", re.IGNORECASE)),
    ("experience", re.compile(r"^(work\s+experience|professional\s+experience|experience|employment|work\s+history|career\s+history)\b", re.IGNORECASE)),
    ("projects", re.compile(r"^(projects?|academic\s+projects?|personal\s+projects?|technical\s+projects?|key\s+projects?)\b", re.IGNORECASE)),
    ("education", re.compile(r"^(education|academic\s+background|academics?|qualifications?|educational\s+qualifications?)\b", re.IGNORECASE)),
    ("certifications", re.compile(r"^(certifications?|certificates?|licenses?|professional\s+certifications?)\b", re.IGNORECASE)),
]


@dataclass
class SourceBullet:
    source_id: str
    section: str  # "experience" or "projects"
    entry_id: str
    entry_name: str
    original: str


@dataclass
class SourceEntry:
    entry_id: str
    section: str  # "experience" or "projects"
    title: str = ""
    organization: str = ""
    dates: str = ""
    location: str = ""
    header_raw: str = ""
    bullets: list[SourceBullet] = field(default_factory=list)


@dataclass
class ResumeDocument:
    raw_text: str = ""
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    summary: str = ""
    skills: list[str] = field(default_factory=list)
    experience: list[SourceEntry] = field(default_factory=list)
    projects: list[SourceEntry] = field(default_factory=list)
    education: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    other_sections: list[dict[str, Any]] = field(default_factory=list)

    @property
    def experience_count(self) -> int:
        return len(self.experience)

    @property
    def project_count(self) -> int:
        return len(self.projects)

    @property
    def contact(self) -> dict[str, str]:
        return {
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "linkedin": self.linkedin,
            "github": self.github,
        }

    @property
    def education_count(self) -> int:
        return len(self.education)

    @property
    def certification_count(self) -> int:
        return len(self.certifications)

    @property
    def all_bullets(self) -> list[SourceBullet]:
        bullets = []
        for entry in self.experience:
            bullets.extend(entry.bullets)
        for entry in self.projects:
            bullets.extend(entry.bullets)
        return bullets

    @property
    def bullet_map(self) -> dict[str, SourceBullet]:
        return {b.source_id: b for b in self.all_bullets}


def _clean_line(line: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(line or "")).strip()
    cleaned = CONTINUED_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\bover\s*~\s*(\d)", r"\1", cleaned)
    cleaned = re.sub(r"~\s*(\d)", r"\1", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w+#.%-]+\b", str(text or "")))


def _is_section_header(line: str) -> Optional[str]:
    cleaned = _clean_line(line)
    if not cleaned:
        return None
    header_candidate = re.sub(r"[:|-]+$", "", cleaned).strip()
    for sec_name, pattern in SECTION_PATTERNS:
        if pattern.match(header_candidate) or header_candidate.lower() == sec_name:
            return sec_name
    # Short uppercase line check
    if len(header_candidate) <= 40 and header_candidate.isupper() and any(c.isalpha() for c in header_candidate):
        for sec_name, pattern in SECTION_PATTERNS:
            if pattern.search(header_candidate):
                return sec_name
    return None


def _is_entry_header_candidate(line: str, in_bullets: bool = False) -> bool:
    cleaned = _clean_line(line)
    if not cleaned:
        return False
    if BULLET_PREFIX_RE.match(cleaned):
        return False
    # If already parsing bullets inside an entry, require a clear entry-level separator or date
    if in_bullets:
        if "|" in cleaned or "•" in cleaned:
            parts = [p.strip() for p in re.split(r"[\s]*[|•][\s]*", cleaned) if p.strip()]
            if len(parts) >= 2:
                return True
        if DATE_PATTERN.search(cleaned):
            return True
        return False
    # If line has pipe or bullet separators often used in "Company | Title | Date"
    if "|" in cleaned or "•" in cleaned:
        return True
    # If line has a date range
    if DATE_PATTERN.search(cleaned):
        return True
    # If line is short and doesn't end with a period
    if len(cleaned.split()) <= 8 and not cleaned.endswith((".", ";", ":")):
        return True
    return False


ROLE_KEYWORDS = {
    "intern", "engineer", "developer", "lead", "manager", "specialist",
    "analyst", "architect", "director", "scientist", "consultant",
    "designer", "researcher", "assistant", "associate", "officer",
    "administrator", "head", "vp", "president", "fellow", "programmer",
}
ORG_KEYWORDS = {
    "pvt", "ltd", "inc", "corp", "llc", "technologies", "analytics",
    "solutions", "systems", "labs", "company", "group", "services",
    "gmbh", "co.", "university", "institute", "foundation", "agency",
}


def _is_placeholder_title(text: str) -> bool:
    if not text:
        return True
    cleaned = _clean_line(text).strip()
    if not cleaned:
        return True
    # e.g., "X Entry N", "Experience Entry 1", "Projects Entry 2", "Entry 1"
    if re.search(r"\bentry\s+\d+\b", cleaned, re.I):
        return True
    # e.g., "EXPERIENCE", "PROJECTS", "SUMMARY", "SKILLS", "EDUCATION", "CERTIFICATIONS"
    if _is_section_header(cleaned) is not None:
        return True
    if cleaned.lower() in {
        "experience", "work experience", "projects", "key projects", "technical projects",
        "relevant experience", "employment", "summary", "skills", "education", "certifications",
    }:
        return True
    return False


def _parse_entry_header(line: str) -> tuple[str, str, str, str]:
    """Returns (organization/company, title/role, dates, location)."""
    cleaned = _clean_line(line)
    dates = ""
    date_match = DATE_PATTERN.search(cleaned)
    if date_match:
        dates = date_match.group(0).strip()
        cleaned_no_date = cleaned[:date_match.start()] + cleaned[date_match.end():]
        cleaned_no_date = re.sub(r"[\s,|–—-]+$", "", cleaned_no_date).strip()
    else:
        cleaned_no_date = cleaned

    parts = [p.strip() for p in re.split(r"[\s]*[|•][\s]*", cleaned_no_date) if p.strip()]
    if len(parts) >= 2:
        p0_role = any(kw in parts[0].lower() for kw in ROLE_KEYWORDS)
        p1_org = any(kw in parts[1].lower() for kw in ORG_KEYWORDS)
        p0_org = any(kw in parts[0].lower() for kw in ORG_KEYWORDS)
        p1_role = any(kw in parts[1].lower() for kw in ROLE_KEYWORDS)
        if (p0_role or p1_org) and not (p0_org and not p1_org):
            title = parts[0]
            org = parts[1]
        elif (p1_role or p0_org) and not (p0_role and not p1_org):
            org = parts[0]
            title = parts[1]
        else:
            # Default to source order: Company / Project Name | Title / Tech
            org = parts[0]
            title = parts[1]
        loc = parts[2] if len(parts) > 2 else ""
        return org, title, dates, loc
    if len(parts) == 1:
        # Check if comma or hyphen separates company and title
        subparts = [p.strip() for p in re.split(r"\s+-\s+|\s*,\s*", parts[0]) if p.strip()]
        if len(subparts) >= 2:
            p0_role = any(kw in subparts[0].lower() for kw in ROLE_KEYWORDS)
            p1_org = any(kw in subparts[1].lower() for kw in ORG_KEYWORDS)
            p0_org = any(kw in subparts[0].lower() for kw in ORG_KEYWORDS)
            p1_role = any(kw in subparts[1].lower() for kw in ROLE_KEYWORDS)
            if (p0_role or p1_org) and not (p0_org and not p1_org):
                return subparts[1], subparts[0], dates, ""
            elif (p1_role or p0_org) and not (p0_role and not p1_org):
                return subparts[0], subparts[1], dates, ""
            else:
                return subparts[1], subparts[0], dates, ""
        if any(kw in parts[0].lower() for kw in ROLE_KEYWORDS):
            return "", parts[0], dates, ""
        return parts[0], "", dates, ""
    return "", "", dates, ""


def _parse_section_entries(section_name: str, lines: list[str]) -> list[SourceEntry]:
    entries: list[SourceEntry] = []
    current_entry: Optional[SourceEntry] = None
    sec_prefix = "project" if section_name.startswith("project") else section_name
    canonical_sec = "projects" if sec_prefix == "project" else sec_prefix

    # Step 1: Preprocess lines to attach standalone bullet markers and drop section headers/placeholders
    preprocessed: list[tuple[str, bool]] = []
    pending_marker = False

    for raw_line in lines:
        line = _clean_line(raw_line)
        if not line or line.lower() == "continued":
            continue
        # Drop section headers inside section (e.g. 'EXPERIENCE', 'PROJECTS', 'SUMMARY')
        if _is_section_header(line) is not None or _is_placeholder_title(line):
            continue

        b_match = BULLET_PREFIX_RE.match(line)
        if b_match:
            bullet_body = b_match.group(1).strip()
            if not bullet_body:
                # Standalone bullet marker on its own line like '-' or '•'
                pending_marker = True
                continue
            else:
                preprocessed.append((bullet_body, True))
                pending_marker = False
        else:
            if pending_marker:
                preprocessed.append((line, True))
                pending_marker = False
            else:
                preprocessed.append((line, False))

    # Step 2: Parse into entries and merge line-wraps
    for line, is_bullet in preprocessed:
        has_bullets = bool(current_entry and current_entry.bullets)

        if not is_bullet and _is_entry_header_candidate(line, in_bullets=has_bullets):
            # Never treat section headers or placeholder strings as entry headers
            if _is_section_header(line) is not None or _is_placeholder_title(line):
                continue

            org, title, dates, loc = _parse_entry_header(line)
            # If an entry has no title, merge it into the previous entry or drop it.
            # Never create a project or role with no source text behind it.
            if canonical_sec == "projects":
                project_name = org or title
                technologies = title if title != org else ""
                if not project_name or _is_placeholder_title(project_name):
                    continue
                idx = len(entries) + 1
                entry_id = f"{sec_prefix}_{idx:03d}"
                current_entry = SourceEntry(
                    entry_id=entry_id,
                    section=canonical_sec,
                    title=technologies,
                    organization=project_name,
                    dates=dates,
                    location=loc,
                    header_raw=line,
                    bullets=[],
                )
                entries.append(current_entry)
                continue
            else:
                # Experience section:
                has_title = bool(
                    (title and not _is_placeholder_title(title))
                    or (org and not _is_placeholder_title(org))
                )
                if not has_title:
                    continue
                idx = len(entries) + 1
                entry_id = f"{sec_prefix}_{idx:03d}"
                current_entry = SourceEntry(
                    entry_id=entry_id,
                    section=canonical_sec,
                    title=title or org,
                    organization=org or title,
                    dates=dates,
                    location=loc,
                    header_raw=line,
                    bullets=[],
                )
                entries.append(current_entry)
                continue

        # Line-wrap merge check:
        # A line that doesn't start with a bullet marker and follows a bullet should be appended to that bullet.
        # Also merge when previous line ends without terminal punctuation.
        if current_entry and current_entry.bullets:
            prev_bullet = current_entry.bullets[-1]
            prev_ends_punct = prev_bullet.original.rstrip().endswith((".", "!", "?", ":"))

            should_merge = False
            if not is_bullet:
                # Line does not start with a bullet marker and follows a bullet
                should_merge = True
            elif not prev_ends_punct:
                # Previous line ends without terminal punctuation
                should_merge = True
            elif _word_count(line) < 5 or (line and line[0].islower()):
                # Fragment under 5 words or lower-case start
                should_merge = True

            if should_merge:
                prev_bullet.original = f"{prev_bullet.original.rstrip()} {line.lstrip()}".strip()
                continue

        # If not merged, handle bullet
        if not current_entry:
            if entries:
                # If an entry has no title, merge it into the previous entry
                current_entry = entries[-1]
            else:
                # Titleless container for source bullets - never assign placeholder 'X Entry N' titles
                idx = len(entries) + 1
                entry_id = f"{sec_prefix}_{idx:03d}"
                current_entry = SourceEntry(
                    entry_id=entry_id,
                    section=canonical_sec,
                    title="",
                    organization="",
                    header_raw="",
                    bullets=[],
                )
                entries.append(current_entry)

        b_idx = len(current_entry.bullets) + 1
        source_id = f"{current_entry.entry_id}_bullet_{b_idx:03d}"
        current_entry.bullets.append(
            SourceBullet(
                source_id=source_id,
                section=canonical_sec,
                entry_id=current_entry.entry_id,
                entry_name=current_entry.title or current_entry.organization,
                original=line,
            )
        )

    # Post-process: ensure no bullet under 5 words, no (continued), merge/drop entries with no title, drop empty entries
    clean_entries: list[SourceEntry] = []
    for entry in entries:
        title_valid = bool(entry.title and not _is_placeholder_title(entry.title))
        org_valid = bool(entry.organization and not _is_placeholder_title(entry.organization))
        if not title_valid and not org_valid:
            if clean_entries:
                clean_entries[-1].bullets.extend(entry.bullets)
                continue
            elif len(entries) > 1:
                continue

        cleaned_bullets: list[SourceBullet] = []
        for b in entry.bullets:
            b_text = _clean_line(b.original)
            if not b_text or b_text.lower() == "continued":
                continue
            if _word_count(b_text) < 5:
                if cleaned_bullets:
                    cleaned_bullets[-1].original = f"{cleaned_bullets[-1].original.rstrip()} {b_text}".strip()
                else:
                    b.original = b_text
                    cleaned_bullets.append(b)
            else:
                b.original = b_text
                cleaned_bullets.append(b)

        if len(cleaned_bullets) >= 2 and _word_count(cleaned_bullets[0].original) < 5:
            first = cleaned_bullets.pop(0)
            cleaned_bullets[0].original = f"{first.original.rstrip()} {cleaned_bullets[0].original}".strip()

        final_bullets = [b for b in cleaned_bullets if _word_count(b.original) >= 5 and b.original.lower() != "continued"]
        if not final_bullets:
            continue

        entry.bullets = final_bullets
        clean_entries.append(entry)

    # Re-index clean_entries sequentially
    for idx, entry in enumerate(clean_entries, 1):
        entry.entry_id = f"{sec_prefix}_{idx:03d}"
        for b_idx, b in enumerate(entry.bullets, 1):
            b.source_id = f"{entry.entry_id}_bullet_{b_idx:03d}"
            b.entry_id = entry.entry_id
            b.entry_name = entry.title or entry.organization
            b.section = canonical_sec

    return clean_entries


def _split_preserving_parens(text: str) -> list[str]:
    """Splits a string by commas, pipes, semicolons, bullets outside parentheses."""
    items = []
    current = []
    depth = 0
    for char in text:
        if char in "([{":
            depth += 1
            current.append(char)
        elif char in ")]}":
            depth = max(0, depth - 1)
            current.append(char)
        elif depth == 0 and char in ",|;•\t":
            part = "".join(current).strip()
            if part:
                items.append(part)
            current = []
        else:
            current.append(char)
    last = "".join(current).strip()
    if last:
        items.append(last)
    return items


def parse_source_resume(text: str) -> ResumeDocument:
    """Parses raw resume text into a normalized, structured ResumeDocument."""
    from services.professional_resume_pdf import _extract_source_contact_and_certs, is_education_text

    raw_text = str(text or "").strip()
    contact = _extract_source_contact_and_certs(raw_text)

    # First pass: find candidate name from top lines
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    candidate_name = ""
    for line in lines[:5]:
        if (
            not _is_section_header(line)
            and not is_education_text(line)
            and "@" not in line
            and not re.search(r"linkedin|github", line, re.IGNORECASE)
            and not re.search(r"\d{6,}", line)
        ):
            candidate_name = line
            break

    # Second pass: group lines by section
    sections: dict[str, list[str]] = {}
    current_sec = "header"
    for line in lines:
        sec_header = _is_section_header(line)
        if sec_header:
            current_sec = sec_header
            sections.setdefault(current_sec, [])
            inline_content = re.sub(r"^[^:\-–—|]+[:\-–—|]\s*", "", line).strip()
            if inline_content and inline_content.lower() != line.lower() and not _is_section_header(inline_content):
                sections[current_sec].append(inline_content)
        else:
            sections.setdefault(current_sec, []).append(line)

    # Extract summary
    summary_lines = sections.get("summary", [])
    summary_text = " ".join(summary_lines).strip()


    # Extract skills
    skills_lines = sections.get("skills", [])
    extracted_skills: list[str] = []
    for s_line in skills_lines:
        cleaned = re.sub(r"^(?:technical\s+|core\s+)?skills?\s*[:|-]\s*", "", s_line, flags=re.IGNORECASE)
        for item in _split_preserving_parens(cleaned):
            item_clean = re.sub(r"^[A-Za-z &/]+:\s*", "", item.strip().strip("-*•"))
            if item_clean and len(item_clean) > 1 and item_clean not in extracted_skills:
                extracted_skills.append(item_clean)

    # Extract experience and project entries
    experience_entries = _parse_section_entries("experience", sections.get("experience", []))
    project_entries = _parse_section_entries("projects", sections.get("projects", []))

    # Extract education and certifications
    education_lines = [l for l in sections.get("education", []) if l]
    cert_lines = [l for l in sections.get("certifications", []) if l]
    if not cert_lines and contact.get("certifications"):
        cert_lines = list(contact.get("certifications") or [])

    return ResumeDocument(
        raw_text=raw_text,
        name=candidate_name or "Your Name",
        email=contact.get("email") or "",
        phone=contact.get("phone") or "",
        location=contact.get("location") or "",
        linkedin=contact.get("linkedin") or "",
        github=contact.get("github") or "",
        summary=summary_text,
        skills=extracted_skills,
        experience=experience_entries,
        projects=project_entries,
        education=education_lines,
        certifications=cert_lines,
    )


def build_source_items_for_prompt(doc: ResumeDocument) -> list[dict[str, Any]]:
    """Builds the list of structured source items to be sent to the LLM for transformation."""
    items: list[dict[str, Any]] = []
    for entry in doc.experience:
        for bullet in entry.bullets:
            items.append({
                "source_id": bullet.source_id,
                "section": "experience",
                "entry_name": entry.title or entry.organization,
                "original": bullet.original,
            })
    for entry in doc.projects:
        for bullet in entry.bullets:
            items.append({
                "source_id": bullet.source_id,
                "section": "projects",
                "entry_name": entry.title or entry.organization,
                "original": bullet.original,
            })
    return items


def reconstruct_resume_structure(
    doc: ResumeDocument,
    bullet_rewrites: dict[str, dict[str, Any]],
    optimized_summary: str = "",
    optimized_skills: Any = None,
) -> dict[str, Any]:
    """Reconstructs the original resume hierarchy with validated optimized content."""
    reconstructed_experience = []
    for entry in doc.experience:
        entry_bullets = []
        for bullet in entry.bullets:
            rewrite = bullet_rewrites.get(bullet.source_id)
            cand_text = ""
            if isinstance(rewrite, dict):
                cand_text = str(rewrite.get("improved") or rewrite.get("text") or "").strip()
            elif isinstance(rewrite, str):
                cand_text = rewrite.strip()

            if cand_text:
                candidate = _clean_line(cand_text)
                if candidate and candidate.lower() != "continued":
                    entry_bullets.append(candidate)
                else:
                    entry_bullets.append(_clean_line(bullet.original))
            else:
                entry_bullets.append(_clean_line(bullet.original))

        if not entry_bullets:
            continue

        org = entry.organization if not _is_placeholder_title(entry.organization) else ""
        title = entry.title if not _is_placeholder_title(entry.title) else ""
        if org.lower() == title.lower():
            title = ""

        reconstructed_experience.append({
            "entry_id": entry.entry_id,
            "organization": org,
            "title": title,
            "dates": entry.dates,
            "location": entry.location,
            "header_raw": entry.header_raw,
            "bullets": entry_bullets,
        })

    reconstructed_projects = []
    for entry in doc.projects:
        entry_bullets = []
        for bullet in entry.bullets:
            rewrite = bullet_rewrites.get(bullet.source_id)
            cand_text = ""
            if isinstance(rewrite, dict):
                cand_text = str(rewrite.get("improved") or rewrite.get("text") or "").strip()
            elif isinstance(rewrite, str):
                cand_text = rewrite.strip()

            if cand_text:
                candidate = _clean_line(cand_text)
                if candidate and candidate.lower() != "continued":
                    entry_bullets.append(candidate)
                else:
                    entry_bullets.append(_clean_line(bullet.original))
            else:
                entry_bullets.append(_clean_line(bullet.original))

        if not entry_bullets:
            continue

        org = entry.organization if not _is_placeholder_title(entry.organization) else ""
        title = entry.title if not _is_placeholder_title(entry.title) else ""
        name = org or title
        tech = title if title != org else ""

        reconstructed_projects.append({
            "entry_id": entry.entry_id,
            "name": name,
            "organization": org,
            "technologies": tech,
            "dates": entry.dates,
            "header_raw": entry.header_raw,
            "bullets": entry_bullets,
        })

    return {
        "name": doc.name,
        "contact": {
            "email": doc.email,
            "phone": doc.phone,
            "location": doc.location,
            "linkedin": doc.linkedin,
            "github": doc.github,
        },
        "summary": optimized_summary or doc.summary,
        "skills": _ensure_output_skills_superset(
            optimized_skills,
            list(dict.fromkeys(doc.skills + _extract_tech_tokens_from_doc(doc))),
            doc=doc,
        ),
        "experience": reconstructed_experience,
        "projects": reconstructed_projects,
        "education": [
            re.sub(r"\b(CGPA|GPA)\s+([0-9.]+(?:/[0-9.]+)?)\b", lambda m: f"{m.group(1)}\u00a0{m.group(2)}", _clean_line(e))
            for e in doc.education
        ],
        "certifications": doc.certifications,
    }


COMMON_TECH_CANONICAL = {
    "ci/cd": "CI/CD", "xgboost": "XGBoost", "sql": "SQL", "pandas": "Pandas", "numpy": "NumPy",
    "pytorch": "PyTorch", "scikit-learn": "scikit-learn", "sklearn": "scikit-learn", "fastapi": "FastAPI",
    "docker": "Docker", "git": "Git", "mlflow": "MLflow", "aws": "AWS", "linux": "Linux",
    "c++": "C++", "python": "Python", "opencv": "OpenCV", "onnx": "ONNX", "bert": "BERT",
    "resnet": "ResNet-50", "resnet-50": "ResNet-50", "flask": "Flask",
    "hugging face transformers": "Hugging Face Transformers", "transformers": "Transformers",
    "feature engineering": "Feature Engineering", "model inference": "Model Inference",
    "kubernetes": "Kubernetes", "jenkins": "Jenkins", "spark": "Apache Spark", "kafka": "Apache Kafka",
}


def _extract_tech_tokens_from_doc(doc: ResumeDocument) -> list[str]:
    tokens: list[str] = []
    # From project stack lines (e.g. Project Name | Stack)
    for p in doc.projects:
        header = p.header_raw or ""
        if "|" in header:
            parts = header.split("|")
            for raw_item in _split_preserving_parens(parts[1]):
                cleaned = raw_item.strip()
                if not cleaned:
                    continue
                c_low = cleaned.lower()
                if c_low in COMMON_TECH_CANONICAL:
                    tokens.append(COMMON_TECH_CANONICAL[c_low])
                else:
                    tokens.append(cleaned)
    # From all bullets
    for b in doc.all_bullets:
        text = b.original or ""
        for kw, canonical in COMMON_TECH_CANONICAL.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
                tokens.append(canonical)
    return list(dict.fromkeys(tokens))


def _ensure_output_skills_superset(
    optimized_skills: Any,
    source_skills: list[str],
    doc: Optional[ResumeDocument] = None,
) -> Any:
    if not source_skills:
        return optimized_skills

    if optimized_skills is None or (isinstance(optimized_skills, dict) and not optimized_skills) or (isinstance(optimized_skills, list) and not optimized_skills):
        if doc and doc.raw_text:
            try:
                from routers.optimizer import _extract_source_skill_groups
                optimized_skills = _extract_source_skill_groups(doc.raw_text)
            except Exception:
                pass
        if not optimized_skills:
            optimized_skills = list(source_skills)

    # Detect parenthetical detailed forms across all inputs (e.g. "AWS (S3, EC2)")
    parenthetical_map: dict[str, str] = {}
    for s in source_skills:
        m = re.match(r"^([^(]+)\s*\(([^)]+)\)$", str(s or "").strip())
        if m:
            base = m.group(1).strip().lower()
            parenthetical_map[base] = str(s).strip()

    if isinstance(optimized_skills, dict):
        for v in optimized_skills.values():
            if isinstance(v, list):
                for s in v:
                    m = re.match(r"^([^(]+)\s*\(([^)]+)\)$", str(s or "").strip())
                    if m:
                        base = m.group(1).strip().lower()
                        parenthetical_map[base] = str(s).strip()

    if isinstance(optimized_skills, dict):
        result_skills = {k: list(v) for k, v in optimized_skills.items()}

        # FIX D3: Preserve source groups and their order if doc is available
        source_group_order: list[str] = []
        if doc and doc.raw_text:
            try:
                from routers.optimizer import _extract_source_skill_groups
                sg = _extract_source_skill_groups(doc.raw_text)
                if sg:
                    source_group_order = list(sg.keys())
            except Exception:
                pass

        if source_group_order:
            key_map: dict[str, str] = {}
            for src_k in source_group_order:
                match_cat = next((cat for cat in result_skills if cat.lower() == src_k.lower()), None)
                if not match_cat:
                    match_cat = next((cat for cat in result_skills if src_k.lower() in cat.lower() or cat.lower() in src_k.lower()), None)
                if match_cat:
                    key_map[src_k] = match_cat

            if key_map:
                ordered_keys = list(dict.fromkeys(list(key_map.values()) + list(result_skills.keys())))
            else:
                ordered_keys = list(dict.fromkeys(list(source_group_order) + list(result_skills.keys())))

            ordered_skills: dict[str, list[str]] = {k: [] for k in ordered_keys}
            for cat, items in result_skills.items():
                target_cat = cat if cat in ordered_skills else None
                if not target_cat:
                    for src_k, mapped_k in key_map.items():
                        if cat.lower() in src_k.lower() or src_k.lower() in cat.lower() or cat.lower() in mapped_k.lower():
                            target_cat = mapped_k
                            break
                for item in items:
                    if target_cat:
                        ordered_skills[target_cat].append(item)
                    else:
                        item_low = item.lower()
                        if any(k in item_low for k in ["python", "sql", "c++", "java", "javascript", "golang", "rust", "typescript", "bash"]) and any("language" in k.lower() for k in ordered_skills):
                            t_g = next(k for k in ordered_skills if "language" in k.lower())
                            ordered_skills[t_g].append(item)
                        elif any(k in item_low for k in ["pytorch", "scikit", "pandas", "numpy", "transformers", "xgboost", "tensor", "model", "feature engineering", "opencv", "onnx", "bert", "resnet"]) and any("ml" in k.lower() or "data" in k.lower() for k in ordered_skills):
                            t_g = next(k for k in ordered_skills if "ml" in k.lower() or "data" in k.lower())
                            ordered_skills[t_g].append(item)
                        elif any("tool" in k.lower() or "devops" in k.lower() or "platform" in k.lower() for k in ordered_skills):
                            t_g = next(k for k in ordered_skills if "tool" in k.lower() or "devops" in k.lower() or "platform" in k.lower())
                            ordered_skills[t_g].append(item)
                        else:
                            ordered_skills[list(ordered_skills.keys())[0]].append(item)
            result_skills = ordered_skills

        existing_flat = {s.lower() for v in result_skills.values() for s in (v if isinstance(v, list) else [v])}

        # Keep Feature Engineering under ML & Data if present
        if "ML & Data" in result_skills:
            ml_data_lower = {s.lower() for s in result_skills["ML & Data"]}
            if "feature engineering" not in ml_data_lower:
                for grp, items in list(result_skills.items()):
                    if grp != "ML & Data":
                        result_skills[grp] = [x for x in items if x.lower() != "feature engineering"]
                result_skills["ML & Data"].append("Feature Engineering")
                existing_flat.add("feature engineering")

        # Ensure all source skills and tech tokens are present (output skills ⊇ source skills)
        for src_skill in source_skills:
            lower_src = src_skill.lower()
            base_src = re.sub(r"\s*\([^)]*\)", "", lower_src).strip()
            # If parenthetical version already exists, skip
            if any(lower_src == s.lower() or (base_src == re.sub(r"\s*\([^)]*\)", "", s.lower()).strip() and "(" in s) for s in existing_flat):
                continue

            added = False
            if ("feature engineering" in lower_src or "opencv" in lower_src) and any("ml" in k.lower() or "data" in k.lower() for k in result_skills):
                target_g = next(k for k in result_skills if "ml" in k.lower() or "data" in k.lower())
                result_skills[target_g].append(src_skill)
                added = True
            elif any(k in lower_src for k in ["python", "sql", "c++", "java", "javascript", "golang", "rust", "typescript", "bash"]) and any("language" in k.lower() for k in result_skills):
                target_g = next(k for k in result_skills if "language" in k.lower())
                result_skills[target_g].append(src_skill)
                added = True
            elif any(k in lower_src for k in ["pytorch", "scikit", "pandas", "numpy", "transformers", "xgboost", "tensor", "model", "onnx", "bert", "resnet"]) and any("ml" in k.lower() or "data" in k.lower() for k in result_skills):
                target_g = next(k for k in result_skills if "ml" in k.lower() or "data" in k.lower())
                result_skills[target_g].append(src_skill)
                added = True
            elif any(k in lower_src for k in ["docker", "git", "ci/cd", "fastapi", "aws", "linux", "cloud", "mlflow", "flask", "kubernetes", "jenkins"]) and any("tool" in k.lower() or "devops" in k.lower() or "platform" in k.lower() for k in result_skills):
                target_g = next(k for k in result_skills if "tool" in k.lower() or "devops" in k.lower() or "platform" in k.lower())
                result_skills[target_g].append(src_skill)
                added = True
            if not added:
                target_g = list(result_skills.keys())[-1]
                result_skills[target_g].append(src_skill)
                added = True
            if added:
                existing_flat.add(lower_src)

        # Merge "AWS" with "AWS (S3, EC2)" case-insensitively across ALL groups:
        for base, detailed in parenthetical_map.items():
            has_detailed = any(any(detailed.lower() == s.lower() for s in items) for items in result_skills.values())
            if has_detailed:
                for cat in result_skills:
                    result_skills[cat] = [s for s in result_skills[cat] if s.lower() != base]

        # Dedupe each category case-insensitively
        for category in result_skills:
            if isinstance(result_skills[category], list):
                seen_in_cat = set()
                deduped_cat = []
                for s in result_skills[category]:
                    if s.lower() not in seen_in_cat:
                        seen_in_cat.add(s.lower())
                        deduped_cat.append(s)
                result_skills[category] = deduped_cat

        return result_skills

    if isinstance(optimized_skills, list):
        res_list = list(optimized_skills)
        flat_lower = {s.lower() for s in res_list}
        for src_skill in source_skills:
            if src_skill.lower() not in flat_lower:
                res_list.append(src_skill)
                flat_lower.add(src_skill.lower())
        return res_list

    return optimized_skills
