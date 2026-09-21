# =============================================================================
# database.py — SQLite Database
# Invoice Management System
# =============================================================================

import sqlite3
from pathlib import Path
from datetime import datetime

DB_FILE = Path.cwd() / "data" / "invoices.db"

# Global variable to keep connection in memory
_PERSISTENT_CONNECTION = None

def _connect():
    global _PERSISTENT_CONNECTION
    
    # If connection does not exist, create it once
    if _PERSISTENT_CONNECTION is None:
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False prevents conflicts between GUI and Engine
        _PERSISTENT_CONNECTION = sqlite3.connect(str(DB_FILE), check_same_thread=False)
        _PERSISTENT_CONNECTION.row_factory = sqlite3.Row
        _PERSISTENT_CONNECTION.execute("PRAGMA journal_mode=WAL;")
        _PERSISTENT_CONNECTION.execute("PRAGMA synchronous=NORMAL;")
        
    return _PERSISTENT_CONNECTION


def initialize():
    """Creates tables if they don't exist."""
    with _connect() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS processed_invoices (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_num    TEXT NOT NULL,
                access_key     TEXT UNIQUE,
                supplier       TEXT,
                total_value    REAL,
                inv_date       TEXT,
                batch          TEXT,
                excel_row      INTEGER,
                processed_date TEXT DEFAULT (datetime('now','localtime')),
                xml_file       TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                date_time TEXT DEFAULT (datetime('now','localtime')),
                type      TEXT,   -- INFO, SUCCESS, ERROR, WARNING
                message   TEXT,
                detail    TEXT
            );

            CREATE TABLE IF NOT EXISTS backups (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                date_time TEXT DEFAULT (datetime('now','localtime')),
                file_path TEXT,
                size_kb   INTEGER,
                reason    TEXT
            );

            CREATE TABLE IF NOT EXISTS anomalies (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date_time   TEXT DEFAULT (datetime('now','localtime')),
                invoice_num TEXT,
                type        TEXT,
                description TEXT,
                reviewed    INTEGER DEFAULT 0
            );
        """)

# ─── Processed Invoices ───────────────────────────────────────────────────────

def invoice_already_processed(access_key: str) -> bool:
    with _connect() as con:
        row = con.execute(
            "SELECT 1 FROM processed_invoices WHERE access_key = ?", (access_key,)
        ).fetchone()
        return row is not None


def register_invoice(invoice_num, access_key, supplier, total_value,
                     inv_date, batch, excel_row, xml_file):
    with _connect() as con:
        con.execute("""
            INSERT OR IGNORE INTO processed_invoices
            (invoice_num, access_key, supplier, total_value, inv_date, batch, excel_row, xml_file)
            VALUES (?,?,?,?,?,?,?,?)
        """, (invoice_num, access_key, supplier, total_value, inv_date, batch, excel_row, xml_file))


def list_invoices(limit=200) -> list:
    with _connect() as con:
        rows = con.execute("""
            SELECT invoice_num, supplier, total_value, inv_date, batch,
                   processed_date, xml_file
            FROM processed_invoices
            ORDER BY processed_date DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


def total_invoices_month() -> int:
    with _connect() as con:
        row = con.execute("""
            SELECT COUNT(*) as total FROM processed_invoices
            WHERE strftime('%Y-%m', processed_date) = strftime('%Y-%m', 'now','localtime')
        """).fetchone()
        return row["total"] if row else 0


def total_value_month() -> float:
    with _connect() as con:
        row = con.execute("""
            SELECT COALESCE(SUM(total_value),0) as total_sum FROM processed_invoices
            WHERE strftime('%Y-%m', processed_date) = strftime('%Y-%m', 'now','localtime')
        """).fetchone()
        return row["total_sum"] if row else 0.0


def invoices_by_supplier() -> list:
    with _connect() as con:
        rows = con.execute("""
            SELECT supplier, COUNT(*) as qty, SUM(total_value) as total
            FROM processed_invoices
            GROUP BY supplier ORDER BY total DESC LIMIT 10
        """).fetchall()
        return [dict(r) for r in rows]


def monthly_history() -> list:
    with _connect() as con:
        rows = con.execute("""
            SELECT strftime('%m/%Y', processed_date) as month,
                   COUNT(*) as qty, SUM(total_value) as total
            FROM processed_invoices
            GROUP BY month ORDER BY processed_date DESC LIMIT 12
        """).fetchall()
        return [dict(r) for r in rows]


# ─── Audit Log ────────────────────────────────────────────────────────────────

def log(type: str, message: str, detail: str = ""):
    with _connect() as con:
        con.execute(
            "INSERT INTO audit_log (type, message, detail) VALUES (?,?,?)",
            (type, message, detail)
        )


def list_log(limit=500) -> list:
    with _connect() as con:
        rows = con.execute("""
            SELECT date_time, type, message, detail
            FROM audit_log ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


# ─── Backups ──────────────────────────────────────────────────────────────────

def register_backup(file_path: str, size_kb: int, reason: str):
    with _connect() as con:
        con.execute(
            "INSERT INTO backups (file_path, size_kb, reason) VALUES (?,?,?)",
            (file_path, size_kb, reason)
        )


def list_backups(limit=20) -> list:
    with _connect() as con:
        rows = con.execute("""
            SELECT date_time, file_path as path, size_kb, reason
            FROM backups ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


# ─── Anomalies ────────────────────────────────────────────────────────────────

def register_anomaly(invoice_num: str, type: str, description: str):
    with _connect() as con:
        con.execute(
            "INSERT INTO anomalies (invoice_num, type, description) VALUES (?,?,?)",
            (invoice_num, type, description)
        )


def pending_alerts() -> list:
    with _connect() as con:
        rows = con.execute("""
            SELECT id, date_time, invoice_num, type, description
            FROM anomalies WHERE reviewed = 0
            ORDER BY id DESC
        """).fetchall()
        return [dict(r) for r in rows]


def mark_alert_reviewed(anomaly_id: int):
    with _connect() as con:
        con.execute("UPDATE anomalies SET reviewed=1 WHERE id=?", (anomaly_id,))