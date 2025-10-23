"""Command-line entry point for the compliance news agent."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from compliance_agent.agent import ComplianceNewsAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a compliance intelligence report.")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Optional path to write the Markdown report.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use bundled offline fixtures instead of making network requests.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of items to include in the report.",
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
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    parser.add_argument(
        "--no-print",
        action="store_true",
        help="Do not print the report to stdout.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    agent = ComplianceNewsAgent(config_dir=args.config_dir, sample_data_dir=args.sample_data_dir)
    report = agent.generate_report(output_path=args.output, offline=args.offline, limit=args.limit)

    if not args.no_print:
        print(report)


if __name__ == "__main__":
    main()
