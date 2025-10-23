"""Keyword matching and scoring logic for compliance news."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

from .models import KeywordSet, NewsItem, TopicsConfig


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _match_keywords(text: str, keyword_set: KeywordSet) -> list[str]:
    normalized_text = _normalize(text)
    matches: list[str] = []
    for keyword in keyword_set.keywords:
        if keyword.lower() in normalized_text:
            matches.append(keyword)
    return matches


def apply_topic_matching(
    item: NewsItem,
    topics: TopicsConfig,
    source_vertical_hints: Sequence[str] | None = None,
) -> NewsItem:
    """Populate the match fields on ``item`` based on configured topics."""

    item.vertical_matches = []
    item.compliance_matches = []
    search_space = " ".join(
        part for part in [item.title, item.summary, " ".join(item.raw_categories)] if part
    )

    keyword_hits: dict[str, dict[str, list[str]]] = defaultdict(dict)

    for key, cluster in topics.verticals.items():
        matches = _match_keywords(search_space, cluster)
        if matches:
            item.vertical_matches.append(key)
            keyword_hits.setdefault("verticals", {})[key] = matches

    if source_vertical_hints:
        for hint in source_vertical_hints:
            if hint in topics.verticals and hint not in item.vertical_matches:
                item.vertical_matches.append(hint)
                keyword_hits.setdefault("verticals", {})[hint] = []

    for key, cluster in topics.compliance.items():
        matches = _match_keywords(search_space, cluster)
        if matches:
            item.compliance_matches.append(key)
            keyword_hits.setdefault("compliance", {})[key] = matches

    item.keyword_hits = {cat: dict(matches) for cat, matches in keyword_hits.items()}
    return item


def filter_relevant_items(items: Iterable[NewsItem]) -> list[NewsItem]:
    """Return only items that have both a vertical and compliance match."""

    return [item for item in items if item.vertical_matches and item.compliance_matches]
