import os
from typing import List
import httpx

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

async def search_google_books(q: str, max_results: int = 5) -> List[dict]:
    """Search Google Books and return simplified metadata list."""
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": q, "maxResults": max_results}
    if GOOGLE_API_KEY:
        params["key"] = GOOGLE_API_KEY

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()

    items = []
    for it in data.get("items", []):
        vi = it.get("volumeInfo", {})
        items.append({
            "title": vi.get("title"),
            "authors": vi.get("authors") or [],
            "description": vi.get("description"),
            "publishedDate": vi.get("publishedDate"),
            "thumbnail": vi.get("imageLinks", {}).get("thumbnail")
        })
    return items
