from pathlib import Path

from core.assistant import CONSULTATION_CTA, DISCLAIMER, NO_INFORMATION, append_required_footer
from core.knowledge import KnowledgeBase, parse_front_matter, tokenize


def test_front_matter_is_parsed():
    metadata, body = parse_front_matter(
        "---\ntitle: Test Source\nsource_url: https://example.com\n---\n# Heading\nBody"
    )
    assert metadata["title"] == "Test Source"
    assert metadata["source_url"] == "https://example.com"
    assert "Body" in body


def test_retriever_finds_relevant_source(tmp_path: Path):
    (tmp_path / "services.md").write_text(
        "---\ntitle: Services\n---\n# Startup law\nWe support founders with incorporation and founder agreements.",
        encoding="utf-8",
    )
    (tmp_path / "contact.md").write_text(
        "# Contact\nThe office is in Addis Ababa.", encoding="utf-8"
    )
    knowledge = KnowledgeBase.from_directory(tmp_path)
    results = knowledge.search("Do you support startup founders?")
    assert results
    assert results[0][0].title == "Services"
    assert "founders" in results[0][0].text


def test_retriever_declines_unmatched_question(tmp_path: Path):
    (tmp_path / "services.md").write_text(
        "# Services\nWe support business formation.", encoding="utf-8"
    )
    knowledge = KnowledgeBase.from_directory(tmp_path)
    assert knowledge.search("What is the weather on Mars?") == []


def test_footer_is_always_added_once():
    first = append_required_footer("A grounded response.")
    second = append_required_footer(first)
    assert first.count(DISCLAIMER) == 1
    assert first.count(CONSULTATION_CTA) == 1
    assert second.count(DISCLAIMER) == 1
    assert second.count(CONSULTATION_CTA) == 1


def test_empty_answer_uses_safe_fallback():
    answer = append_required_footer("")
    assert NO_INFORMATION in answer
    assert DISCLAIMER in answer


def test_unicode_tokenizer_supports_amharic():
    tokens = tokenize("የንግድ ሕግ መረጃ")
    assert "የንግድ" in tokens
