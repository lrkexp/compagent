"""Data structures used by the compliance news agent."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Mapping, Sequence


@dataclass(slots=True)
class NewsSource:
    """Represents a single RSS/Atom feed that should be queried."""

    name: str
    url: str
    topics: Sequence[str] = field(default_factory=tuple)


@dataclass(slots=True)
class KeywordSet:
    """Grouping of related keywords with a human readable label."""

    key: str
    label: str
    keywords: Sequence[str]


@dataclass(slots=True)
class NewsItem:
    """Normalized representation of a news item returned from a feed."""

    source: str
    title: str
    link: str
    published: datetime | None
    summary: str
    raw_categories: Sequence[str] = field(default_factory=tuple)
    vertical_matches: List[str] = field(default_factory=list)
    compliance_matches: List[str] = field(default_factory=list)
    keyword_hits: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)

    def score(self) -> int:
        """Return an integer score used for sorting relevance."""

        return len(self.vertical_matches) + len(self.compliance_matches)


@dataclass(slots=True)
class TopicsConfig:
    """Configuration containing keyword clusters."""

    verticals: Mapping[str, KeywordSet]
    compliance: Mapping[str, KeywordSet]


@dataclass(slots=True)
class AgentConfig:
    """Aggregated configuration for the compliance agent."""

    sources: List[NewsSource]
    topics: TopicsConfig
    request_timeout: int = 20
    max_items_per_source: int | None = None
