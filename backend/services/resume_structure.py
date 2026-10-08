# ============================================================
# CareerLens - Resume Structure & Source-of-Truth Representation
# File: backend/services/resume_structure.py
# ============================================================

from dataclasses import dataclass, field
import logging
import re
from typing import Any, Optional

logger = logging.getLogger("careerlens.resume_structure")

MONTH_NAMES = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
DATE_ITEM = rf"(?:(?:0?[1-9]|1[0-2])/(?:19|20)\d{{2}}|(?:{MONTH_NAMES}\s*)?(?:19|20)\d{{2}})"
END_ITEM = rf"(?:present|current|now|(?:0?[1-9]|1[0-2])/(?:19|20)\d{{2}}|(?:{MONTH_NAMES}\s*)?(?:(?:19|20)\d{{2}}|\d{{2}}))"
DATE_SEP = r"\s*(?:-|–|—|to)\s*"

DATE_PATTERN = re.compile(
    rf"\b{DATE_ITEM}{DATE_SEP}{END_ITEM}\b"
    rf"|\b(?:0?[1-9]|1[0-2])/(?:19|20)\d{{2}}\b"
    rf"|\b(?:{MONTH_NAMES}\s*)?(?:19|20)\d{{2}}\b",
    re.IGNORECASE,
)

BULLET_PREFIX_RE = re.compile(r"^[\s\-*\u2022\u25cf\u25aa\u25b8\u2013\u2014\u25e6\u25ab\u25a0\u2023\u2043]+(.*)$")
CONTINUED_RE = re.compile(r"\s*\(?\bcontinued\b\)?\s*", re.IGNORECASE)

_SUMMARY_PATS = r"summary|professional\s+summary|profile|executive\s+summary|career\s+objective|objective|about\s+me"
_SKILLS_PATS = r"technical\s+skills?|core\s+skills?|key\s+skills?|soft\s+skills?|core\s+competencies|skills(\s+(?:and|&)\s+abilities)?|skills\s+(?:and|&)\s+technologies|technologies|proficiencies"
_EXP_PATS = r"work\s+experience|professional\s+experience|experience|employment|work\s+history|career\s+history|internships?|internship\s+experience"
_PROJ_PATS = r"projects?|selected\s+projects?|notable\s+projects?|side\s+projects?|personal\s+projects?|academic\s+projects?|technical\s+projects?|key\s+projects?|open\s+source(\s+projects?)?"
_EDU_PATS = r"education|academic\s+background|academics?|qualifications?|educational\s+qualifications?"
_CERT_PATS = r"certifications?|certificates?|licenses?|professional\s+certifications?"
_KW_PATS = r"keywords?|ats\s+keywords?"
_ACHIEVE_PATS = r"achievements?|accomplishments?|awards?(\s+(?:and|&)\s+(?:honou?rs|achievements?))?|honou?rs(\s+(?:and|&)\s+awards?)?|awards\s+(?:and|&)\s+achievements|achievements\s+(?:and|&)\s+awards|honors\s+(?:and|&)\s+awards|honours\s+(?:and|&)\s+awards"
_ACT_PATS = r"extra[\s-]?curricular(\s+activities)?|activities|hackathons?|leadership(\s+(?:and|&)\s+activities)?|volunteering|volunteer\s+experience|positions?\s+of\s+responsibility|clubs?(\s+(?:and|&)\s+societies)?"
_PUB_PATS = r"publications?|research\s+papers?"
_INT_PATS = r"interests|hobbies|hobbies\s+(?:and|&)\s+interests"

