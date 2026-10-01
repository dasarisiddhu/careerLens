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

BULLET_PREFIX_RE = re.compile(r"^[\s\-*\u2022\u25cf\u25aa\u25b8\u2013\u2014]+(.*)$")

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
    return re.sub(r"\s+", " ", str(line or "")).strip()


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


def _is_entry_header_candidate(line: str) -> bool:
    cleaned = _clean_line(line)
    if not cleaned:
        return False
    if BULLET_PREFIX_RE.match(cleaned):
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
        org = parts[0]
        title = parts[1]
        loc = parts[2] if len(parts) > 2 else ""
        return org, title, dates, loc
    if len(parts) == 1:
        # Check if comma or hyphen separates company and title
        subparts = [p.strip() for p in re.split(r"\s+-\s+|\s*,\s*", parts[0]) if p.strip()]
        if len(subparts) >= 2:
            return subparts[0], subparts[1], dates, ""
        return parts[0], "", dates, ""
    return cleaned, "", dates, ""


def _parse_section_entries(section_name: str, lines: list[str]) -> list[SourceEntry]:
    entries: list[SourceEntry] = []
    current_entry: Optional[SourceEntry] = None
    sec_prefix = "project" if section_name.startswith("project") else section_name

    for raw_line in lines:
        line = _clean_line(raw_line)
        if not line:
            continue

        bullet_match = BULLET_PREFIX_RE.match(line)
        is_bullet = bool(bullet_match)

        if not is_bullet and _is_entry_header_candidate(line):
            # New entry header
            idx = len(entries) + 1
            entry_id = f"{sec_prefix}_{idx:03d}"
            org, title, dates, loc = _parse_entry_header(line)
            current_entry = SourceEntry(
                entry_id=entry_id,
                section="projects" if sec_prefix == "project" else sec_prefix,
                title=title or org,
                organization=org,
                dates=dates,
                location=loc,
                header_raw=line,
                bullets=[],
            )
            entries.append(current_entry)
        else:
            # Bullet point
            bullet_text = bullet_match.group(1).strip() if bullet_match else line
            if not current_entry:
                idx = len(entries) + 1
                entry_id = f"{sec_prefix}_{idx:03d}"
                current_entry = SourceEntry(
                    entry_id=entry_id,
                    section="projects" if sec_prefix == "project" else sec_prefix,
                    title=f"{section_name.title()} Entry {idx}",
                    organization=f"{section_name.title()} Entry {idx}",
                    header_raw="",
                    bullets=[],
                )
                entries.append(current_entry)

            b_idx = len(current_entry.bullets) + 1
            source_id = f"{current_entry.entry_id}_bullet_{b_idx:03d}"
            current_entry.bullets.append(
                SourceBullet(
                    source_id=source_id,
                    section="projects" if sec_prefix == "project" else sec_prefix,
                    entry_id=current_entry.entry_id,
                    entry_name=current_entry.title or current_entry.organization,
                    original=bullet_text,
                )
            )

    return entries


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
        for item in re.split(r"[,|;/•\t]", cleaned):
            item_clean = item.strip().strip("-*•")
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
            if rewrite and rewrite.get("improved"):
                entry_bullets.append(rewrite["improved"])
            else:
                entry_bullets.append(bullet.original)
        reconstructed_experience.append({
            "entry_id": entry.entry_id,
            "organization": entry.organization,
            "title": entry.title,
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
            if rewrite and rewrite.get("improved"):
                entry_bullets.append(rewrite["improved"])
            else:
                entry_bullets.append(bullet.original)
        reconstructed_projects.append({
            "entry_id": entry.entry_id,
            "name": entry.organization or entry.title,
            "organization": entry.organization,
            "technologies": entry.title if entry.title != entry.organization else "",
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
        "skills": optimized_skills or doc.skills,
        "experience": reconstructed_experience,
        "projects": reconstructed_projects,
        "education": doc.education,
        "certifications": doc.certifications,
    }
