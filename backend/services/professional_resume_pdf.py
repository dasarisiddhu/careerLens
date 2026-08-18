import base64
import html
import logging
import os
import re
import unicodedata
from dataclasses import dataclass
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
        words = paragraph.strip().split()
        if not words:
            lines.append("")
            continue

        current = ""
        for word in words:
            word_parts = (
                _split_long_word(word, max_width, font, size)
                if _text_width(word, font, size) > max_width
                else [word]
            )
            for part in word_parts:
                candidate = part if not current else f"{current} {part}"
                if current and _text_width(candidate, font, size) > max_width:
                    lines.append(current)
                    current = part
                else:
                    current = candidate
        if current:
            lines.append(current)
    return lines


class ResumePdfBuilder:
    def __init__(self):
        import fitz

        self.fitz = fitz
        self.doc = fitz.open()
        self.page = None
        self.y = MARGIN_TOP
        self.visible_lines: list[str] = []
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
        self.gap(9)
        self.line(text.upper(), font="hebo", size=9.5, color=NAVY_COLOR, after=2)
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
            skills = _clean_list(group.get("skills"), limit=12)
            if skills:
                groups.append({
                    "category": _clean_pdf_text(group.get("category")),
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


def _visible_text_for_content(name: str, email: str, phone: str, content: dict) -> str:
    parts = [
        name,
        email,
        phone,
        content.get("headline"),
        content.get("summary"),
        " ".join(content.get("skills") or []),
        " ".join(content.get("educationLines") or []),
        " ".join(content.get("improvedBullets") or []),
        " ".join(content.get("newBullets") or []),
        " ".join(content.get("bullets") or []),
    ]
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
    content: Any,
    source_resume_text: str = "",
) -> GeneratedResumePdf:
    content_data = _content_dict(content)
    cleaned_name = _clean_pdf_text(name) or "Your Name"
    cleaned_email = _clean_pdf_text(email)
    cleaned_phone = _clean_pdf_text(phone)
    headline = _clean_pdf_text(content_data.get("headline"))
    summary = _clean_pdf_text(content_data.get("summary")) or "No summary generated."
    skill_groups = _skill_groups(content_data)
    fallback_skills = _clean_list(content_data.get("skills"), limit=30)
    education_lines = _clean_list(content_data.get("educationLines"), limit=6)
    improved_bullets = _clean_list(content_data.get("improvedBullets"), limit=10)
    new_bullets = _clean_list(content_data.get("newBullets"), limit=8)
    fallback_bullets = _clean_list(content_data.get("bullets"), limit=10)
    github_projects = [
        project for project in (content_data.get("githubProjects") or [])
        if isinstance(project, dict)
    ][:3]

    builder = ResumePdfBuilder()
    try:
        builder.line(cleaned_name, font="hebo", size=21, color=(0.07, 0.07, 0.07), after=2)
        contact = " | ".join(value for value in [cleaned_email, cleaned_phone] if value)
        if headline:
            builder.line(headline, font="hebo", size=10.5, color=BLUE_COLOR, after=2)
        if contact:
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

        if improved_bullets or fallback_bullets:
            builder.heading("Experience")
            builder.line("Relevant Experience", font="hebo", size=10, color=NAVY_COLOR, after=3)
            for bullet in (improved_bullets or fallback_bullets):
                builder.bullet(bullet)

        if new_bullets:
            builder.heading("Projects")
            builder.line("Projects & Additional Impact", font="hebo", size=10, color=NAVY_COLOR, after=3)
            for bullet in new_bullets:
                builder.bullet(bullet)

        _render_github_projects(builder, github_projects)

        if education_lines:
            builder.heading("Education")
            for line in education_lines:
                builder.wrapped(line, size=9.2, line_gap=1, after=1)

        pdf_bytes = builder.finish()
        visible_text = "\n".join(builder.visible_lines) or _visible_text_for_content(
            cleaned_name,
            cleaned_email,
            cleaned_phone,
            content_data,
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
    )
