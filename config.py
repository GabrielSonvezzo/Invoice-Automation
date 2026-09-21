# =============================================================================
# config.py — Configuration Management
# Invoice Management System
# =============================================================================

import json
import os
from pathlib import Path

CONFIG_FILE = Path.cwd() / "data" / "config.json"

DEFAULT_CONFIG = {
    "xml_folder": "",
    "processed_folder": "",
    "excel_file": "",
    "batch_column": "W",
    "sheet_name": "Steel Plant",
    "default_supplier": 36003,
    "column_map": {
        "INVOICE": "C", 
        "ORDER": "D", 
        "SUPPLIER": "E", 
        "INV_DATE": "F",
        "WEIGHT": "G", 
        "PROD": "H", 
        "QUALITY": "I", 
        "THICKNESS": "J", 
        "WIDTH": "K",
        "TOTAL_VALUE": "L", 
        "TAX_ICMS": "M", 
        "TAX_IPI": "N",
        "DUE_DATE": "T", 
        "BILLING": "U", 
        "INV_VALUE": "V", 
        "NCM": "Z"
    },
    "max_backups": 10,
    "alert_due_days": 2,
    "outlook_folder": "Invoices",
    "outlook_active": False,
    "automation_active": False,
    "license_id": "",
    "theme": "dark"
}


def load() -> dict:
    """Loads config from disk. If not found, returns default."""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merges with default to capture any new keys
            config = {**DEFAULT_CONFIG, **data}
            config["column_map"] = {**DEFAULT_CONFIG["column_map"], **data.get("column_map", {})}
            return config
    except Exception:
        pass
    return dict(DEFAULT_CONFIG)


def save(config: dict) -> None:
    """Persists config to disk."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get(key: str, default=None):
    """Reads a value directly by its key name."""
    return load().get(key, default)