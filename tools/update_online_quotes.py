"""Fetch, validate, and normalize the public online quote feed."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_URL = "https://zenquotes.io/api/quotes"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "online" / "quotes.json"
MAX_QUOTES = 50
MAX_TEXT_LENGTH = 383
MAX_AUTHOR_LENGTH = 95


def fetch_quotes() -> list[dict[str, str]]:
    """Return a normalized ZenQuotes batch or raise on invalid input."""
    request = Request(
        SOURCE_URL,
        headers={"Accept": "application/json", "User-Agent": "Motivation-Feed-Updater/1.0"},
    )
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"ZenQuotes returned HTTP {response.status}")
        payload = json.load(response)

    if not isinstance(payload, list):
        raise ValueError("ZenQuotes response is not an array")

    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        text = item.get("q")
        author = item.get("a")
        if not isinstance(text, str) or not isinstance(author, str):
            continue
        text, author = text.strip(), author.strip()
        if (
            not text
            or not author
            or len(text.encode("utf-8")) > MAX_TEXT_LENGTH
            or len(author.encode("utf-8")) > MAX_AUTHOR_LENGTH
            or text in seen
        ):
            continue
        normalized.append({"q": text, "a": author})
        seen.add(text)
        if len(normalized) == MAX_QUOTES:
            break

    if not normalized:
        raise ValueError("ZenQuotes response contained no usable quotes")
    return normalized


def main() -> None:
    """Write a deterministic UTF-8 JSON feed only after full validation."""
    quotes = fetch_quotes()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_PATH.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(quotes, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    temporary.replace(OUTPUT_PATH)
    print(f"Wrote {len(quotes)} validated quotes to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
