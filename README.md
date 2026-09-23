# Invoice Management System

Version 2.0

A desktop application that reads Brazilian electronic invoice XML files (NF-e),
cross-references each invoice against a production planning spreadsheet by batch
number, and writes the invoice data into the matching row while preserving all
existing cell formatting.

All data in this package is anonymized sample data. Company names, tax IDs,
addresses, contacts and registration numbers have been replaced with fictitious
values, and digital signature blocks have been removed from the sample XMLs.

Geographic identifiers are neutral as well: the state code is `99` and the
municipal codes are `9999999` and `9999998`, in the `cUF`, `cMunFG` and `cMun`
fields and at the start of every access key. The access keys carry a valid
modulo-11 check digit recomputed after the change, and each file has its own
unique key and protocol number.

---

## 1. Requirements

- Python 3.10 or higher
- Dependencies:

```
pip install customtkinter openpyxl xmltodict Pillow
```

---

## 2. Running the application

Graphical interface:

```
python gui.py
```

Processing engine only (no interface, logs to console):

```
python invoice_bot.py
```

---

## 3. Configuration

Settings are stored in `./data/config.json`, relative to the project folder.
The application creates this file automatically on first run if it does not exist.

| Key | Meaning | Value in this package |
|---|---|---|
| `xml_folder` | Folder scanned for pending XML files | `./Pending_Invoices` |
| `processed_folder` | Folder XMLs are moved to after processing | `./Processed_Invoices` |
| `excel_file` | Spreadsheet to be filled | `./production_planning.xlsx` |
| `sheet_name` | Worksheet name inside the file | `Steel Plant` |
| `batch_column` | Column holding the batch number used for matching | `W` |
| `default_supplier` | Supplier code written to the supplier column | `36003` |
| `column_map` | Maps each data field to a spreadsheet column | see below |
| `max_backups` | Number of backups kept before the oldest is deleted | `10` |

Column mapping used by this package:

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

---

## 4. How to use

First run:

1. Start the application with `python gui.py`.
2. Open the **Settings** tab.
3. Set the pending XML folder, the processed XML folder, the spreadsheet path,
   the worksheet name and the batch column.
4. Click **Save Settings**.

To post invoices:

1. Place the XML files in the pending folder.
2. Open the **Process Invoices** tab.
3. Click **PROCESS INVOICES IN SPREADSHEET**.

The engine then:

- creates a timestamped backup of the spreadsheet before the first write;
- checks each invoice against the database and skips any already processed;
- reads the batch number from the XML and looks it up in the batch column;
- writes the invoice data into the matching row, preserving cell formatting;
- saves the workbook once, after all invoices in the run are processed;
- moves the processed XMLs to the processed folder;
- records every invoice and every operation in the local database.

---

## 5. Protections

| Protection | Behaviour |
|---|---|
| Automatic backup | Copies the spreadsheet before the first write of each run |
| Duplicate detection | Skips invoices whose access key is already in the database |
| Audit log | Records every operation with type, timestamp and detail |
| Local database | SQLite file holding invoice history, audit log and backup history |
| Single save | Writes the workbook once per run, regardless of batch size |
| Backup rotation | Keeps only the most recent backups, per `max_backups` |

---

## 6. Interface

The interface is built with customtkinter and has six screens:

| Screen | Purpose |
|---|---|
| Dashboard | Summary counters and a table of the most recent invoices |
| Process Invoices | Runs the engine and streams its log to the screen |
| Settings | Folder paths, spreadsheet path, worksheet, column mapping |
| Audit Log | Full operation history from the database |
| Backups | Lists backups on disk, with restore |
| Outlook (Soon) | Placeholder for the planned mailbox integration |

Screenshots of each screen are in the `screenshots/` folder.

---

## 7. Source files

| File | Role |
|---|---|
| `gui.py` | customtkinter interface, all six screens |
| `invoice_bot.py` | XML parsing and spreadsheet writing engine |
| `database.py` | SQLite access: invoices, audit log, backup history |
| `backup.py` | Backup creation, rotation and restore |
| `config.py` | Loads and saves `./data/config.json` |

`gui.py` will display a `logo.png` placed next to it in the sidebar if one is
present. No logo ships with this package, and the interface renders normally
without it.

Runtime data, all under the project folder:

```
InvoiceSystem/
├── data/
│   ├── config.json        — settings
│   ├── invoices.db        — SQLite database (created on first run)
│   └── Backups/           — timestamped spreadsheet backups
├── Pending_Invoices/      — XMLs waiting to be processed
└── Processed_Invoices/    — XMLs moved here after processing
```

---

## 8. Package contents

| Item | Format | Description |
|---|---|---|
| `gui.py` | Python source (.py) | Graphical interface |
| `invoice_bot.py` | Python source (.py) | Processing engine |
| `database.py` | Python source (.py) | Database layer |
| `backup.py` | Python source (.py) | Backup system |
| `config.py` | Python source (.py) | Configuration management |
| `README.md` | Markdown (.md) | This document |
| `production_planning_BEFORE.xlsx` | Excel workbook (.xlsx) | Reference input spreadsheet, before processing |
| `production_planning_AFTER.xlsx` | Excel workbook (.xlsx) | Output produced by running the engine on the BEFORE file |
| `production_planning.xlsx` | Excel workbook (.xlsx) | Working copy, identical to the BEFORE file, targeted by `config.json` |
| `Pending_Invoices/invoice_1.xml` … `invoice_5.xml` | NF-e XML (.xml) | Five anonymized sample invoices |
| `Processed_Invoices/` | Folder | Empty; destination for processed XMLs |
| `data/config.json` | JSON (.json) | Settings used to produce the AFTER file |
| `data/Backups/` | Folder | Empty; destination for automatic backups |
| `screenshots/` | PNG images (.png) | One screenshot per interface screen |

---

## 9. Reproducing the delivered output

`production_planning_AFTER.xlsx` was produced from
`production_planning_BEFORE.xlsx` using the five XMLs in `Pending_Invoices/`
and the settings in `data/config.json`.

To reproduce it from a clean state:

```
python invoice_bot.py
```

The engine reads `./production_planning.xlsx`, which ships as an exact copy of
the BEFORE file. After the run, the five invoice rows in that file will match
`production_planning_AFTER.xlsx` cell for cell.

The five invoices map to these rows, matched on the batch number in column W:

| XML | Invoice number | Batch | Row |
|---|---|---|---|
| `invoice_4.xml` | 3875370 | 25142895N | 4 |
| `invoice_1.xml` | 3874662 | 25144113K | 5 |
| `invoice_5.xml` | 3875530 | 25140767F | 6 |
| `invoice_2.xml` | 3873944 | 25140768D | 7 |
| `invoice_3.xml` | 3873950 | 25142001J | 8 |

To run it a second time from scratch, delete `data/invoices.db`, copy
`production_planning_BEFORE.xlsx` over `production_planning.xlsx`, and move the
XMLs from `Processed_Invoices/` back to `Pending_Invoices/`. Without deleting
the database, the duplicate check will correctly skip all five invoices.

---

## 10. Building an executable (optional)

```
pip install pyinstaller
pyinstaller --onefile --windowed gui.py
```

The executable is written to the `dist/` folder. The application uses no bundled
icon or logo file, so no `--add-data` or `--icon` arguments are required.

---

## 11. Planned work

The **Outlook** screen is a placeholder for a planned integration that would
monitor a mailbox, download invoice XMLs from incoming messages and process them
without manual intervention. It is not implemented in this version.
#   I n v o i c e - A u t o m a t i o n  
 