import os
import asyncio
from typing import List, Optional

import strawberry
from strawberry.file_uploads import Upload

from .providers.books import search_google_books
from .providers.llms import call_openai
from .utils.pdf_utils import extract_text_from_pdf_bytes

# --- Simple env config (no BaseSettings) ---
PROMPT_PREFIX = os.getenv("PROMPT_PREFIX", "You are an expert book reviewer.")
PROMPT_POSTFIX = os.getenv("PROMPT_POSTFIX", "Keep it concise and helpful.")
try:
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "8"))
except Exception:
    MAX_UPLOAD_MB = 8

# --- GraphQL types ---
@strawberry.type
class BookMeta:
    title: str
    authors: List[str]
    description: Optional[str]
    publishedDate: Optional[str]
    thumbnail: Optional[str]

@strawberry.type
class ReviewResult:
    review: str

@strawberry.input
class GenerateInput:
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    spoiler: bool = False
    model: Optional[str] = "openai"

# --- Resolvers ---
@strawberry.type
class Query:
    @strawberry.field
    async def searchBooks(self, query: str) -> List[BookMeta]:
        items = await search_google_books(query)
        return [
            BookMeta(
                title=i.get("title") or "",
                authors=i.get("authors") or [],
                description=i.get("description"),
                publishedDate=i.get("publishedDate"),
                thumbnail=i.get("thumbnail"),
            )
            for i in items
        ]

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def generateReview(self, input: GenerateInput, file: Optional[Upload] = None) -> ReviewResult:
        extracted_text = ""
        if file:
            data = await file.read()
            size_bytes = len(data)
            max_bytes = MAX_UPLOAD_MB * 1024 * 1024
            if size_bytes > max_bytes:
                raise ValueError(f"Upload too large. Max {MAX_UPLOAD_MB} MB")
            loop = asyncio.get_running_loop()
            extracted_text = await loop.run_in_executor(None, extract_text_from_pdf_bytes, data)

        meta = f"Title: {input.title or 'unknown'}\nAuthors: {', '.join(input.authors or [])}"
        spoiler_instr = "Include spoilers." if input.spoiler else "Avoid spoilers; add a clear spoiler warning if needed."
        prompt_parts = [
            PROMPT_PREFIX,
            meta,
            (f"Context from uploaded file:\n{extracted_text}" if extracted_text else ""),
            f"User request: Write a concise book review. {spoiler_instr}",
            PROMPT_POSTFIX,
        ]
        prompt = "\n\n".join([p for p in prompt_parts if p])

        review_text = await call_openai(prompt)

        return ReviewResult(review=review_text)

schema = strawberry.Schema(query=Query, mutation=Mutation)