SECTION_PATTERNS = [
    ("summary", re.compile(rf"^\s*(?:{_SUMMARY_PATS})\s*(?::|&)?\s*$", re.IGNORECASE)),
    ("skills", re.compile(rf"^\s*(?:{_SKILLS_PATS})\s*(?::|&)?\s*$", re.IGNORECASE)),
    ("experience", re.compile(rf"^\s*(?:{_EXP_PATS})\s*(?::|&)?\s*$", re.IGNORECASE)),
    ("projects", re.compile(rf"^\s*(?:{_PROJ_PATS})\s*(?::|&)?\s*$", re.IGNORECASE)),
    ("education", re.compile(rf"^\s*(?:{_EDU_PATS})\s*(?::|&)?\s*$", re.IGNORECASE)),
    ("certifications", re.compile(rf"^\s*(?:{_CERT_PATS})\s*(?::|&)?\s*$", re.IGNORECASE)),
    ("keywords", re.compile(rf"^\s*(?:{_KW_PATS})\s*(?::|&)?\s*$", re.IGNORECASE)),
    ("achievements", re.compile(rf"^\s*(?:{_ACHIEVE_PATS})\s*(?::|&)?\s*$", re.IGNORECASE)),
    ("activities", re.compile(rf"^\s*(?:{_ACT_PATS})\s*(?::|&)?\s*$", re.IGNORECASE)),
    ("publications", re.compile(rf"^\s*(?:{_PUB_PATS})\s*(?::|&)?\s*$", re.IGNORECASE)),
    ("interests", re.compile(rf"^\s*(?:{_INT_PATS})\s*(?::|&)?\s*$", re.IGNORECASE)),
]

OTHER_SECTION_TITLES = {
    "achievements": "Achievements",
    "activities": "Activities",
    "publications": "Publications",
    "interests": "Interests",
}


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
    skill_groups: dict[str, list[str]] = field(default_factory=dict)
    dropped_or_unmapped: list[str] = field(default_factory=list)

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
    # Hedges (~500, over ~50) are preserved
    return re.sub(r"\s+", " ", cleaned).strip()


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w+#.%-]+\b", str(text or "")))


def _is_section_header(line: str) -> Optional[str]:
    cleaned = _clean_line(line)
    if not cleaned:
        return None
    # Require at most 4 words
    if len(cleaned.split()) > 4:
        return None
    header_candidate = re.sub(r"[:|-]+$", "", cleaned).strip()
    for sec_name, pattern in SECTION_PATTERNS:
        if pattern.match(cleaned) or pattern.match(header_candidate):
            return sec_name
    return None


ROLE_KEYWORDS = {
    "intern", "engineer", "developer", "dev", "lead", "manager", "specialist",
    "analyst", "architect", "director", "scientist", "consultant",
    "designer", "researcher", "assistant", "associate", "officer",
    "administrator", "head", "vp", "president", "fellow", "programmer",
}
ORG_KEYWORDS = {
    "pvt", "ltd", "inc", "corp", "llc", "technologies", "analytics",
    "solutions", "systems", "labs", "company", "group", "services",
    "gmbh", "co.", "university", "institute", "foundation", "agency",
}


def _has_role_keyword(text: str) -> bool:
    if re.search(r"\blead\s+management\b", text, re.IGNORECASE):
        return False
    for kw in ROLE_KEYWORDS:
        if re.search(r"(?<![A-Za-z0-9])" + re.escape(kw) + r"(?![A-Za-z0-9])", text, re.IGNORECASE):
            return True
    return False


def _has_org_keyword(text: str) -> bool:
    for kw in ORG_KEYWORDS:
        if re.search(r"(?<![A-Za-z0-9])" + re.escape(kw) + r"(?![A-Za-z0-9])", text, re.IGNORECASE):
            return True
    return False


