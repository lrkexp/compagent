"""Download and parse RSS/Atom feeds using only the standard library."""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from html import unescape
from typing import List, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from .models import NewsItem, NewsSource

LOGGER = logging.getLogger(__name__)
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _TAG_RE.sub("", unescape(text or ""))


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1].lower()
    return tag.lower()


def _find_child_text(element: ET.Element, *names: str) -> str:
    targets = {name.lower() for name in names}
    for child in list(element):
        if _local_name(child.tag) in targets:
            if child.text and child.text.strip():
                return child.text.strip()
            href = child.attrib.get("href")
            if href:
                return href.strip()
    return ""


def _parse_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    value = value.strip()
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_rss(root: ET.Element) -> List[ET.Element]:
    channel = root.find("channel")
    if channel is None:
        return []
    return list(channel.findall("item"))


def _parse_atom(root: ET.Element) -> List[ET.Element]:
    entries = list(root.findall("{http://www.w3.org/2005/Atom}entry"))
    if entries:
        return entries
    return list(root.findall("entry"))


def _parse_feed_entries(data: bytes) -> List[ET.Element]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:  # pragma: no cover - depends on upstream formatting
        LOGGER.warning("Failed to parse feed XML: %s", exc)
        return []

    local = _local_name(root.tag)
    if local in {"rss", "rdf"}:
        return _parse_rss(root)
    if local == "feed":
        return _parse_atom(root)

    # Attempt to locate entries within wrapper elements.
    items = root.findall(".//item")
    if items:
        return list(items)
    return list(root.findall(".//{http://www.w3.org/2005/Atom}entry"))


def _extract_categories(element: ET.Element) -> List[str]:
    categories: List[str] = []
    for child in list(element):
        if _local_name(child.tag) in {"category", "subject", "tag"}:
            text = child.text or child.attrib.get("term")
            if text:
                categories.append(text.strip())
    return categories


def fetch_feed(source: NewsSource, timeout: int = 20, max_items: int | None = None) -> List[NewsItem]:
    """Fetch and parse a feed, returning normalized news items."""

    LOGGER.debug("Fetching feed %s", source.url)
    request = Request(source.url, headers={"User-Agent": "saas-compliance-intelligence/1.0"})
    request = Request(source.url, headers={"User-Agent": "clubessential-compliance-agent/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:  # type: ignore[call-arg]
            data = response.read()
    except URLError as exc:  # pragma: no cover - network failure path
        LOGGER.warning("Failed to fetch %s: %s", source.url, exc)
        return []

    entries = _parse_feed_entries(data)
    if max_items is not None:
        entries = entries[:max_items]

    items: List[NewsItem] = []
    for entry in entries:
        title = _strip_html(_find_child_text(entry, "title")) or "Untitled"
        link = _find_child_text(entry, "link", "id")
        summary = _strip_html(_find_child_text(entry, "summary", "description", "content"))
        published_raw = _find_child_text(entry, "published", "updated", "issued", "pubDate")
        published = _parse_datetime(published_raw)
        categories = _extract_categories(entry)
        items.append(
            NewsItem(
                source=source.name,
                title=title,
                link=link,
                summary=summary,
                published=published,
                raw_categories=tuple(categories),
            )
        )
    return items
