# =============================================================================
# backup.py — Automatic Spreadsheet Backup
# Invoice Management System
# =============================================================================

import os
import shutil
from pathlib import Path
from datetime import datetime
import database
import config


def _backup_folder() -> Path:
    """Returns the backup folder path, creating it if necessary."""
    folder = Path.cwd() / "data" / "Backups"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def create_backup(reason: str = "Manual") -> str | None:
    """
    Copies the Excel file to the backup folder with a timestamp.
    Returns the created backup path, or None if it fails.
    Also clears old backups, keeping only the most recent ones.
    """
    cfg = config.load()
    excel_file = cfg.get("excel_file", "")

    if not excel_file or not os.path.exists(excel_file):
        database.log("WARNING", "Backup skipped: Excel file not found.", excel_file)
        return None

    try:
        folder = _backup_folder()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        orig_name = Path(excel_file).stem
        backup_name = f"{orig_name}_backup_{ts}.xlsx"
        destination = folder / backup_name

        shutil.copy2(excel_file, destination)

        size_kb = destination.stat().st_size // 1024
        database.register_backup(str(destination), size_kb, reason)
        database.log("INFO", f"Backup created successfully: {backup_name}", reason)

        # Clear old backups
        _clean_old_backups(folder, cfg.get("max_backups", 10))

        return str(destination)

    except Exception as e:
        database.log("ERROR", f"Failed to create backup: {e}")
        return None


def _clean_old_backups(folder: Path, limit: int):
    """Removes oldest backups, keeping only the last `limit` files."""
    try:
        files = sorted(folder.glob("*_backup_*.xlsx"), key=lambda p: p.stat().st_mtime)
        while_remove = len(files) - limit
        for i in range(max(0, while_remove)):
            files[i].unlink()
    except Exception:
        pass


def restore_backup(backup_path: str) -> bool:
    """
    Copies a backup back to the original Excel file location.
    Returns True if successful.
    """
    cfg = config.load()
    excel_file = cfg.get("excel_file", "")

    if not excel_file:
        return False

    try:
        # Backup current file before restoring
        create_backup(reason="Auto before restore")
        shutil.copy2(backup_path, excel_file)
        database.log("INFO", f"Spreadsheet restored from: {Path(backup_path).name}")
        return True
    except Exception as e:
        database.log("ERROR", f"Failed to restore: {e}")
        return False


def list_available_backups() -> list:
    """Returns a list of available backups on disk (newest first)."""
    folder = _backup_folder()
    files = sorted(
        folder.glob("*_backup_*.xlsx"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    result = []
    for f in files:
        stat = f.stat()
        result.append({
            "name": f.name,
            "path": str(f),
            "size_kb": stat.st_size // 1024,
            "date": datetime.fromtimestamp(stat.st_mtime).strftime("%m/%d/%Y %H:%M")
        })
    return result