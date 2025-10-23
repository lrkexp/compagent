"""Configuration helpers for the compliance news agent."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .models import AgentConfig, KeywordSet, NewsSource, TopicsConfig


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Configuration file {path} must contain a JSON object at the top level.")
    return data


def _build_keyword_sets(raw: Dict[str, Any]) -> Dict[str, KeywordSet]:
    keyword_sets: Dict[str, KeywordSet] = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            raise ValueError(f"Keyword configuration for '{key}' must be an object.")
        label = value.get("label", key.replace("_", " ").title())
        keywords = value.get("keywords", [])
        if not isinstance(keywords, list):
            raise ValueError(f"Keywords for '{key}' must be provided as a list.")
        if any(not isinstance(item, str) for item in keywords):
            raise ValueError(f"All keywords for '{key}' must be strings.")
        cleaned = [item.strip() for item in keywords if item and item.strip()]
        unique_keywords = tuple(dict.fromkeys(cleaned))
        keyword_sets[key] = KeywordSet(key=key, label=label, keywords=unique_keywords)
    return keyword_sets


def load_topics_config(path: Path) -> TopicsConfig:
    raw = _load_json(path)
    verticals_raw = raw.get("verticals", {})
    compliance_raw = raw.get("compliance", {})
    if not isinstance(verticals_raw, dict) or not isinstance(compliance_raw, dict):
        raise ValueError("'verticals' and 'compliance' must be JSON objects.")
    return TopicsConfig(
        verticals=_build_keyword_sets(verticals_raw),
        compliance=_build_keyword_sets(compliance_raw),
    )


def load_sources_config(path: Path) -> list[NewsSource]:
    raw = _load_json(path)
    sources_raw = raw.get("sources", [])
    if not isinstance(sources_raw, list):
        raise ValueError("'sources' must be a list of source definitions.")
    sources: list[NewsSource] = []
    for entry in sources_raw:
        if not isinstance(entry, dict):
            raise ValueError("Each source definition must be a JSON object.")
        name = entry.get("name")
        url = entry.get("url")
        topics = entry.get("topics", [])
        if not name or not url:
            raise ValueError("Source definitions must include both 'name' and 'url'.")
        if not isinstance(topics, list):
            raise ValueError("'topics' must be a list when provided.")
        sources.append(NewsSource(name=name, url=url, topics=tuple(topics)))
    return sources


def load_agent_config(config_dir: Path) -> AgentConfig:
    topics = load_topics_config(config_dir / "topics.json")
    sources = load_sources_config(config_dir / "news_sources.json")
    agent_settings_path = config_dir / "agent.json"
    agent_settings = _load_json(agent_settings_path) if agent_settings_path.exists() else {}
    request_timeout = agent_settings.get("request_timeout", 20)
    max_items = agent_settings.get("max_items_per_source")
    return AgentConfig(
        sources=sources,
        topics=topics,
        request_timeout=request_timeout,
        max_items_per_source=max_items,
    )