def _is_entry_header_candidate(line: str, in_bullets: bool = False) -> bool:
    cleaned = _clean_line(line)
    if not cleaned:
        return False
    if BULLET_PREFIX_RE.match(cleaned):
        return False
    if cleaned[0].islower():
        return False
    if in_bullets:
        if "|" in cleaned or "•" in cleaned:
            parts = [p.strip() for p in re.split(r"[\s]*[|•][\s]*", cleaned) if p.strip()]
            if len(parts) >= 2:
                return True
        if DATE_PATTERN.search(cleaned):
            return True
        ends_punct = cleaned.endswith((".", "!", "?", ";", ":", ","))
        if ends_punct and re.search(r"\b(?:inc|llc|ltd|pvt|corp|co|llp|gmbh)\.$", cleaned, re.IGNORECASE):
            ends_punct = False
        if (
            len(cleaned.split()) <= 6
            and not ends_punct
            and cleaned[0].isupper()
            and (_has_org_keyword(cleaned) or _has_role_keyword(cleaned) or cleaned.isupper() or cleaned.istitle())
        ):
            return True
        return False
    if "|" in cleaned or "•" in cleaned:
        return True
    if DATE_PATTERN.search(cleaned):
        return True
    if cleaned.endswith(":") and len(cleaned.split()) <= 18:
        return True
    ends_punct = cleaned.endswith((".", "!", "?", ";", ","))
    if ends_punct and re.search(r"\b(?:inc|llc|ltd|pvt|corp|co|llp|gmbh)\.$", cleaned, re.IGNORECASE):
        ends_punct = False
    if (
        len(cleaned.split()) <= 8
        and not ends_punct
        and (_has_org_keyword(cleaned) or _has_role_keyword(cleaned) or cleaned.isupper() or cleaned.istitle())
    ):
        first_word = cleaned.split()[0].lower()
        if first_word in ACTION_VERBS and not (_has_org_keyword(cleaned) or _has_role_keyword(cleaned)):
            return False
        return True
    return False


def _is_placeholder_title(text: str) -> bool:
    if not text:
        return True
    cleaned = _clean_line(text).strip()
    if not cleaned:
        return True
    if re.search(r"\bentry\s+\d+\b", cleaned, re.I):
        return True
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
        start, end = date_match.start(), date_match.end()
        if start > 0 and cleaned[start - 1] == "(" and end < len(cleaned) and cleaned[end] == ")":
            start -= 1
            end += 1
        cleaned_no_date = cleaned[:start] + cleaned[end:]
        cleaned_no_date = re.sub(r"\(\s*\)", "", cleaned_no_date).strip()
        cleaned_no_date = re.sub(r"[\s,:|–—-]+$", "", cleaned_no_date).strip()
    else:
        cleaned_no_date = re.sub(r"[\s,:|–—-]+$", "", cleaned).strip()

    parts = [p.strip() for p in re.split(r"[\s]*[|•][\s]*", cleaned_no_date) if p.strip()]
    if len(parts) >= 2:
        p0_role = _has_role_keyword(parts[0])
        p1_org = _has_org_keyword(parts[1])
        p0_org = _has_org_keyword(parts[0])
        p1_role = _has_role_keyword(parts[1])
        if (p0_role or p1_org) and not (p0_org and not p1_org):
            title = parts[0]
            org = parts[1]
        elif (p1_role or p0_org) and not (p0_role and not p1_org):
            org = parts[0]
            title = parts[1]
        else:
            org = parts[0]
            title = parts[1]
        loc = parts[2] if len(parts) > 2 else ""
        return org, title, dates, loc
    if len(parts) == 1:
        if "," in parts[0]:
            comma_parts = [p.strip() for p in parts[0].split(",") if p.strip()]
            if len(comma_parts) >= 2 and comma_parts[1].lower().rstrip(".") in {"inc", "llc", "ltd", "pvt", "corp", "co", "llp", "gmbh"}:
                return parts[0], "", dates, ""
            elif len(comma_parts) >= 2:
                pre = comma_parts[0]
                post = comma_parts[1]
                if _has_role_keyword(post):
                    return pre, post, dates, ""
                elif _has_role_keyword(pre):
                    return post, pre, dates, ""
                else:
                    return pre, "", dates, post

        subparts = [p.strip() for p in re.split(r"\s+-\s+", parts[0]) if p.strip()]
        if len(subparts) >= 2:
            p0_role = _has_role_keyword(subparts[0])
            p1_org = _has_org_keyword(subparts[1])
            p0_org = _has_org_keyword(subparts[0])
            p1_role = _has_role_keyword(subparts[1])
            if (p0_role or p1_org) and not (p0_org and not p1_org):
                return subparts[1], subparts[0], dates, ""
            elif (p1_role or p0_org) and not (p0_role and not p1_org):
                return subparts[0], subparts[1], dates, ""
            else:
                return subparts[0], subparts[1], dates, ""
        if _has_role_keyword(parts[0]):
            return "", parts[0], dates, ""
        return parts[0], "", dates, ""
    return "", "", dates, ""


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
_NEW_PROJECT_RE = re.compile(
    r"^(?:Created|Built|Developed|Designed|Implemented)\s+(?:a|an)\s+"
    r"(?P<name>[A-Z][\w&/\- ]{2,50}?\s(?:System|Application|App|Platform|Tool|Bot|Website|Portal|Tracker|Manager|Dashboard|Engine|Game))\b"
)


