"""Generate static site data for the compliance intelligence dashboard."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from compliance_agent.agent import ComplianceNewsAgent
from compliance_agent.report import build_markdown_report, build_structured_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect compliance news and render JSON/Markdown artifacts for the static site.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/data/latest.json"),
        help=(
            "Path where the structured JSON payload will be written."
            " Defaults to a local artifacts directory so generated files don't"
            " disturb tracked site assets."
        ),
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=Path("artifacts/latest.md"),
        help="Optional path for a Markdown snapshot (set to '-' to skip).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of items to include in the output.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use bundled fixture data instead of fetching live feeds.",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("config"),
        help="Directory containing configuration files.",
    )
    parser.add_argument(
        "--sample-data-dir",
        type=Path,
        default=Path("sample_data"),
        help="Directory containing offline sample articles.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging verbosity (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    agent = ComplianceNewsAgent(config_dir=args.config_dir, sample_data_dir=args.sample_data_dir)
    items = agent.collect_news(offline=args.offline, limit=args.limit)

    generated_at = datetime.now(timezone.utc)
    payload = build_structured_payload(items, agent.config.topics, generated_at)

    output_json = args.output_json
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    logging.info("Structured payload written to %s", output_json)

    if args.output_markdown != Path("-"):
        markdown = build_markdown_report(items, agent.config.topics, generated_at)
        output_md = args.output_markdown
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(markdown, encoding="utf-8")
        logging.info("Markdown report written to %s", output_md)


if __name__ == "__main__":
    main()
