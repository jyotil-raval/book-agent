import io
import pdfplumber
from typing import Optional


def extract_text_from_pdf_bytes(b: bytes, char_limit: int = 4000) -> str:
    try:
        buf = io.BytesIO(b)
        text_pages = []
        with pdfplumber.open(buf) as pdf:
            for page in pdf.pages:
                pg_text = page.extract_text() or ""
                if pg_text:
                    text_pages.append(pg_text)
                if sum(len(p) for p in text_pages) > char_limit:
                    break
        full = "\n\n".join(text_pages)
        return full[:char_limit]
    except Exception:
        try:
            return b.decode("utf-8", errors="ignore")[:char_limit]
        except Exception:
            return ""
