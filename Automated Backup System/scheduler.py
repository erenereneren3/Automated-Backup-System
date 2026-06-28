"""
scheduler.py — Runs backups on a configurable schedule.

Usage:
    python scheduler.py              # Start the scheduler (runs forever)
    python scheduler.py --run-now    # Run one backup immediately, then start schedule

The interval is read from config.json → backup_interval_hours.
Press Ctrl+C to stop.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import schedule

from backup import run_backup, setup_logging

logger = logging.getLogger(__name__)


def load_interval(config_path: Path = Path("config.json")) -> float:
    """Read backup_interval_hours from the config file."""
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    return float(config.get("backup_interval_hours", 6))


def scheduled_job() -> None:
    """Wrapper called by the scheduler on each tick."""
    logger.info("Scheduler triggered — starting backup job.")
    success = run_backup(dry_run=False)
    if success:
        logger.info("Scheduled backup finished successfully.")
    else:
        logger.error("Scheduled backup finished with errors.")


def main() -> None:
    script_dir = Path(__file__).parent
    setup_logging(script_dir / "logs")

    parser = argparse.ArgumentParser(
        description="Automated Backup System — continuous scheduler"
    )
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Execute a backup immediately before starting the schedule.",
    )
    args = parser.parse_args()

    try:
        interval_hours = load_interval(script_dir / "config.json")
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logger.critical(f"Cannot read config: {e}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Automated Backup System — Scheduler started")
    logger.info(f"Backup interval: every {interval_hours} hour(s)")
    logger.info("Press Ctrl+C to stop.")
    logger.info("=" * 60)

    # Optionally run a backup immediately on startup
    if args.run_now:
        logger.info("--run-now flag set — executing immediate backup.")
        scheduled_job()

    # Register the recurring job
    schedule.every(interval_hours).hours.do(scheduled_job)
    logger.info(f"Next backup scheduled in {interval_hours} hour(s).")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds for pending jobs
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user (Ctrl+C).")
        sys.exit(0)


if __name__ == "__main__":
    main()
