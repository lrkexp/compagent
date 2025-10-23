"""Main orchestration logic for the compliance news agent."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from .config import load_agent_config
from .filters import apply_topic_matching, filter_relevant_items
from .models import AgentConfig, NewsItem
from .news_fetcher import fetch_feed
from .report import build_markdown_report

LOGGER = logging.getLogger(__name__)


class ComplianceNewsAgent:
    """Coordinator that loads configuration, collects news, and produces reports."""

    def __init__(
        self,
        config_dir: Path | str = Path("config"),
        sample_data_dir: Path | str = Path("sample_data"),
    ) -> None:
        self.config_dir = Path(config_dir)
        self.sample_data_dir = Path(sample_data_dir)
        self._config: AgentConfig | None = None

    @property
    def config(self) -> AgentConfig:
        if self._config is None:
            LOGGER.debug("Loading configuration from %s", self.config_dir)
            self._config = load_agent_config(self.config_dir)
        return self._config

    # ------------------------------------------------------------------
    # Data collection
    # ------------------------------------------------------------------
    def collect_news(self, offline: bool = False, limit: int | None = None) -> List[NewsItem]:
        """Fetch news from configured sources, optionally using offline fixtures."""

        raw_items: List[NewsItem] = []
        source_hint_map = {source.name: source.topics for source in self.config.sources}

        if offline:
            LOGGER.info("Loading offline fixture data from %s", self.sample_data_dir)
            raw_items.extend(self._load_offline_items())
        else:
            for source in self.config.sources:
                feed_items = fetch_feed(
                    source,
                    timeout=self.config.request_timeout,
                    max_items=self.config.max_items_per_source or None,
                )
                raw_items.extend(feed_items)

        LOGGER.info("Collected %s raw items", len(raw_items))
        for item in raw_items:
            hints = source_hint_map.get(item.source, ())
            apply_topic_matching(item, self.config.topics, hints)

        relevant = filter_relevant_items(raw_items)
        LOGGER.info("Identified %s relevant items", len(relevant))
        deduped = self._deduplicate(relevant)
        LOGGER.debug("After deduplication %s items remain", len(deduped))
        sorted_items = sorted(deduped, key=lambda item: (item.score(), item.published or datetime.min), reverse=True)
        if limit is not None:
            sorted_items = sorted_items[:limit]
        return sorted_items

    # ------------------------------------------------------------------
    def _load_offline_items(self) -> List[NewsItem]:
        fixture_path = self.sample_data_dir / "offline_articles.json"
        if not fixture_path.exists():
            raise FileNotFoundError(
                "Offline mode requested but fixture file 'offline_articles.json' was not found "
                f"in {self.sample_data_dir}"
            )
        with fixture_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        items: List[NewsItem] = []
        for entry in payload:
            published = None
            published_raw = entry.get("published")
            if published_raw:
                try:
                    published = datetime.fromisoformat(published_raw)
                except ValueError:
                    LOGGER.warning("Could not parse published date '%s'", published_raw)
            items.append(
                NewsItem(
                    source=entry.get("source", "Unknown"),
                    title=entry.get("title", "Untitled"),
                    link=entry.get("link", ""),
                    summary=entry.get("summary", ""),
                    published=published,
                    raw_categories=tuple(entry.get("categories", [])),
                )
            )
        return items

    # ------------------------------------------------------------------
    @staticmethod
    def _deduplicate(items: Iterable[NewsItem]) -> List[NewsItem]:
        seen: dict[str, NewsItem] = {}
        for item in items:
            key = item.link or item.title
            existing = seen.get(key)
            if not existing or item.score() > existing.score():
                seen[key] = item
        return list(seen.values())

    # ------------------------------------------------------------------
    def generate_report(
        self,
        output_path: Path | None = None,
        offline: bool = False,
        limit: int | None = None,
    ) -> str:
        items = self.collect_news(offline=offline, limit=limit)
        report = build_markdown_report(items, self.config.topics, datetime.now())
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report, encoding="utf-8")
            LOGGER.info("Report written to %s", output_path)
        return report
