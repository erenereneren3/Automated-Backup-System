"""
backup.py — Core backup logic.

Usage:
    python backup.py              # Run a single backup
    python backup.py --dry-run    # Simulate without copying files
"""

import argparse
import json
import logging
import os
import shutil
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

import colorlog

from notifier import TelegramNotifier

# ---------------------------------------------------------------------------
# Logging setup — colorised console + plain rotating file
# ---------------------------------------------------------------------------

def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "backup.log"

    # Coloured formatter for the console
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s]%(reset)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG":    "cyan",
            "INFO":     "green",
            "WARNING":  "yellow",
            "ERROR":    "red",
            "CRITICAL": "bold_red",
        },
    )

    # Plain formatter for the log file
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(file_formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(console_handler)
    root.addHandler(file_handler)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(config_path: Path = Path("config.json")) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    # Basic validation
    required_keys = ["source_folders", "destination_folder", "keep_last_n_backups"]
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Missing required config key: '{key}'")

    return config


# ---------------------------------------------------------------------------
# Backup helpers
# ---------------------------------------------------------------------------

def _count_files(folders: list[str]) -> int:
    """Count total files across all source folders."""
    total = 0
    for folder in folders:
        p = Path(folder)
        if p.exists():
            total += sum(1 for _ in p.rglob("*") if _.is_file())
    return total


def create_zip_backup(
    source_folders: list[str],
    destination: Path,
    backup_name: str,
    dry_run: bool = False,
) -> tuple[Path, int]:
    """
    Zip all source folders into a single archive at destination/backup_name.
    Returns (archive_path, file_count).
    """
    archive_path = destination / backup_name
    file_count = 0

    if dry_run:
        # Simulate: just count what would be backed up
        for folder in source_folders:
            p = Path(folder)
            if not p.exists():
                logger.warning(f"[DRY-RUN] Source folder not found, skipping: {folder}")
                continue
            for file in p.rglob("*"):
                if file.is_file():
                    logger.debug(f"[DRY-RUN] Would add: {file}")
                    file_count += 1
        logger.info(f"[DRY-RUN] Would create archive: {archive_path}")
        return archive_path, file_count

    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder in source_folders:
            p = Path(folder)
            if not p.exists():
                logger.warning(f"Source folder not found, skipping: {folder}")
                continue

            logger.info(f"Compressing: {folder}")
            # Preserve folder name as the top-level entry in the archive
            base_name = p.name
            for file in p.rglob("*"):
                if file.is_file():
                    arcname = base_name / file.relative_to(p)
                    zf.write(file, arcname)
                    file_count += 1

    return archive_path, file_count


def purge_old_backups(destination: Path, keep_n: int, dry_run: bool = False) -> None:
    """Delete oldest backups so that only keep_n archives remain."""
    archives = sorted(
        destination.glob("backup_*.zip"),
        key=lambda f: f.stat().st_mtime,
    )

    to_delete = archives[:-keep_n] if keep_n > 0 else archives

    for old_archive in to_delete:
        if dry_run:
            logger.info(f"[DRY-RUN] Would delete old backup: {old_archive.name}")
        else:
            old_archive.unlink()
            logger.info(f"Deleted old backup: {old_archive.name}")


def human_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_backup(dry_run: bool = False) -> bool:
    """
    Execute a full backup cycle.
    Returns True on success, False on failure.
    """
    script_dir = Path(__file__).parent
    setup_logging(script_dir / "logs")

    logger.info("=" * 60)
    logger.info("Automated Backup System — starting backup")
    if dry_run:
        logger.info("*** DRY-RUN MODE — no files will be written ***")
    logger.info("=" * 60)

    start_time = time.time()

    try:
        config = load_config(script_dir / "config.json")
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        logger.critical(f"Failed to load config: {e}")
        return False

    # Telegram notifier (silently disabled if credentials are absent)
    tg_cfg = config.get("telegram", {})
    notifier = TelegramNotifier(
        bot_token=tg_cfg.get("bot_token", ""),
        chat_id=tg_cfg.get("chat_id", ""),
    )

    source_folders: list[str] = config["source_folders"]
    destination = Path(config["destination_folder"])
    keep_n: int = int(config["keep_last_n_backups"])

    # Build a timestamped archive name
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    backup_name = f"backup_{timestamp}.zip"

    logger.info(f"Sources   : {source_folders}")
    logger.info(f"Destination: {destination}")
    logger.info(f"Archive   : {backup_name}")
    logger.info(f"Keep last : {keep_n} backups")

    try:
        archive_path, file_count = create_zip_backup(
            source_folders, destination, backup_name, dry_run=dry_run
        )

        # Archive size (0 in dry-run since nothing was created)
        size_bytes = archive_path.stat().st_size if archive_path.exists() else 0
        duration = time.time() - start_time

        # Purge backups that exceed the keep_n limit
        if not dry_run:
            purge_old_backups(destination, keep_n, dry_run=dry_run)
        else:
            purge_old_backups(destination, keep_n, dry_run=True)

        # ── Summary report ──────────────────────────────────────────────────
        logger.info("-" * 60)
        logger.info("BACKUP SUMMARY")
        logger.info(f"  Archive  : {backup_name}")
        logger.info(f"  Files    : {file_count}")
        logger.info(f"  Size     : {human_size(size_bytes)}")
        logger.info(f"  Duration : {duration:.1f}s")
        logger.info("-" * 60)

        if not dry_run:
            notifier.notify_success(
                backup_name=backup_name,
                size_mb=size_bytes / (1024 * 1024),
                duration_sec=duration,
                file_count=file_count,
            )

        logger.info("Backup completed successfully.")
        return True

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Backup failed after {duration:.1f}s: {e}", exc_info=True)
        notifier.notify_failure(str(e))
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Automated Backup System — single backup run"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the backup without writing any files.",
    )
    args = parser.parse_args()

    success = run_backup(dry_run=args.dry_run)
    sys.exit(0 if success else 1)
