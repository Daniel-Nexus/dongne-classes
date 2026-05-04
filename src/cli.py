"""CLI 진입점.

사용:
  python -m src.cli crawl --source=all --db=data.db
  python -m src.cli crawl --source=splib,songpa_kids --db=data.db
  python -m src.cli search --db=data.db --age-min=4 --age-max=7 --status=recruiting,upcoming
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Iterable

from src import pipeline, storage
from src.sources.base import Source
from src.sources.songpa_gu_office import SongpaGuOfficeSource
from src.sources.songpa_kids import SongpaKidsSource
from src.sources.seoul_youth import SeoulYouthSource
from src.sources.splib import SplibSource


# 활성 소스 레지스트리. jamsil_youth 는 deprecated 라 제외.
SOURCE_FACTORIES = {
    "songpa_gu_office": lambda: SongpaGuOfficeSource(),
    "splib":            lambda: SplibSource(),
    "songpa_kids":      lambda: SongpaKidsSource(),
    "seoul_youth":      lambda: SeoulYouthSource(center_ids=(507, 538)),
}


def _resolve_sources(spec: str) -> list[Source]:
    if spec == "all":
        keys = list(SOURCE_FACTORIES.keys())
    else:
        keys = [s.strip() for s in spec.split(",") if s.strip()]
    out: list[Source] = []
    for k in keys:
        if k not in SOURCE_FACTORIES:
            raise SystemExit(f"unknown source: {k} (available: {sorted(SOURCE_FACTORIES)})")
        out.append(SOURCE_FACTORIES[k]())
    return out


def _cmd_crawl(args: argparse.Namespace) -> int:
    pipeline.configure_logging(level=logging.INFO)
    sources = _resolve_sources(args.source)
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    conn = storage.connect(args.db)
    results = pipeline.crawl_all(sources, conn)
    print()
    print(f"{'source':<20s} {'rows':>6s} {'elapsed':>8s}  status")
    for r in results:
        status = "ok" if r.ok else f"FAIL: {r.error}"
        print(f"{r.source_id:<20s} {r.rows:>6d} {r.elapsed_sec:>7.1f}s  {status}")
    return 0 if all(r.ok for r in results) else 1


def _cmd_search(args: argparse.Namespace) -> int:
    statuses: Iterable[str] | None
    if args.status:
        statuses = [s.strip() for s in args.status.split(",") if s.strip()]
    else:
        statuses = None
    conn = storage.connect(args.db)
    results = storage.search_kids(
        conn,
        age_min=args.age_min,
        age_max=args.age_max,
        statuses=statuses,
        limit=args.limit,
    )
    if not results:
        print("(no matches)")
        return 0
    for c in results:
        age = f"{c.target_age_min}-{c.target_age_max}세"
        fee = "무료" if c.fee_won == 0 else (f"{c.fee_won:,}원" if c.fee_won else "?")
        deadline = c.registration_end.strftime("%m/%d") if c.registration_end else "-"
        print(
            f"[{c.status.value:11s}] {c.facility_name:18s} | {c.title[:60]:<60s} "
            f"({age}, {fee}, ~{deadline})"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dongne-classes")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_crawl = sub.add_parser("crawl", help="크롤 → SQLite upsert")
    p_crawl.add_argument("--source", default="all",
                        help='all | comma-separated (e.g. "splib,songpa_kids")')
    p_crawl.add_argument("--db", default="data/dongne.db", help="SQLite path")
    p_crawl.set_defaults(func=_cmd_crawl)

    p_search = sub.add_parser("search", help="DB에서 강좌 검색")
    p_search.add_argument("--db", default="data/dongne.db")
    p_search.add_argument("--age-min", type=int, default=storage.DEFAULT_AGE_MIN)
    p_search.add_argument("--age-max", type=int, default=storage.DEFAULT_AGE_MAX)
    p_search.add_argument("--status", default=None,
                         help="comma-separated (recruiting,upcoming,...)")
    p_search.add_argument("--limit", type=int, default=50)
    p_search.set_defaults(func=_cmd_search)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
