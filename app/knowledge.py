from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from .config import settings


def load_knowledge_files() -> list[Path]:
    root = Path(settings.knowledge_dir)
    root.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    for ext in ("*.md", "*.txt"):
        files.extend(root.rglob(ext))
    return sorted(files)


def search_knowledge(query: str, limit: int = 5) -> List[Tuple[str, str]]:
    query_words = [w.strip().lower() for w in query.split() if w.strip()]
    scored: list[tuple[int, str, str]] = []
    for path in load_knowledge_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        lowered = text.lower()
        score = sum(lowered.count(word) for word in query_words)
        if score <= 0:
            continue
        snippet = make_snippet(text, query_words)
        scored.append((score, path.name, snippet))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(name, snippet) for _, name, snippet in scored[:limit]]


def make_snippet(text: str, query_words: list[str], radius: int = 220) -> str:
    lowered = text.lower()
    first_pos = min((lowered.find(w) for w in query_words if lowered.find(w) >= 0), default=0)
    start = max(0, first_pos - radius)
    end = min(len(text), first_pos + radius)
    snippet = text[start:end].replace("\n", " ").strip()
    return snippet