def _parse_markerless_entries(canonical_sec: str, sec_prefix: str, lines: list[str]) -> list[SourceEntry]:
    """Parse a section whose source has NO bullet markers (common in student resumes)."""
    logical: list[str] = []
    for line in lines:
        is_hdr = _is_entry_header_candidate(line)
        prev_is_hdr = _is_entry_header_candidate(logical[-1]) if logical else False
        if logical and not is_hdr and not prev_is_hdr and (not re.search(r"[.!?:]$", logical[-1]) or line[:1].islower()):
            logical[-1] = f"{logical[-1]} {line}".strip()
        else:
            logical.append(line)

    entries: list[SourceEntry] = []
    current: Optional[SourceEntry] = None

    def _new_entry(name: str, header_raw: str, title: str = "", dates: str = "", loc: str = "") -> SourceEntry:
        entry = SourceEntry(
            entry_id=f"{sec_prefix}_{len(entries) + 1:03d}",
            section=canonical_sec,
            title=title,
            organization=name,
            dates=dates,
            location=loc,
            header_raw=header_raw,
            bullets=[],
        )
        entries.append(entry)
        return entry

    for chunk in logical:
        if _is_comma_dump(chunk):
            continue
        if _is_entry_header_candidate(chunk, in_bullets=bool(current and current.bullets)):
            org, title, dates, loc = _parse_entry_header(chunk)
            if org or title or dates:
                if current and len(current.bullets) == 0:
                    is_date_only = bool(dates and not org and not title)
                    if is_date_only:
                        if not current.dates:
                            current.dates = dates
                        if not current.location and loc:
                            current.location = loc
                        continue
                    curr_has_org = bool(current.organization and not _is_placeholder_title(current.organization))
                    curr_has_title = bool(current.title and not _is_placeholder_title(current.title))
                    if not (curr_has_org and curr_has_title):
                        if not curr_has_org and org:
                            current.organization = org
                        if not curr_has_title:
                            if title:
                                current.title = title
                            elif org and curr_has_org:
                                current.title = org
                        if not current.dates and dates:
                            current.dates = dates
                        if not current.location and loc:
                            current.location = loc
                        continue
                current = _new_entry(name=org or title, header_raw=chunk, title=title if title != org else "", dates=dates, loc=loc)
                continue

        sentences = [p.strip() for p in _SENTENCE_SPLIT_RE.split(chunk) if p.strip()]
        for sent in sentences:
            if _is_comma_dump(sent):
                continue
            if sent.endswith(":") and _word_count(sent) <= 18:
                current = _new_entry(sent.rstrip(":").strip(), sent)
                continue
            if canonical_sec == "projects" and current is not None and current.bullets:
                m = _NEW_PROJECT_RE.match(sent)
                if m:
                    current = _new_entry(m.group("name").strip(), "")
            if current is None:
                current = _new_entry("", "")
            if _word_count(sent) < 5 and current.bullets:
                current.bullets[-1].original = f"{current.bullets[-1].original.rstrip()} {sent}".strip()
                continue
            b_idx = len(current.bullets) + 1
            current.bullets.append(
                SourceBullet(
                    source_id=f"{current.entry_id}_bullet_{b_idx:03d}",
                    section=canonical_sec,
                    entry_id=current.entry_id,
                    entry_name=current.organization or current.title,
                    original=sent,
                )
            )
    return [e for e in entries if e.bullets or e.organization or e.title or e.dates]


