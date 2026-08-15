# Add this to your existing FastAPI scraper backend (same one serving /scrape/single, port 8002)
#
# Install: pip install pdfplumber
#
# In main.py:
#   from datasheet_summary import router as datasheet_router
#   app.include_router(datasheet_router)

import io
import re
import httpx
import pdfplumber
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class DatasheetRequest(BaseModel):
    datasheet_url: str


def extract_text_column_aware(page):
    """
    pdfplumber's default extract_text() reads words roughly top-to-bottom
    across the FULL page width, which interleaves left-column and
    right-column text on 2-column datasheets (very common for ST/TI/etc
    'Features' sections) — sentences end up chopped into fragments.

    This groups words by which half of the page they're in, sorts each
    half top-to-bottom, then concatenates left column fully, then right
    column — restoring readable sentence order for genuinely 2-column
    content. Falls back gracefully (just returns similar output) for
    normal single-column pages.
    """
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    if not words:
        return page.extract_text() or ""

    mid_x = page.width / 2
    left_words = [w for w in words if (w["x0"] + w["x1"]) / 2 < mid_x]
    right_words = [w for w in words if (w["x0"] + w["x1"]) / 2 >= mid_x]

    def words_to_text(word_list):
        lines = {}
        for w in word_list:
            key = round(w["top"] / 3) * 3  # bucket nearby y-positions into the same line
            lines.setdefault(key, []).append(w)
        text_lines = []
        for key in sorted(lines.keys()):
            row = sorted(lines[key], key=lambda w: w["x0"])
            text_lines.append(" ".join(w["text"] for w in row))
        return "\n".join(text_lines)

    return words_to_text(left_words) + "\n" + words_to_text(right_words)


def extract_description(text: str, max_chars: int = 400):
    """Extract the actual product description from a datasheet."""

    if not text:
        return None

    # Normalize PDF whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    description = None

    # 1. Try explicit Description section — take everything after the heading
    # up to the next recognizable section heading, OR up to max_chars.
    # Iterates ALL occurrences of "Description" because the word also shows
    # up as a Table-of-Contents entry (e.g. "1 Description ..... 9") — those
    # are skipped by checking for dot-leader patterns right after the match.
    for heading_match in re.finditer(r'\b(?:General\s+)?Description\b\s*[:\-]?\s*', text, re.IGNORECASE):
        remainder = text[heading_match.end():]
        if re.search(r'(?:\.\s*){4,}', remainder[:150]):  # dot-leaders (with or without spaces between dots) = still inside TOC block
            continue
        stop = re.search(
            r'\b(Applications?|Ordering\s+Information|Table\s+of\s+Contents|Pin\s*(?:out|\s*Description|Configuration)|Electrical\s+Characteristics|Absolute\s+Maximum)\b',
            remainder, re.IGNORECASE
        )
        candidate = (remainder[:stop.start()] if stop else remainder).strip()
        if len(candidate) > 30:  # sanity check — too short means we probably grabbed junk
            description = candidate
            break

    # 2. onsemi-style datasheet: title -> subtitle -> description -> Features
    if not description:
        match = re.search(
            r'(?:ESD Protection Diode\s+)?'
            r'(?:Micro[-−]Packaged Diodes for ESD Protection\s+)?'
            r'.*?'
            r'(?P<desc>(?:The\s+.*?))'
            r'(?=\s+Features\b)',
            text,
            re.IGNORECASE
        )
        if match:
            description = match.group("desc").strip()

    # 3. Generic fallback — neither specific pattern matched (very common:
    # datasheet formatting/section headers vary a lot by manufacturer).
    # Better to show *something* than nothing — take the start of the
    # cleaned page text. Cut it off at "Features" if that word appears,
    # so we don't drag feature-list/package-list junk into the prose.
    if not description:
        print("[datasheet-summary] no Description/onsemi pattern matched — using generic fallback")
        cut = re.search(r'\b(Features|Applications)\b', text, re.IGNORECASE)
        description = text[:cut.start()] if cut else text

    # Clean PDF artifacts
    description = re.sub(r'\s+', ' ', description).strip()
    if not description:
        return None

    # Limit length
    if len(description) > max_chars:
        description = description[:max_chars]
        last_period = description.rfind(".")

        if last_period > 100:
            description = description[:last_period + 1]
        else:
            description = description.rsplit(" ", 1)[0] + "..."

    return description or None


