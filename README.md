# Invoice Automation – NF-e to Spreadsheet

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-red)

A desktop application that automates the posting of Brazilian electronic invoices (NF-e) into a production planning spreadsheet.

It reads invoice XML files, matches each invoice to the correct spreadsheet row by **batch number**, and writes the invoice data into that row **while preserving all existing cell formatting**, replacing hours of manual data entry with a single click.

![Dashboard](screenshots/dashboard.png)

---

## Why this project exists

In an industrial planning (PPCP) environment, every incoming invoice had to be typed manually into a shared production spreadsheet: invoice number, weight, dimensions, taxes, due date and more. With hundreds of invoices per cycle, this was slow and error-prone.

This tool was built to solve that real problem: it processes **800+ invoices in a few minutes**, with backup, duplicate detection and a full audit trail.

---

## Features

- **Automatic XML parsing** of NF-e files (invoice, order, weight, product, quality, dimensions, taxes, due date, NCM)
- **Batch-number matching** between the XML and the spreadsheet
- **Formatting-safe writing**: data is inserted without breaking the spreadsheet's existing styles
- **Duplicate detection** by NF-e access key
- **Automatic timestamped backup** before every run, with rotation and restore
- **Audit log** of every operation, stored in SQLite
- **Single save per run**, regardless of batch size
- **Graphical interface** with dashboard, settings, logs and backup management

---

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Interface | CustomTkinter |
| XML parsing | xmltodict |
| Spreadsheet | openpyxl |
| Database | SQLite |
| Packaging | PyInstaller (optional) |

---

## Screenshots

| Dashboard | Process Invoices |
|---|---|
| ![Dashboard](screenshots/dashboard.png) | ![Process](screenshots/process.png) |

| Settings | Audit Log |
|---|---|
| ![Settings](screenshots/settings.png) | ![Audit Log](screenshots/audit_log.png) |

---

## Getting started

### Requirements

- Python 3.10 or higher

### Installation

```bash
pip install customtkinter openpyxl xmltodict Pillow
```

### Running

Graphical interface:

```bash
python gui.py
```

Processing engine only (no interface, logs to console):

```bash
python invoice_bot.py
```

---

## How to use

**First run**

1. Start the application with `python gui.py`.
2. Open the **Settings** tab.
3. Set the pending XML folder, processed XML folder, spreadsheet path, worksheet name and batch column.
4. Click **Save Settings**.

**Posting invoices**

1. Place the XML files in the pending folder.
2. Open the **Process Invoices** tab.
3. Click **PROCESS INVOICES IN SPREADSHEET**.

**What the engine does on each run**

1. Creates a timestamped backup of the spreadsheet.
2. Skips invoices already recorded in the database.
3. Reads the batch number from each XML and finds the matching row.
4. Writes the invoice data into that row, preserving formatting.
5. Saves the workbook once, after all invoices are processed.
6. Moves the processed XMLs to the processed folder.
7. Records every invoice and operation in the local database.

---

## Configuration

Settings are stored in `./data/config.json` and created automatically on first run.

| Key | Meaning | Sample value |
|---|---|---|
| `xml_folder` | Folder scanned for pending XMLs | `./Pending_Invoices` |
| `processed_folder` | Destination for processed XMLs | `./Processed_Invoices` |
| `excel_file` | Spreadsheet to be filled | `./production_planning.xlsx` |
| `sheet_name` | Worksheet name | `Steel Plant` |
| `batch_column` | Column used for batch matching | `W` |
| `default_supplier` | Supplier code written to the supplier column | `36003` |
| `column_map` | Field-to-column mapping | see below |
| `max_backups` | Backups kept before the oldest is deleted | `10` |

<details>
<summary><b>Column mapping</b></summary>

| Field | Column | Field | Column |
|---|---|---|---|
| INVOICE | C | TOTAL_VALUE | L |
| ORDER | D | TAX_ICMS | M |
| SUPPLIER | E | TAX_IPI | N |
| INV_DATE | F | DUE_DATE | T |
| WEIGHT | G | BILLING | U |
| PROD | H | INV_VALUE | V |
| QUALITY | I | NCM | Z |
| THICKNESS | J | | |
| WIDTH | K | | |

</details>

---

## Project structure

```
InvoiceSystem/
├── gui.py                  # CustomTkinter interface (six screens)
├── invoice_bot.py          # XML parsing and spreadsheet writing engine
├── database.py             # SQLite: invoices, audit log, backup history
├── backup.py               # Backup creation, rotation and restore
├── config.py               # Loads and saves config.json
├── data/
│   ├── config.json         # Settings
│   ├── invoices.db         # SQLite database (created on first run)
│   └── Backups/            # Timestamped spreadsheet backups
├── Pending_Invoices/       # XMLs waiting to be processed
├── Processed_Invoices/     # XMLs moved here after processing
├── screenshots/            # Interface screenshots
├── production_planning_BEFORE.xlsx
├── production_planning_AFTER.xlsx
└── production_planning.xlsx
```

---

## Reproducing the sample output

`production_planning_AFTER.xlsx` was generated from `production_planning_BEFORE.xlsx` using the five sample XMLs and the settings in `data/config.json`.

```bash
python invoice_bot.py
```

After the run, the five invoice rows in `production_planning.xlsx` will match `production_planning_AFTER.xlsx` cell for cell.

| XML | Invoice | Batch | Row |
|---|---|---|---|
| `invoice_4.xml` | 3875370 | 25142895N | 4 |
| `invoice_1.xml` | 3874662 | 25144113K | 5 |
| `invoice_5.xml` | 3875530 | 25140767F | 6 |
| `invoice_2.xml` | 3873944 | 25140768D | 7 |
| `invoice_3.xml` | 3873950 | 25142001J | 8 |

**To run again from scratch:**