ACTION_VERBS = {
    "built", "developed", "created", "designed", "implemented", "managed", "led",
    "architected", "engineered", "improved", "optimized", "spearheaded", "reduced",
    "increased", "maintained", "automated", "orchestrated", "conducted", "supported",
    "collaborated", "authored", "deployed", "scaled", "delivered", "coordinated",
    "supervised", "directed", "initiated", "established", "streamlined", "analyzed",
    "programmed", "resolved", "executed", "formulated", "configured", "integrated",
}


def _is_comma_dump(text: str) -> bool:
    tokens = [t.strip() for t in text.split(",") if t.strip()]
    if len(tokens) < 6:
        return False
    if text.rstrip().endswith("."):
        return False
    text_words = set(re.findall(r"\b[A-Za-z]+\b", text.lower()))
    if any(verb in text_words for verb in ACTION_VERBS):
        return False
    return True


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

    # Markerless section (no bullet markers, no 'Name | Stack' headers): the marker-based wrap
    # merge below would fuse every line into one bullet, so segment by sentence instead.
    if preprocessed and not any(is_b for _, is_b in preprocessed) and not any("|" in l for l, _ in preprocessed):
        return _parse_markerless_entries(canonical_sec, sec_prefix, [l for l, _ in preprocessed])

    # Step 2: Parse into entries and merge line-wraps
    for line, is_bullet in preprocessed:
        has_bullets = bool(current_entry and current_entry.bullets)

        if not is_bullet and _is_entry_header_candidate(line, in_bullets=has_bullets):
            # Never treat section headers or placeholder strings as entry headers
            if _is_section_header(line) is not None or _is_placeholder_title(line):
                continue

            org, title, dates, loc = _parse_entry_header(line)

            # A1-a: Split headers merge when current_entry has 0 bullets
            if current_entry and len(current_entry.bullets) == 0:
                is_date_only = bool(dates and not org and not title)
                if is_date_only:
                    if not current_entry.dates:
                        current_entry.dates = dates
                    if not current_entry.location and loc:
                        current_entry.location = loc
                    continue

                curr_has_title = bool(current_entry.title and not _is_placeholder_title(current_entry.title))
                curr_has_org = bool(current_entry.organization and not _is_placeholder_title(current_entry.organization))

                if not (curr_has_org and curr_has_title):
                    merged = False
                    if not curr_has_org and org:
                        current_entry.organization = org
                        merged = True
                    if not curr_has_title:
                        if title:
                            current_entry.title = title
                            merged = True
                        elif org and curr_has_org:
                            current_entry.title = org
                            merged = True
                        elif "|" in line:
                            current_entry.title = line.strip()
                            merged = True
                    if not current_entry.dates and dates:
                        current_entry.dates = dates
                        merged = True
                    if not current_entry.location and loc:
                        current_entry.location = loc
                        merged = True
                    if merged:
                        continue

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
                    or dates
                )
                if not has_title:
                    continue
                idx = len(entries) + 1
                entry_id = f"{sec_prefix}_{idx:03d}"
                current_entry = SourceEntry(
                    entry_id=entry_id,
                    section=canonical_sec,
                    title=title,
                    organization=org,
                    dates=dates,
                    location=loc,
                    header_raw=line,
                    bullets=[],
                )
                entries.append(current_entry)
                continue

        # A4: Comma-dump check
        if _is_comma_dump(line):
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
        if not title_valid and not org_valid and not entry.dates:
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

        final_bullets = [
            b for b in cleaned_bullets
            if (_word_count(b.original) >= 3 or len(cleaned_bullets) == 1)
            and b.original.lower() != "continued"
        ]
        if not final_bullets and not (entry.organization or entry.title or entry.dates):
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


