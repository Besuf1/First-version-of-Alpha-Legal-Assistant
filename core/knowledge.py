from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
STOP_WORDS = {
    "a", "about", "an", "and", "are", "as", "at", "be", "by", "can", "could",
    "do", "does", "for", "from", "how", "i", "in", "is", "it", "me", "my",
    "of", "on", "or", "our", "please", "that", "the", "their", "this", "to",
    "us", "we", "what", "when", "where", "which", "who", "with", "would", "you",
    "your",
}
SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf"}


@dataclass(frozen=True)
class KnowledgeChunk:
    id: str
    text: str
    title: str
    heading: str
    file: str
    url: str = ""

    def public_metadata(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "heading": self.heading,
            "file": self.file,
            "url": self.url,
        }


def normalize_token(token: str) -> str:
    """Apply conservative English singular normalization; leave other scripts unchanged."""
    if not token.isascii() or len(token) <= 3:
        return token
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("es") and len(token) > 4 and not token.endswith(("sses", "uses")):
        return token[:-1]  # services -> service; provides -> provide
    if token.endswith("s") and len(token) > 4 and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    return [
        normalize_token(token)
        for token in TOKEN_RE.findall(text.lower())
        if len(token) > 1 and token not in STOP_WORDS
    ]


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    metadata: dict[str, str] = {}
    if not text.startswith("---\n"):
        return metadata, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return metadata, text
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip().lower()] = value.strip().strip('"\'')
    return metadata, text[end + 5 :]


def split_markdown(text: str, max_chars: int = 1500, overlap_chars: int = 180) -> list[tuple[str, str]]:
    """Split text into heading-aware chunks without requiring a vector database."""
    sections: list[tuple[str, list[str]]] = []
    current_heading = "Overview"
    current_lines: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if current_lines:
                sections.append((current_heading, current_lines))
            current_heading = stripped.lstrip("#").strip() or "Overview"
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_heading, current_lines))

    chunks: list[tuple[str, str]] = []
    for heading, lines in sections:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", "\n".join(lines)) if p.strip()]
        buffer = ""
        for paragraph in paragraphs:
            candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
            if len(candidate) <= max_chars:
                buffer = candidate
                continue
            if buffer:
                chunks.append((heading, buffer))
            if len(paragraph) <= max_chars:
                buffer = paragraph
            else:
                start = 0
                while start < len(paragraph):
                    end = min(start + max_chars, len(paragraph))
                    piece = paragraph[start:end].strip()
                    if piece:
                        chunks.append((heading, piece))
                    if end == len(paragraph):
                        break
                    start = max(end - overlap_chars, start + 1)
                buffer = ""
        if buffer:
            chunks.append((heading, buffer))
    return chunks


def read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF support requires pypdf. Install requirements.txt.") from exc
    reader = PdfReader(str(path))
    pages = []
    for index, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(f"# Page {index + 1}\n\n{page_text}")
    return "\n\n".join(pages)


class KnowledgeBase:
    def __init__(self, chunks: Iterable[KnowledgeChunk]):
        self.chunks = list(chunks)
        self._tokens = [tokenize(f"{c.title} {c.heading} {c.text}") for c in self.chunks]
        self._term_frequencies = [Counter(tokens) for tokens in self._tokens]
        self._lengths = [len(tokens) for tokens in self._tokens]
        self._average_length = sum(self._lengths) / max(len(self._lengths), 1)
        document_frequency: Counter[str] = Counter()
        for tokens in self._tokens:
            document_frequency.update(set(tokens))
        self._document_frequency = document_frequency

    @property
    def source_count(self) -> int:
        return len({chunk.file for chunk in self.chunks})

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    @classmethod
    def from_directory(cls, directory: Path) -> "KnowledgeBase":
        chunks: list[KnowledgeChunk] = []
        if not directory.exists():
            return cls([])
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            raw_text = read_pdf(path) if path.suffix.lower() == ".pdf" else path.read_text(encoding="utf-8")
            metadata, body = parse_front_matter(raw_text)
            title = metadata.get("title") or path.stem.replace("_", " ").title()
            url = metadata.get("source_url", "")
            for index, (heading, text) in enumerate(split_markdown(body)):
                if not text.strip():
                    continue
                chunks.append(
                    KnowledgeChunk(
                        id=f"{path.stem}-{index + 1}",
                        text=text.strip(),
                        title=title,
                        heading=heading,
                        file=path.name,
                        url=url,
                    )
                )
        return cls(chunks)

    def search(self, query: str, limit: int = 4, minimum_score: float = 0.55) -> list[tuple[KnowledgeChunk, float]]:
        """Return BM25-ranked chunks. It is fast, local, and has no embedding cost."""
        query_terms = tokenize(query)
        if not query_terms or not self.chunks:
            return []

        number_of_documents = len(self.chunks)
        k1, b = 1.5, 0.72
        scored: list[tuple[KnowledgeChunk, float]] = []
        normalized_query = " ".join(query_terms)

        for chunk, frequencies, length in zip(self.chunks, self._term_frequencies, self._lengths):
            score = 0.0
            for term in query_terms:
                frequency = frequencies.get(term, 0)
                if not frequency:
                    continue
                document_frequency = self._document_frequency.get(term, 0)
                inverse_document_frequency = math.log(
                    1 + (number_of_documents - document_frequency + 0.5) / (document_frequency + 0.5)
                )
                denominator = frequency + k1 * (
                    1 - b + b * length / max(self._average_length, 1)
                )
                score += inverse_document_frequency * (frequency * (k1 + 1)) / denominator

            haystack = f"{chunk.title} {chunk.heading} {chunk.text}".lower()
            if normalized_query and normalized_query in " ".join(tokenize(haystack)):
                score += 1.0
            matched_unique = len(set(query_terms) & set(frequencies))
            if matched_unique >= 2:
                score += min(0.6, matched_unique * 0.12)
            if score >= minimum_score:
                scored.append((chunk, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]
