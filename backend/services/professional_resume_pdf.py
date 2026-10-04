import base64
import html
import logging
import os
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from services.pdf_service import extract_text_from_pdf_base64

logger = logging.getLogger("careerlens.resume_pdf")

PAGE_WIDTH = 595.28
PAGE_HEIGHT = 841.89
MARGIN_X = 48
MARGIN_TOP = 42
MARGIN_BOTTOM = 42
CONTENT_WIDTH = PAGE_WIDTH - (MARGIN_X * 2)

TEXT_COLOR = (0.20, 0.20, 0.20)
MUTED_COLOR = (0.36, 0.36, 0.36)
BLUE_COLOR = (0.29, 0.56, 0.85)
NAVY_COLOR = (0.10, 0.17, 0.29)
LIGHT_BLUE_COLOR = (0.88, 0.93, 0.98)

ROLE_KEYWORDS = {
    "intern", "internship", "engineer", "developer", "lead", "architect", "manager",
    "consultant", "analyst", "specialist", "scientist", "administrator", "associate",
    "officer", "director", "head", "vp", "president", "fellow", "researcher",
    "assistant", "trainee", "founder", "co-founder", "instructor", "lecturer",
}
ORG_KEYWORDS = {
    "ltd", "inc", "pvt", "llc", "corp", "corporation", "technologies", "technology",
    "solutions", "analytics", "labs", "systems", "services", "company", "group",
    "ventures", "enterprises", "holdings", "university", "institute", "college",
}

PDF_REGULAR_FONT_NAME = "CareerLensResumeRegular"
PDF_BOLD_FONT_NAME = "CareerLensResumeBold"
BASE_REGULAR_FONT_NAME = "helv"
BASE_BOLD_FONT_NAME = "hebo"

REGULAR_FONT_CANDIDATES = [
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]
BOLD_FONT_CANDIDATES = [
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]

_FONT_FILES_BY_NAME: dict[str, str] = {}
_FONT_OBJECTS_BY_NAME: dict[str, Any] = {}


@dataclass
class GeneratedResumePdf:
    pdf_bytes: bytes
    visible_text: str
    extracted_text: str
    extraction_ratio: float
    emitted_headings: set[str] = field(default_factory=set)