def extract_features(raw_text: str, max_items: int = 10):
    """
    Pulls the 'Features' / 'Key Specifications' bullet block that almost
    every datasheet has on page 1 — this is what makes the summary look
    like a spec sheet instead of a wall of prose.

    Expects raw_text to already be in reading order (see
    extract_text_column_aware for 2-column pages).
    """
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

    start_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^(key\s+)?(features|specifications|highlights)\b", line, re.IGNORECASE):
            start_idx = i + 1
            break
    if start_idx is None:
        return []

    # Stop at the next major section heading
    stop_pattern = re.compile(
        r"^(description|applications|ordering|pin\s*out|pin\s*configuration|absolute\s+maximum|contents|table\s+of)",
        re.IGNORECASE,
    )

    bullet_pattern = re.compile(r"^[•\-\*●▪○■–]\s*")
    items = []
    for line in lines[start_idx:]:
        if stop_pattern.match(line):
            break

        has_bullet_marker = bool(re.match(r"^[•\*●▪○■]|^[-–]\s", line))
        cleaned = bullet_pattern.sub("", line).strip()

        if not cleaned or cleaned.isdigit() or len(cleaned) > 160:
            continue

        letters = re.sub(r"[^A-Za-z]", "", cleaned)
        is_heading_like = letters and letters.isupper() and len(cleaned) <= 40

        if has_bullet_marker and not is_heading_like:
            if len(items) >= max_items:
                break
            items.append(cleaned)
        elif items and not is_heading_like:
            # No bullet marker on this line — it's almost certainly a
            # wrapped continuation of the previous bullet (common when a
            # feature sentence runs onto 2-3 lines in the PDF).
            items[-1] = f"{items[-1]} {cleaned}"
        # else: heading-like or nothing to attach to yet — skip

    return items


@router.post("/datasheet/summarize")
async def summarize_datasheet(req: DatasheetRequest):
    """
    Downloads the datasheet PDF, extracts text from the first 2 pages, and
    returns a short description PLUS a features/specs bullet list — so the
    frontend can render it as a spec sheet rather than a paragraph.
    Fails silently (returns nulls) — this is a nice-to-have.
    """
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(req.datasheet_url)
            print(f"[datasheet-summary] fetch status={resp.status_code} content-type={resp.headers.get('content-type')} size={len(resp.content)} bytes for {req.datasheet_url}")
            resp.raise_for_status()
            pdf_bytes = resp.content

        if not pdf_bytes.startswith(b"%PDF"):
            print(f"[datasheet-summary] response is not a real PDF (doesn't start with %PDF magic bytes) — likely got an HTML error/consent page instead, for {req.datasheet_url}")
            return {"summary": None, "features": []}

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = pdf.pages[:2]
            # Simple text first — used to find WHICH page has "Features"
            simple_chunks = [p.extract_text() or "" for p in pages]

            features_page_idx = None
            for i, chunk in enumerate(simple_chunks):
                if re.search(r"^(key\s+)?(features|specifications|highlights)\b", chunk, re.IGNORECASE | re.MULTILINE):
                    features_page_idx = i
                    break

            if features_page_idx is not None:
                # Re-extract just that page column-aware, so 2-column feature
                # lists don't get sentence-interleaved
                features_text = extract_text_column_aware(pages[features_page_idx])
            else:
                features_text = "\n".join(simple_chunks)

        raw_text = "\n".join(simple_chunks)

        # Strip out Table-of-Contents lines entirely (any line containing a
        # dot-leader run like ". . . . . 9") before description extraction —
        # this guarantees TOC text can never leak into the description,
        # regardless of which extraction path ends up being used.
        toc_line_pattern = re.compile(r'(?:\.\s*){4,}')
        filtered_lines = [ln for ln in raw_text.split("\n") if not toc_line_pattern.search(ln)]
        cleaned_text = re.sub(r"\s+", " ", "\n".join(filtered_lines)).strip()

        description = extract_description(cleaned_text)
        features = extract_features(features_text)

        if not description and not features:
            print(f"[datasheet-summary] nothing extracted at all for {req.datasheet_url} — PDF text may be image-based (scanned) or extraction failed silently")

        return {"summary": description, "features": features}

    except Exception as e:
        import traceback
        print(f"[datasheet-summary] failed for {req.datasheet_url}: {type(e).__name__}: {e}")
        traceback.print_exc()
        return {"summary": None, "features": []}