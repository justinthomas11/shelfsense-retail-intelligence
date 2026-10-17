"""
ShelfSense — Daily Ingestion Pipeline & Scheduler
==================================================
Extract → Validate → Deduplicate → Load, once a day via APScheduler.

Sources:
  scrape    live retailer scrapers (default)
  simulate  date-seeded simulated prices (offline / demo mode)

With --fallback-simulate, any retailer whose scraper returns nothing (e.g.
blocked or markup changed) is filled from the simulator, and the run log
says which retailers were simulated.

Usage:
    python pipeline/scheduler.py --once                       # run now, then exit
    python pipeline/scheduler.py --once --source simulate     # offline run
    python pipeline/scheduler.py --hour 6 --minute 30         # run daily at 06:30 IST
"""

import argparse
import logging
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_simulator.product_catalog import PRODUCT_CATALOG
from pipeline.simulated_source import simulate_day
from pipeline.validation import deduplicate, validate_records
from scrapers import SCRAPERS

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
logger = logging.getLogger("shelfsense.pipeline")


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_DIR / "pipeline.log", encoding="utf-8"),
        ],
    )


def extract(source, retailers, fallback_simulate, target_date):
    """Collect raw records from the chosen source. Returns (records, simulated_retailers)."""
    if source == "simulate":
        return simulate_day(target_date, retailers), list(retailers)

    records, simulated = [], []
    for name in retailers:
        scraped = SCRAPERS[name]().scrape_catalog(PRODUCT_CATALOG)
        logger.info("%s: scraped %d products", name, len(scraped))
        if not scraped and fallback_simulate:
            logger.warning("%s: no live data, falling back to simulator", name)
            scraped = simulate_day(target_date, [name])
            simulated.append(name)
        for r in scraped:
            r.price_date = target_date
        records.extend(scraped)
    return records, simulated


def run_pipeline(source="scrape", retailers=None, fallback_simulate=False, target_date=None):
    """Run one end-to-end ingestion. Returns a summary dict."""
    import psycopg2
    from config.db_config import DB_CONFIG
    from pipeline.loader import load_records

    target_date = target_date or date.today()
    retailers = retailers or list(SCRAPERS)
    logger.info("Pipeline start: source=%s date=%s retailers=%s", source, target_date, retailers)

    raw, simulated = extract(source, retailers, fallback_simulate, target_date)
    valid, rejected = validate_records(raw)
    for record, reason in rejected:
        logger.warning("Rejected %s @ %s: %s", record.product_name, record.retailer_name, reason)
    clean = deduplicate(valid)

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        loaded = load_records(conn, clean)
    finally:
        conn.close()

    summary = {
        "date": target_date.isoformat(),
        "extracted": len(raw),
        "rejected": len(rejected),
        "duplicates_removed": len(valid) - len(clean),
        "loaded": loaded,
        "simulated_retailers": simulated,
    }
    logger.info("Pipeline done: %s", summary)
    return summary


def safe_run(**kwargs):
    """Scheduler entry point: never let one failed run kill the scheduler."""
    try:
        run_pipeline(**kwargs)
    except Exception:
        logger.exception("Pipeline run failed")


def main():
    parser = argparse.ArgumentParser(description="ShelfSense daily ingestion pipeline")
    parser.add_argument("--source", choices=["scrape", "simulate"], default="scrape")
    parser.add_argument("--retailers", nargs="+", choices=list(SCRAPERS), default=list(SCRAPERS))
    parser.add_argument("--fallback-simulate", action="store_true",
                        help="simulate retailers whose scraper returns no data")
    parser.add_argument("--once", action="store_true", help="run immediately and exit")
    parser.add_argument("--hour", type=int, default=6)
    parser.add_argument("--minute", type=int, default=0)
    args = parser.parse_args()

    setup_logging()
    job_kwargs = {
        "source": args.source,
        "retailers": args.retailers,
        "fallback_simulate": args.fallback_simulate,
    }

    if args.once:
        run_pipeline(**job_kwargs)
        return

    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler = BlockingScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(
        safe_run,
        CronTrigger(hour=args.hour, minute=args.minute),
        kwargs=job_kwargs,
        id="daily_price_ingestion",
        misfire_grace_time=3600,
        coalesce=True,
    )
    logger.info("Scheduler started — daily run at %02d:%02d IST. Ctrl+C to stop.",
                args.hour, args.minute)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