def _clean_pdf_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("**", "")
    replacements = {
        "\u00a0": " ",
        "\u2013": "-",
        "\u2014": "-",
        "\u2010": "-",
        "\u2011": "-",
        "\u00ad": "-",
        "\u2212": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "-",
        "\u2605": "star",
        "\u2197": "",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = unicodedata.normalize("NFKD", text).encode("latin-1", "replace").decode("latin-1")
    text = re.sub(r"[^\S\r\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _clean_list(values: Any, limit: int = 50) -> list[str]:
    if not isinstance(values, list):
        return []
    cleaned: list[str] = []
    for value in values:
        text = _clean_pdf_text(value)
        if text:
            cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def _normalize_for_ratio(value: str) -> str:
    return re.sub(r"\s+", " ", _clean_pdf_text(value)).strip()


def _first_existing_font_path(*values: str | None) -> str | None:
    for value in values:
        if not value:
            continue
        path = Path(value)
        if path.is_file():
            return str(path)
    return None


def _resolve_font_files() -> tuple[str | None, str | None]:
    regular = _first_existing_font_path(
        os.getenv("CAREERLENS_RESUME_FONT_REGULAR"),
        *REGULAR_FONT_CANDIDATES,
    )
    bold = _first_existing_font_path(
        os.getenv("CAREERLENS_RESUME_FONT_BOLD"),
        *BOLD_FONT_CANDIDATES,
    )
    return regular, bold or regular


def _remember_font_file(fontname: str, fontfile: str | None):
    if fontfile:
        _FONT_FILES_BY_NAME[fontname] = fontfile


def _text_width(text: str, font: str, size: float) -> float:
    import fitz

    fontfile = _FONT_FILES_BY_NAME.get(font)
    if fontfile:
        try:
            font_obj = _FONT_OBJECTS_BY_NAME.get(font)
            if font_obj is None:
                font_obj = fitz.Font(fontfile=fontfile)
                _FONT_OBJECTS_BY_NAME[font] = font_obj
            return font_obj.text_length(text, fontsize=size)
        except Exception:
            pass

    try:
        return fitz.get_text_length(text, fontname=font, fontsize=size)
    except Exception:
        return len(text) * size * 0.55


def _split_long_word(word: str, max_width: float, font: str, size: float) -> list[str]:
    pieces: list[str] = []
    current = ""
    for char in word:
        candidate = f"{current}{char}"
        if current and _text_width(candidate, font, size) > max_width:
            pieces.append(current)
            current = char
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces


def _wrap_text(text: str, max_width: float, font: str, size: float) -> list[str]:
    paragraphs = _clean_pdf_text(text).splitlines() or [""]
    lines: list[str] = []
    for paragraph in paragraphs:
        # Pre-bind "CGPA <score>" or "GPA <score>" so they never split across lines
        bound_paragraph = re.sub(r"\b(CGPA|GPA)\s+([0-9.]+(?:/[0-9.]+)?)\b", r"\1__NBSP__\2", paragraph)
        words = bound_paragraph.strip().split()
        if not words:
            lines.append("")
            continue

        current = ""
        for word in words:
            word_parts = (
                _split_long_word(word, max_width, font, size)
                if _text_width(word.replace("__NBSP__", " "), font, size) > max_width
                else [word]
            )
            for part in word_parts:
                candidate = part if not current else f"{current} {part}"
                candidate_display = candidate.replace("__NBSP__", " ")
                if current and _text_width(candidate_display, font, size) > max_width:
                    lines.append(current.replace("__NBSP__", " "))
                    current = part
                else:
                    current = candidate
        if current:
            lines.append(current.replace("__NBSP__", " "))
    return lines


def _has_held_title(title: str, experience_entries: list, source_resume_text: str = "") -> bool:
    if not title:
        return False
    norm_target = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
    if not norm_target:
        return False

    for entry in (experience_entries or []):
        if isinstance(entry, dict):
            entry_title = re.sub(r"[^a-z0-9]+", " ", str(entry.get("title") or "").lower()).strip()
            entry_hdr = re.sub(r"[^a-z0-9]+", " ", str(entry.get("header_raw") or "").lower()).strip()
            if norm_target in entry_title or norm_target in entry_hdr:
                return True
            target_words = set(norm_target.split())
            if target_words and target_words.issubset(set(entry_title.split())):
                return True
        elif hasattr(entry, "title"):
            entry_title = re.sub(r"[^a-z0-9]+", " ", str(getattr(entry, "title", "") or "").lower()).strip()
            entry_hdr = re.sub(r"[^a-z0-9]+", " ", str(getattr(entry, "header_raw", "") or "").lower()).strip()
            if norm_target in entry_title or norm_target in entry_hdr:
                return True
            target_words = set(norm_target.split())
            if target_words and target_words.issubset(set(entry_title.split())):
                return True

    if source_resume_text:
        # Check source experience section directly
        exp_m = re.search(
            r"(?:experience|work\s+history|employment)\b[\s\S]*?(?=(?:education|projects?|skills|certifications?|$))",
            source_resume_text,
            re.IGNORECASE,
        )
        if exp_m and norm_target in re.sub(r"[^a-z0-9]+", " ", exp_m.group(0).lower()):
            return True

        try:
            from services.resume_structure import parse_source_resume
            doc = parse_source_resume(source_resume_text)
            for entry in doc.experience:
                entry_title = re.sub(r"[^a-z0-9]+", " ", str(entry.title or "").lower()).strip()
                entry_hdr = re.sub(r"[^a-z0-9]+", " ", str(entry.header_raw or "").lower()).strip()
                if norm_target in entry_title or norm_target in entry_hdr:
                    return True
                target_words = set(norm_target.split())
                if target_words and target_words.issubset(set(entry_title.split())):
                    return True
        except Exception:
            pass

    return False


class ResumePdfBuilder:
    def __init__(self):
        import fitz

        self.fitz = fitz
        self.doc = fitz.open()
        self.page = None
        self.y = MARGIN_TOP
        self.visible_lines: list[str] = []
        self.emitted_headings: set[str] = set()
        regular_font_file, bold_font_file = _resolve_font_files()
        if regular_font_file:
            self.regular_font = PDF_REGULAR_FONT_NAME
            self.regular_font_file = regular_font_file
            _remember_font_file(self.regular_font, regular_font_file)
        else:
            self.regular_font = BASE_REGULAR_FONT_NAME
            self.regular_font_file = None
            logger.warning("No embeddable regular resume font found; falling back to Base-14 Helvetica.")

        if bold_font_file:
            self.bold_font = PDF_BOLD_FONT_NAME
            self.bold_font_file = bold_font_file
            _remember_font_file(self.bold_font, bold_font_file)
        else:
            self.bold_font = BASE_BOLD_FONT_NAME
            self.bold_font_file = None
            logger.warning("No embeddable bold resume font found; falling back to Base-14 Helvetica-Bold.")

        self._new_page()

    def _new_page(self):
        self.page = self.doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        self.y = MARGIN_TOP
        self._register_fonts()

    def _register_fonts(self):
        for fontname, fontfile in (
            (self.regular_font, self.regular_font_file),
            (self.bold_font, self.bold_font_file),
        ):
            if fontfile:
                self.page.insert_font(fontname=fontname, fontfile=fontfile)

    def _font_name(self, font: str) -> str:
        if font in {BASE_REGULAR_FONT_NAME, PDF_REGULAR_FONT_NAME}:
            return self.regular_font
        if font in {BASE_BOLD_FONT_NAME, PDF_BOLD_FONT_NAME}:
            return self.bold_font
        return font

    def _ensure_space(self, height: float):
        if self.y + height <= PAGE_HEIGHT - MARGIN_BOTTOM:
            return
        self._new_page()

    def gap(self, height: float):
        self._ensure_space(height)
        self.y += height

    def line(
        self,
        text: str,
        *,
        font: str = "helv",
        size: float = 10,
        color=TEXT_COLOR,
        x: float = MARGIN_X,
        after: float = 0,
        record: bool = True,
    ):
        cleaned = _clean_pdf_text(text)
        if not cleaned:
            return
        font = self._font_name(font)
        line_height = size * 1.28
        self._ensure_space(line_height + after)
        self.page.insert_text(
            self.fitz.Point(x, self.y + size),
            cleaned,
            fontname=font,
            fontsize=size,
            color=color,
        )
        if record:
            self.visible_lines.append(cleaned)
        self.y += line_height + after

    def wrapped(
        self,
        text: str,
        *,
        font: str = "helv",
        size: float = 10,
        color=TEXT_COLOR,
        x: float = MARGIN_X,
        width: float = CONTENT_WIDTH,
        line_gap: float = 1.8,
        after: float = 0,
    ):
        font = self._font_name(font)
        for line in _wrap_text(text, width, font, size):
            if line:
                self.line(line, font=font, size=size, color=color, x=x, after=line_gap)
            else:
                self.gap(size * 0.8)
        if after:
            self.gap(after)

    def heading(self, text: str):
        clean_text = _clean_pdf_text(text).strip()
        norm_key = clean_text.upper()
        if not norm_key or norm_key in self.emitted_headings:
            return
        if re.search(r"\bentry\s+\d+\b", norm_key, re.I):
            return
        self.emitted_headings.add(norm_key)
        self.gap(9)
        self.line(norm_key, font="hebo", size=9.5, color=NAVY_COLOR, after=2)
        self.page.draw_line(
            self.fitz.Point(MARGIN_X, self.y),
            self.fitz.Point(MARGIN_X + 110, self.y),
            color=BLUE_COLOR,
            width=1,
        )
        self.gap(7)

    def bullet(self, text: str, *, size: float = 9.4):
        cleaned = _clean_pdf_text(text).lstrip("- ").strip()
        if not cleaned:
            return
        bullet_x = MARGIN_X + 8
        text_x = MARGIN_X + 20
        font = self.regular_font
        lines = _wrap_text(cleaned, CONTENT_WIDTH - 20, font, size)
        for index, line in enumerate(lines):
            self._ensure_space(size * 1.35)
            if index == 0:
                self.page.insert_text(
                    self.fitz.Point(bullet_x, self.y + size),
                    "-",
                    fontname=font,
                    fontsize=size,
                    color=BLUE_COLOR,
                )
                self.visible_lines.append(f"- {line}")
            else:
                self.visible_lines.append(line)
            self.page.insert_text(
                self.fitz.Point(text_x, self.y + size),
                line,
                fontname=font,
                fontsize=size,
                color=TEXT_COLOR,
            )
            self.y += size * 1.35
        self.gap(1.5)

    def finish(self) -> bytes:
        return self.doc.tobytes(deflate=True, garbage=4)

    def close(self):
        self.doc.close()


def _content_dict(content: Any) -> dict:
    if isinstance(content, dict):
        return content
    if hasattr(content, "model_dump"):
        return content.model_dump()
    if hasattr(content, "dict"):
        return content.dict()
    return {}


def _skill_groups(content: dict) -> list[dict[str, Any]]:
    raw_groups = content.get("skillGroups")
    groups: list[dict[str, Any]] = []
    if isinstance(raw_groups, list):
        for group in raw_groups:
            if not isinstance(group, dict):
                continue
            skills = _clean_list(group.get("skills"))
            if skills:
                groups.append({
                    "category": _clean_pdf_text(group.get("category")),
                    "skills": skills,
                })
    elif isinstance(content.get("skills"), dict):
        for cat, items in content["skills"].items():
            skills = _clean_list(items if isinstance(items, list) else [items])
            if skills:
                groups.append({
                    "category": _clean_pdf_text(cat),
                    "skills": skills,
                })
    elif isinstance((content.get("reconstructed_resume") or {}).get("skills"), dict):
        for cat, items in content["reconstructed_resume"]["skills"].items():
            skills = _clean_list(items if isinstance(items, list) else [items])
            if skills:
                groups.append({
                    "category": _clean_pdf_text(cat),
                    "skills": skills,
                })
    return groups


def _render_github_projects(builder: ResumePdfBuilder, projects: list[dict[str, Any]]):
    if not projects:
        return
    builder.heading("GitHub Projects")
    for project in projects[:3]:
        name = _clean_pdf_text(project.get("name") or "GitHub Project")
        language = _clean_pdf_text(project.get("language"))
        stars = int(project.get("stars") or 0)
        meta = [value for value in [language, f"{stars} stars" if stars else ""] if value]
        builder.line(name, font="hebo", size=9.5, color=NAVY_COLOR, after=0.5)
        if meta:
            builder.line(" | ".join(meta), size=8.2, color=MUTED_COLOR, after=1.5)
        bullet = _clean_pdf_text(project.get("bullet") or project.get("description"))
        if bullet:
            builder.bullet(bullet, size=9)


EDUCATION_TERMS = {
    "university", "institute", "college", "school", "academy", "polytechnic",
    "bachelor", "master", "degree", "b.tech", "m.tech", "btech", "mtech",
    "b.s.", "m.s.", "b.e.", "m.e.", "bca", "mca", "ph.d", "phd", "doctorate",
    "campus", "department",
}


def is_education_text(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(re.search(r"\b" + re.escape(term) + r"\b", lower) for term in EDUCATION_TERMS)


def _extract_source_contact_and_certs(source_text: str) -> dict[str, Any]:
    email = ""
    phone = ""
    linkedin = ""
    github = ""
    location = ""
    certifications = []

    if not source_text:
        return {
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "github": github,
            "location": location,
            "certifications": certifications,
        }

    email_match = re.search(r"[\w.-]+@[\w.-]+\.\w+", source_text)
    if email_match:
        email = email_match.group(0)

    # Robust phone matching: supports country codes (+91, +1, +44), spaces, hyphens, parentheses
    phone_pat = re.compile(
        r"(?:(?:Phone|Tel|Mobile|Mob|Cell)\s*[:#-]?\s*)?"
        r"((?:\+?\d{1,3}[\s.-]?)?\(?\d{2,5}\)?[\s.-]?\d{3,5}[\s.-]?\d{3,5}(?:[\s.-]?\d{1,4})?)",
        re.IGNORECASE,
    )
    for m in phone_pat.finditer(source_text):
        cand = (m.group(1) or m.group(0)).strip()
        digits = re.sub(r"\D", "", cand)
        if 10 <= len(digits) <= 15:
            if not re.match(r"^\d{4}\s*[-–]\s*\d{4}$", cand):
                phone = cand
                break

    linkedin_match = re.search(r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[^\s,|]+", source_text, re.IGNORECASE)
    if linkedin_match:
        linkedin = linkedin_match.group(0).rstrip(".,;")

    github_match = re.search(r"(?:https?:\/\/)?(?:www\.)?github\.com\/[^\s,|]+", source_text, re.IGNORECASE)
    if github_match:
        github = github_match.group(0).rstrip(".,;")

    # Location must be searched ONLY in header lines and NEVER match education institution/degree
    loc_pat = re.compile(r"\b([A-Z][a-zA-Z\s]+,\s*(?:[A-Z]{2}|[A-Za-z]+))\b")
    lines = [l.strip() for l in source_text.splitlines() if l.strip()]
    header_lines = []
    heading_re = re.compile(
        r"^(summary|professional\s+summary|experience|work\s+experience|education|projects|skills|certifications|achievements)\b",
        re.IGNORECASE,
    )
    for l in lines:
        if heading_re.match(l) or (len(l) <= 40 and l == l.upper() and any(c.isalpha() for c in l)):
            break
        header_lines.append(l)
        if len(header_lines) >= 8:
            break

    for line in header_lines:
        if is_education_text(line):
            continue
        for m in loc_pat.finditer(line):
            cand = m.group(1).strip()
            if not is_education_text(cand) and "@" not in cand and not re.search(r"github|linkedin", cand, re.IGNORECASE):
                location = cand
                break
        if location:
            break

    in_certs = False
    for line in source_text.splitlines():
        trimmed = line.strip()
        if not trimmed:
            continue
        lower = trimmed.lower()
        if re.match(r"^(?:certifications?|certificates?|licenses?)\b", lower):
            in_certs = True
            parts = re.split(r"[:|-]", trimmed, maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                for c in re.split(r"[,|;/•]", parts[1]):
                    c_clean = c.strip().strip("-*•")
                    if c_clean and len(c_clean) > 2:
                        certifications.append(c_clean)
            continue
        elif in_certs:
            if re.match(r"^(?:experience|education|projects|summary|skills|languages|awards|work)\b", lower):
                in_certs = False
            else:
                for sub in re.split(r"(?<=\S)\s*[•|;]\s*", trimmed):
                    c_clean = sub.lstrip("-*•").strip()
                    if c_clean and len(c_clean) > 2:
                        certifications.append(c_clean)

    return {
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
        "location": location,
        "certifications": certifications,
    }


def _visible_text_for_content(
    name: str,
    email: str,
    phone: str,
    content: dict,
    *,
    linkedin: str = "",
    github: str = "",
    location: str = "",
    certifications: list[str] | None = None,
) -> str:
    parts = [
        name,
        email,
        phone,
        location,
        linkedin,
        github,
        content.get("headline"),
        content.get("summary"),
        " ".join(content.get("skills") or []),
        " ".join(content.get("educationLines") or []),
        " ".join(certifications or []),
        " ".join(content.get("improvedBullets") or []),
        " ".join(content.get("newBullets") or []),
        " ".join(content.get("bullets") or []),
    ]
    exp_entries = (
        content.get("experience_entries")
        or content.get("experienceEntries")
        or (content.get("reconstructed_resume") or {}).get("experience")
        or content.get("experience")
        or []
    )
    for entry in exp_entries:
        if isinstance(entry, dict):
            parts.extend([
                entry.get("title", ""),
                entry.get("organization", ""),
                entry.get("dates", ""),
                entry.get("location", ""),
            ])
            parts.extend(entry.get("bullets") or [])

    proj_entries = (
        content.get("project_entries")
        or content.get("projectEntries")
        or (content.get("reconstructed_resume") or {}).get("projects")
        or content.get("projects")
        or []
    )
    for entry in proj_entries:
        if isinstance(entry, dict):
            parts.extend([
                entry.get("name", ""),
                entry.get("organization", ""),
                entry.get("technologies", ""),
                entry.get("dates", ""),
            ])
            parts.extend(entry.get("bullets") or [])

    for group in _skill_groups(content):
        parts.append(group.get("category", ""))
        parts.append(" ".join(group.get("skills") or []))
    return "\n".join(_clean_pdf_text(part) for part in parts if _clean_pdf_text(part))


def assert_pdf_text_extractable(
    pdf_bytes: bytes,
    *,
    source_resume_text: str = "",
    visible_text: str = "",
) -> tuple[str, float]:
    pdf_base64 = base64.b64encode(pdf_bytes).decode("ascii")
    extracted = extract_text_from_pdf_base64(pdf_base64)
    extracted = _clean_pdf_text(extracted)
    extracted_normalized = _normalize_for_ratio(extracted)
    source_normalized = _normalize_for_ratio(source_resume_text)
    visible_normalized = _normalize_for_ratio(visible_text)

    reference_len = max(len(source_normalized), len(visible_normalized), 1)
    ratio = len(extracted_normalized) / reference_len
    minimum_chars = max(60, min(500, int(reference_len * 0.05)))
    if len(extracted_normalized) < minimum_chars:
        raise ValueError(
            "Generated PDF failed text extraction regression check: "
            f"extracted {len(extracted_normalized)} chars from reference {reference_len}."
        )
    return extracted, ratio


def build_professional_resume_pdf(
    *,
    name: str,
    email: str = "",
    phone: str = "",
    linkedin: str = "",
    github: str = "",
    location: str = "",
    content: Any,
    source_resume_text: str = "",
) -> GeneratedResumePdf:
    content_data = _content_dict(content)
    parsed = _extract_source_contact_and_certs(source_resume_text)

    contact_dict = content_data.get("contact") if isinstance(content_data.get("contact"), dict) else {}
    cleaned_name = _clean_pdf_text(name or content_data.get("name") or parsed.get("name")) or "Your Name"
    cleaned_email = _clean_pdf_text(email or contact_dict.get("email") or parsed.get("email"))
    cleaned_phone = _clean_pdf_text(phone or contact_dict.get("phone") or parsed.get("phone"))
    cleaned_linkedin = _clean_pdf_text(linkedin or contact_dict.get("linkedin") or parsed.get("linkedin"))
    cleaned_github = _clean_pdf_text(github or contact_dict.get("github") or parsed.get("github"))
    raw_location = location or contact_dict.get("location") or parsed.get("location") or ""
    cleaned_location = "" if is_education_text(raw_location) else _clean_pdf_text(raw_location)

    if (not cleaned_linkedin or not cleaned_github) and content_data.get("contactLine"):
        cline = str(content_data["contactLine"])
        if not cleaned_linkedin:
            lm = re.search(r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[^\s,|]+", cline, re.I)
            if lm:
                cleaned_linkedin = lm.group(0)
        if not cleaned_github:
            gm = re.search(r"(?:https?:\/\/)?(?:www\.)?github\.com\/[^\s,|]+", cline, re.I)
            if gm:
                cleaned_github = gm.group(0)

    raw_certs = (
        content_data.get("certificationLines")
        or content_data.get("certifications")
        or parsed.get("certifications")
        or []
    )
    # Split any certification line containing multiple bullet items or separators so each is on its own line
    split_certs: list[str] = []
    for item in raw_certs:
        if isinstance(item, str):
            for sub in re.split(r"(?<=\S)\s*[•|;]\s*", item):
                c_clean = sub.lstrip("-*•").strip()
                if c_clean and len(c_clean) > 2:
                    split_certs.append(c_clean)
        elif item:
            split_certs.append(str(item))
    certifications = _clean_list(split_certs)

    headline = _clean_pdf_text(content_data.get("headline"))
    summary = _clean_pdf_text(content_data.get("summary")) or "No summary generated."
    skill_groups = _skill_groups(content_data)
    fallback_skills = _clean_list(content_data.get("skills"))
    education_lines = _clean_list(
        content_data.get("educationLines")
        or (content_data.get("reconstructed_resume") or {}).get("education")
        or content_data.get("education"),
        limit=6,
    )
    improved_bullets = _clean_list(content_data.get("improvedBullets"), limit=10)
    new_bullets = _clean_list(content_data.get("newBullets"), limit=8)
    fallback_bullets = _clean_list(content_data.get("bullets"), limit=10)
    experience_entries = (
        content_data.get("experience_entries")
        or content_data.get("experienceEntries")
        or (content_data.get("reconstructed_resume") or {}).get("experience")
        or content_data.get("experience")
        or []
    )
    project_entries = (
        content_data.get("project_entries")
        or content_data.get("projectEntries")
        or (content_data.get("reconstructed_resume") or {}).get("projects")
        or content_data.get("projects")
        or []
    )
    github_projects = [
        project for project in (content_data.get("githubProjects") or [])
        if isinstance(project, dict)
    ][:3]

    # FIX C: Remove the header title line unless the person has actually held that title
    if headline and experience_entries:
        if not _has_held_title(headline, experience_entries, source_resume_text):
            headline = ""

    builder = ResumePdfBuilder()
    try:
        builder.line(cleaned_name, font="hebo", size=21, color=(0.07, 0.07, 0.07), after=2)
        contact_items = [
            val for val in [cleaned_email, cleaned_phone, cleaned_location, cleaned_linkedin, cleaned_github]
            if val and not is_education_text(val)
        ]
        contact = " | ".join(contact_items)
        if headline:
            builder.line(headline, font="hebo", size=10.5, color=BLUE_COLOR, after=2)
        if contact:
            # FIX E: Stop clipping header contact line; wrap across lines cleanly on separators
            contact_font = builder.regular_font
            if _text_width(contact, contact_font, 9.2) > CONTENT_WIDTH:
                curr_line_items: list[str] = []
                for item in contact_items:
                    cand = " | ".join(curr_line_items + [item])
                    if curr_line_items and _text_width(cand, contact_font, 9.2) > CONTENT_WIDTH:
                        builder.line(" | ".join(curr_line_items), size=9.2, color=MUTED_COLOR, after=1.5)
                        curr_line_items = [item]
                    else:
                        curr_line_items.append(item)
                if curr_line_items:
                    builder.line(" | ".join(curr_line_items), size=9.2, color=MUTED_COLOR, after=7)
            else:
                builder.line(contact, size=9.2, color=MUTED_COLOR, after=7)
        else:
            builder.gap(4)

        builder.heading("Summary")
        builder.wrapped(summary, size=9.8, line_gap=1.5, after=2)

        if skill_groups or fallback_skills:
            builder.heading("Skills")
            if skill_groups:
                for group in skill_groups:
                    if group["category"]:
                        builder.line(group["category"], font="hebo", size=9, color=NAVY_COLOR, after=0.5)
                    builder.wrapped(", ".join(group["skills"]), size=9, line_gap=1, after=2)
            else:
                builder.wrapped(", ".join(fallback_skills), size=9, line_gap=1, after=2)

        if experience_entries:
            builder.heading("Experience")
            for entry in experience_entries:
                if not isinstance(entry, dict):
                    continue
                title = _clean_pdf_text(entry.get("title") or "")
                org = _clean_pdf_text(entry.get("organization") or "")
                dates = _clean_pdf_text(entry.get("dates") or "")
                loc = _clean_pdf_text(entry.get("location") or "")

                # FIX G: Keep source entry order (Role | Company)
                p0_role = any(kw in title.lower() for kw in ROLE_KEYWORDS)
                p1_org = any(kw in org.lower() for kw in ORG_KEYWORDS)
                p0_org = any(kw in title.lower() for kw in ORG_KEYWORDS)
                p1_role = any(kw in org.lower() for kw in ROLE_KEYWORDS)
                if (p1_role or p0_org) and not (p0_role and not p1_org):
                    title, org = org, title

                header_parts: list[str] = []
                seen_parts: set[str] = set()
                for p in [title, org, dates, loc]:
                    if not p:
                        continue
                    p_clean = _clean_pdf_text(p)
                    p_lower = p_clean.lower()
                    if p_lower in {"experience", "work experience", "projects", "key projects", "summary", "skills", "education", "certifications"}:
                        continue
                    if re.search(r"\bentry\s+\d+\b", p_lower, re.I):
                        continue
                    if p_lower not in seen_parts:
                        seen_parts.add(p_lower)
                        header_parts.append(p_clean)
                if header_parts:
                    builder.line(" | ".join(header_parts), font="hebo", size=9.8, color=NAVY_COLOR, after=2)
                for bullet in _clean_list(entry.get("bullets"), limit=8):
                    builder.bullet(bullet)
                builder.gap(2)
        elif improved_bullets or fallback_bullets:
            builder.heading("Experience")
            builder.line("Relevant Experience", font="hebo", size=10, color=NAVY_COLOR, after=3)
            for bullet in (improved_bullets or fallback_bullets):
                builder.bullet(bullet)

        if project_entries:
            builder.heading("Projects")
            for entry in project_entries:
                if not isinstance(entry, dict):
                    continue
                name = _clean_pdf_text(entry.get("name") or entry.get("title") or entry.get("organization") or "")
                tech = _clean_pdf_text(entry.get("technologies") or "")
                dates = _clean_pdf_text(entry.get("dates") or "")
                header_parts: list[str] = []
                seen_parts: set[str] = set()
                for p in [name, tech, dates]:
                    if not p:
                        continue
                    p_clean = _clean_pdf_text(p)
                    p_lower = p_clean.lower()
                    if p_lower in {"projects", "key projects", "technical projects", "experience", "education", "skills", "summary"}:
                        continue
                    if re.search(r"\bentry\s+\d+\b", p_lower, re.I):
                        continue
                    if p_lower not in seen_parts:
                        seen_parts.add(p_lower)
                        header_parts.append(p_clean)
                if header_parts:
                    builder.line(" | ".join(header_parts), font="hebo", size=9.8, color=NAVY_COLOR, after=2)
                for bullet in _clean_list(entry.get("bullets"), limit=6):
                    builder.bullet(bullet)
                builder.gap(2)
        elif new_bullets:
            builder.heading("Projects")
            builder.line("Projects & Additional Impact", font="hebo", size=10, color=NAVY_COLOR, after=3)
            for bullet in new_bullets:
                builder.bullet(bullet)

        _render_github_projects(builder, github_projects)

        if education_lines:
            builder.heading("Education")
            for line in education_lines:
                builder.wrapped(line, size=9.2, line_gap=1, after=1)

        if certifications:
            builder.heading("Certifications")
            for cert in certifications:
                builder.bullet(cert)

        pdf_bytes = builder.finish()
        visible_text = "\n".join(builder.visible_lines) or _visible_text_for_content(
            cleaned_name,
            cleaned_email,
            cleaned_phone,
            content_data,
            linkedin=cleaned_linkedin,
            github=cleaned_github,
            location=cleaned_location,
            certifications=certifications,
        )
    finally:
        builder.close()

    extracted_text, ratio = assert_pdf_text_extractable(
        pdf_bytes,
        source_resume_text=source_resume_text,
        visible_text=visible_text,
    )
    logger.info(
        "Generated extractable professional resume PDF: "
        f"{len(extracted_text)} extracted chars, ratio={ratio:.2f}"
    )
    return GeneratedResumePdf(
        pdf_bytes=pdf_bytes,
        visible_text=visible_text,
        extracted_text=extracted_text,
        extraction_ratio=ratio,
        emitted_headings=set(builder.emitted_headings),
    )