def _extract_source_skill_groups(resume_text: str) -> dict[str, list[str]]:
    """Extract grouped skills dictionary from raw resume text."""
    groups: dict[str, list[str]] = {}
    in_skills = False
    for line in resume_text.splitlines():
        trimmed = line.strip()
        if not trimmed:
            continue
        sec_header = _is_section_header(trimmed)
        if sec_header == "skills":
            in_skills = True
            parts = re.split(r"[:|]", trimmed, maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                for item in _split_preserving_parens(parts[1]):
                    s = re.sub(r"^[A-Za-z &/]+:\s*", "", item.strip().strip("-*•")).strip()
                    if s and any(c.isalnum() for c in s):
                        groups.setdefault("Skills", []).append(s)
            continue
        elif in_skills:
            if sec_header is not None:
                in_skills = False
                break
            parts = re.split(r"[:|]", trimmed, maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                cat = parts[0].strip().strip("-*•")
                for item in _split_preserving_parens(parts[1]):
                    s = item.strip().strip("-*•")
                    if s and any(c.isalnum() for c in s):
                        groups.setdefault(cat, []).append(s)
            else:
                for item in _split_preserving_parens(trimmed):
                    s = item.strip().strip("-*•")
                    if s and any(c.isalnum() for c in s):
                        groups.setdefault("Skills", []).append(s)
    return groups


def parse_source_resume(text: str) -> ResumeDocument:
    """Parses raw resume text into a normalized, structured ResumeDocument."""
    from services.professional_resume_pdf import _extract_source_contact_and_certs, is_education_text

    raw_text = str(text or "").strip()
    contact = _extract_source_contact_and_certs(raw_text)

    # First pass: find candidate name from top lines
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    candidate_name = ""
    for line in lines[:5]:
        is_name_cand = (
            not is_education_text(line)
            and "@" not in line
            and not re.search(r"linkedin|github", line, re.IGNORECASE)
            and not re.search(r"\d{6,}", line)
        )
        words = line.split()
        looks_like_name = 1 <= len(words) <= 4 and all(
            w.replace(".", "").replace("-", "").replace("'", "").isalpha() for w in words
        )
        if looks_like_name and is_name_cand and not _is_section_header(line):
            candidate_name = line
            break

    # Second pass: group lines by section
    sections: dict[str, list[str]] = {}
    current_sec = "header"
    dropped_or_unmapped: list[str] = []

    for idx, line in enumerate(lines):
        if line == candidate_name:
            continue
        sec_header = _is_section_header(line)
        if not sec_header and ":" in line:
            prefix = line.split(":", 1)[0].strip()
            if _is_section_header(prefix):
                sec_header = _is_section_header(prefix)
        if sec_header == "keywords":
            current_sec = "keywords"
            dropped_or_unmapped.append(f"Unmapped keywords section heading: {line}")
            continue
        elif sec_header:
            current_sec = sec_header
            sections.setdefault(current_sec, [])
            inline_content = re.sub(r"^[^:\-–—|]+[:\-–—|]\s*", "", line).strip()
            if inline_content and inline_content.lower() != line.lower() and not _is_section_header(inline_content):
                sections[current_sec].append(inline_content)
        else:
            if current_sec == "keywords":
                dropped_or_unmapped.append(f"Unmapped keyword line: {line}")
                continue

            words = line.split()
            is_unknown_heading = (
                current_sec not in {"experience", "projects", "education", "skills"}
                and len(words) <= 4
                and (line.istitle() or line.isupper())
                and not any(c.isdigit() for c in line)
                and not any(c in ".!?;," for c in line)
                and idx + 1 < len(lines)
            )
            if is_unknown_heading:
                current_sec = f"unmapped_{line.lower()}"
                dropped_or_unmapped.append(f"Unmapped unknown heading: {line}")
                continue
            if current_sec.startswith("unmapped_"):
                dropped_or_unmapped.append(f"Unmapped content: {line}")
                continue

            sections.setdefault(current_sec, []).append(line)

    # Extract summary
    summary_lines = sections.get("summary", [])
    summary_text = " ".join(summary_lines).strip()

    # Extract skills (A3-a: require at least one alphanumeric character)
    skills_lines = sections.get("skills", [])
    extracted_skills: list[str] = []
    for s_line in skills_lines:
        cleaned = re.sub(r"^(?:technical\s+|core\s+)?skills?\s*[:|-]\s*", "", s_line, flags=re.IGNORECASE)
        for item in _split_preserving_parens(cleaned):
            item_clean = re.sub(r"^[A-Za-z &/]+:\s*", "", item.strip().strip("-*•")).strip()
            if item_clean and any(c.isalnum() for c in item_clean) and item_clean not in extracted_skills:
                extracted_skills.append(item_clean)

    # Extract experience and project entries
    experience_entries = _parse_section_entries("experience", sections.get("experience", []))
    project_entries = _parse_section_entries("projects", sections.get("projects", []))

    # Extract education and certifications
    education_lines = [l for l in sections.get("education", []) if l]
    cert_lines = [l for l in sections.get("certifications", []) if l]
    if not cert_lines and contact.get("certifications"):
        cert_lines = list(contact.get("certifications") or [])

    other_sections = _collect_other_sections(sections)
    skill_groups = _extract_source_skill_groups(raw_text)

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
        other_sections=other_sections,
        skill_groups=skill_groups,
        dropped_or_unmapped=dropped_or_unmapped,
    )


def _collect_other_sections(sections: dict[str, list[str]]) -> list[dict[str, Any]]:
    """Copy sections the optimizer does not rewrite (achievements, activities, ...) verbatim.

    Items are split on bullet markers. Without markers, every non-wrapped line is its own item;
    a line is treated as a wrap of the previous one when the previous line does not end a
    sentence AND this line starts lowercase.
    """
    result: list[dict[str, Any]] = []
    for key, title in OTHER_SECTION_TITLES.items():
        lines = [_clean_line(l) for l in sections.get(key, [])]
        lines = [l for l in lines if l and _is_section_header(l) is None]
        if not lines:
            continue
        items: list[str] = []
        for line in lines:
            m = BULLET_PREFIX_RE.match(line)
            if m:
                body = m.group(1).strip()
                if body:
                    items.append(body)
                continue
            if items and (line[:1].islower() or not re.search(r"[.!?:]$", items[-1])) and line[:1].islower():
                items[-1] = f"{items[-1]} {line}"
            else:
                items.append(line)
        if items:
            result.append({"title": title, "items": items})
    return result


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
        "other_sections": [dict(sec) for sec in doc.other_sections],
    }


