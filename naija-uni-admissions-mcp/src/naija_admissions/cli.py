"""CLI entry point for ck-crawl - Campus Knowledge Crawler."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .models import InstitutionType
from .server import _run_scrape


def parse_institution_types(types_str: str | None) -> list[InstitutionType] | None:
    """Parse comma-separated institution types string into enum list."""
    if not types_str:
        return None
    types = [t.strip() for t in types_str.split(",") if t.strip()]
    try:
        return [InstitutionType(t) for t in types]
    except ValueError:
        print(f"Error: Invalid institution type. Valid types: {[t.value for t in InstitutionType]}", file=sys.stderr)
        sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="ck-crawl",
        description="Campus Knowledge Crawler - Scrape Nigerian tertiary institution admission data",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=50,
        help="Maximum number of institutions to crawl (default: 50)",
    )
    parser.add_argument(
        "--types",
        type=str,
        default=None,
        help="Comma-separated institution types (e.g., university,polytechnic,college_of_education)",
    )
    parser.add_argument(
        "--state",
        type=str,
        default=None,
        help="Filter by state (e.g., Lagos, FCT, Oyo)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous run state",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-crawl completed institutions",
    )
    parser.add_argument(
        "--sample-by-type",
        action="store_true",
        default=True,
        help="Sample institutions evenly across types (default: True)",
    )
    parser.add_argument(
        "--no-sample-by-type",
        action="store_false",
        dest="sample_by_type",
        help="Don't sample evenly across types",
    )
    parser.add_argument(
        "--failed",
        type=str,
        default=None,
        help="Comma-separated list of institution names to re-crawl (overrides type/state filters)",
    )
    parser.add_argument(
        "--crawl-run-id",
        type=str,
        default=None,
        help="UUID of the crawl_run record in Supabase (links crawl_logs to this run)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
        help="Number of institutions to scrape concurrently (default: 2)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override LOG_LEVEL env var (default: from env or INFO)",
    )
    parser.add_argument(
        "--log-format",
        type=str,
        default=None,
        choices=["console", "json"],
        help="Override LOG_FORMAT env var (default: from env or console)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Crawl + write local JSON/CSV/SQLite, but skip Supabase upserts (preview mode)",
    )
    parser.add_argument(
        "--discover-only",
        action="store_true",
        help="Run discovery connectors (NUC/NBTE/NCCE/NMCN) and write discovered_institutions.json, then exit",
    )
    parser.add_argument(
        "--discover-output",
        type=str,
        default=None,
        help="Path for discovered_institutions.json (default: data/discovered_institutions.json)",
    )

    args = parser.parse_args()

    if args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level
    if args.log_format:
        os.environ["LOG_FORMAT"] = args.log_format
    try:
        from . import utils as _utils
        _utils.structlog.configure(
            processors=[
                _utils.structlog.processors.TimeStamper(fmt="iso"),
                _utils.structlog.processors.add_log_level,
                _utils.structlog.processors.JSONRenderer() if os.environ.get("LOG_FORMAT", "console") == "json"
                else _utils.structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=_utils.structlog.make_filtering_bound_logger(
                getattr(__import__("logging"), os.environ.get("LOG_LEVEL", "INFO"), 0)
            ),
            cache_logger_on_first_use=True,
        )
    except Exception:
        pass

    institution_types = parse_institution_types(args.types)
    failed_institutions = [s.strip() for s in args.failed.split(",") if s.strip()] if args.failed else None

    try:
        if args.discover_only:
            from .discovery import run_discovery, write_discovery_output
            output_path = args.discover_output or str(
                __import__("pathlib").Path(__file__).resolve().parent.parent.parent / "data" / "discovered_institutions.json"
            )
            result = asyncio.run(run_discovery())
            write_discovery_output(result, output_path)
            print(json.dumps({"discovered": len(result), "output": output_path}, indent=2))
            return 0
        result = asyncio.run(_run_scrape(
            max_institutions=args.max,
            institution_types=[t.value for t in institution_types] if institution_types else None,
            resume_run=args.resume,
            sample_by_type=args.sample_by_type,
            force_overwrite=args.force,
            failed_institutions=failed_institutions,
            crawl_run_id=args.crawl_run_id,
            concurrency=args.concurrency,
            dry_run=args.dry_run,
        ))
        print(json.dumps(result, indent=2, default=str))
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())