"""Report building utilities for the compliance news agent."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from textwrap import fill
from typing import Dict, Iterable, List

from .models import NewsItem, TopicsConfig


def _format_datetime(value: datetime | None) -> str:
    if not value:
        return "Unknown publication date"
    return value.strftime("%Y-%m-%d %H:%M %Z") or value.isoformat(timespec="minutes")


def _format_keyword_hits(item: NewsItem, topics: TopicsConfig) -> str:
    parts: list[str] = []
    keyword_hits = item.keyword_hits or {}
    for cat_key, mapping in keyword_hits.items():
        for key, matches in mapping.items():
            if not matches:
                continue
            if cat_key == "verticals":
                label = topics.verticals.get(key).label if key in topics.verticals else key
            else:
                label = topics.compliance.get(key).label if key in topics.compliance else key
            deduped = ", ".join(sorted(set(matches)))
            parts.append(f"{label}: {deduped}")
    return "; ".join(parts)


def _format_item(item: NewsItem, topics: TopicsConfig) -> str:
    vertical_labels: list[str] = []
    for key in item.vertical_matches:
        cluster = topics.verticals.get(key) if hasattr(topics.verticals, 'get') else None
        vertical_labels.append(cluster.label if cluster else key)
    compliance_labels: list[str] = []
    for key in item.compliance_matches:
        cluster = topics.compliance.get(key) if hasattr(topics.compliance, 'get') else None
        compliance_labels.append(cluster.label if cluster else key)

    header = f"**{item.title}** ({item.source}, {_format_datetime(item.published)})"
    details = [
        f"Vertical focus: {', '.join(vertical_labels) if vertical_labels else 'Unclassified'}",
        f"Compliance lens: {', '.join(compliance_labels) if compliance_labels else 'Unclassified'}",
    ]
    if item.summary:
        details.append("Summary: " + fill(item.summary, width=98))
    keyword_hits = _format_keyword_hits(item, topics)
    if keyword_hits:
        details.append(f"Keywords flagged: {keyword_hits}")
    return "- " + "\n  - ".join([header] + details)


def build_markdown_report(items: Iterable[NewsItem], topics: TopicsConfig, generated_at: datetime) -> str:
    items_list = sorted(items, key=lambda item: (item.score(), item.published or datetime.min), reverse=True)
    total_items = len(items_list)
    sources = sorted({item.source for item in items_list})

    lines: list[str] = []
    lines.append(f"# Compliance Intelligence Briefing — {generated_at.date().isoformat()}")
    lines.append("")
    lines.append("## Snapshot")
    lines.append(f"- Relevant items: {total_items}")
    lines.append(f"- Sources scanned: {', '.join(sources) if sources else 'None'}")
    lines.append("")

    if not items_list:
        lines.append("No new items matched the configured criteria.")
        return "\n".join(lines)

    grouped: Dict[str, Dict[str, List[NewsItem]]] = defaultdict(lambda: defaultdict(list))
    for item in items_list:
        for vertical_key in item.vertical_matches or ("unclassified",):
            compliance_keys = item.compliance_matches or ["unclassified"]
            for compliance_key in compliance_keys:
                grouped[vertical_key][compliance_key].append(item)

    for vertical_key, compliance_map in grouped.items():
        cluster = topics.verticals.get(vertical_key) if hasattr(topics.verticals, 'get') else None
        vertical_label = cluster.label if cluster else vertical_key.replace('_', ' ').title()
        lines.append(f"## {vertical_label}")
        for compliance_key, items_for_compliance in compliance_map.items():
            compliance_cluster = topics.compliance.get(compliance_key) if hasattr(topics.compliance, 'get') else None
            compliance_label = compliance_cluster.label if compliance_cluster else compliance_key.replace('_', ' ').title()
            lines.append(f"### {compliance_label}")
            for item in items_for_compliance:
                lines.append(_format_item(item, topics))
            lines.append("")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _label_for_vertical(topics: TopicsConfig, key: str) -> str:
    cluster = topics.verticals.get(key) if hasattr(topics.verticals, "get") else None
    if cluster:
        return cluster.label
    if key == "unclassified":
        return "Unclassified"
    return key.replace("_", " ").title()


def _label_for_compliance(topics: TopicsConfig, key: str) -> str:
    cluster = topics.compliance.get(key) if hasattr(topics.compliance, "get") else None
    if cluster:
        return cluster.label
    if key == "unclassified":
        return "Unclassified"
    return key.replace("_", " ").title()


def _serialize_item(item: NewsItem, topics: TopicsConfig) -> Dict[str, object]:
    verticals = item.vertical_matches or ["unclassified"]
    compliance = item.compliance_matches or ["unclassified"]
    return {
        "title": item.title,
        "link": item.link,
        "source": item.source,
        "published": item.published.isoformat() if item.published else None,
        "summary": item.summary,
        "verticals": [
            {"key": key, "label": _label_for_vertical(topics, key)} for key in verticals
        ],
        "compliance": [
            {"key": key, "label": _label_for_compliance(topics, key)} for key in compliance
        ],
        "raw_categories": list(item.raw_categories),
        "keyword_hits": item.keyword_hits,
        "score": item.score(),
    }


def build_structured_payload(
    items: Iterable[NewsItem], topics: TopicsConfig, generated_at: datetime
) -> Dict[str, object]:
    """Return a JSON-serialisable payload used by the static site."""

    items_list = sorted(items, key=lambda item: (item.score(), item.published or datetime.min), reverse=True)
    sources = sorted({item.source for item in items_list})

    vertical_counter: Counter[str] = Counter()
    compliance_counter: Counter[str] = Counter()
    for item in items_list:
        for vertical_key in item.vertical_matches or ["unclassified"]:
            vertical_counter[vertical_key] += 1
        for compliance_key in item.compliance_matches or ["unclassified"]:
            compliance_counter[compliance_key] += 1

    grouped: Dict[str, Dict[str, List[NewsItem]]] = defaultdict(lambda: defaultdict(list))
    for item in items_list:
        vertical_keys = item.vertical_matches or ["unclassified"]
        compliance_keys = item.compliance_matches or ["unclassified"]
        for vertical_key in vertical_keys:
            for compliance_key in compliance_keys:
                grouped[vertical_key][compliance_key].append(item)

    sections: List[Dict[str, object]] = []
    for vertical_key in sorted(grouped.keys()):
        segments: List[Dict[str, object]] = []
        for compliance_key in sorted(grouped[vertical_key].keys()):
            segment_items = [
                _serialize_item(item, topics)
                for item in grouped[vertical_key][compliance_key]
            ]
            segments.append(
                {
                    "compliance": {
                        "key": compliance_key,
                        "label": _label_for_compliance(topics, compliance_key),
                    },
                    "items": segment_items,
                }
            )
        sections.append(
            {
                "vertical": {
                    "key": vertical_key,
                    "label": _label_for_vertical(topics, vertical_key),
                },
                "segments": segments,
            }
        )

    summary = {
        "total_items": len(items_list),
        "sources": sources,
        "vertical_counts": [
            {
                "key": key,
                "label": _label_for_vertical(topics, key),
                "count": count,
            }
            for key, count in vertical_counter.most_common()
        ],
        "compliance_counts": [
            {
                "key": key,
                "label": _label_for_compliance(topics, key),
                "count": count,
            }
            for key, count in compliance_counter.most_common()
        ],
    }

    return {
        "generated_at": generated_at.isoformat(),
        "summary": summary,
        "sections": sections,
    }