COMMON_TECH_CANONICAL = {
    "ci/cd": "CI/CD", "xgboost": "XGBoost", "sql": "SQL", "pandas": "Pandas", "numpy": "NumPy",
    "pytorch": "PyTorch", "scikit-learn": "scikit-learn", "sklearn": "scikit-learn", "fastapi": "FastAPI",
    "docker": "Docker", "git": "Git", "mlflow": "MLflow", "aws": "AWS", "linux": "Linux",
    "c++": "C++", "python": "Python", "opencv": "OpenCV", "onnx": "ONNX", "bert": "BERT",
    "resnet": "ResNet", "resnet-50": "ResNet-50", "flask": "Flask",
    "hugging face transformers": "Hugging Face Transformers", "transformers": "Transformers",
    "feature engineering": "Feature Engineering", "model inference": "Model Inference",
    "kubernetes": "Kubernetes", "jenkins": "Jenkins", "spark": "Spark", "kafka": "Kafka",
}


def _extract_tech_tokens_from_doc(doc: ResumeDocument) -> list[str]:
    tokens: list[str] = []
    # From project stack lines (e.g. Project Name | Stack)
    for p in doc.projects:
        header = p.header_raw or ""
        if "|" in header:
            parts = header.split("|")
            stack_part = DATE_PATTERN.sub("", parts[1]).strip()
            for raw_item in _split_preserving_parens(stack_part):
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
        if doc and doc.skill_groups:
            optimized_skills = doc.skill_groups
        elif doc and doc.raw_text:
            optimized_skills = _extract_source_skill_groups(doc.raw_text)
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
        if doc and doc.skill_groups:
            source_group_order = list(doc.skill_groups.keys())
        elif doc and doc.raw_text:
            sg = _extract_source_skill_groups(doc.raw_text)
            if sg:
                source_group_order = list(sg.keys())

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
