# Library CLI

Command-line library manager on SQLite. Search books, check them in/out, list active loans, and handle fines from a text menu.

## Requirements
- Python 3.10+
- Official Django release (At least ver 5.2.9)
- Packages: `sqlalchemy`, `pandas` (`sqlite3` is stdlib)

Install extras:
```bash
pip install sqlalchemy pandas
python -m pip install Django
```
## Django Site
- Hosted locally: http://127.0.0.1:8000/
## Project Layout
- `database_normalizer.py` – prompts for raw CSVs and normalizes them into `normalized_files/`.
- `database_creator.py` – builds `library.db` from normalized CSVs.
- `main.py` – CLI entry point.
- `db_*.py` – feature modules (search, checkout, check-in, fines, loans, admin backdate).
- `card_utils.py` – normalizes Card IDs (accepts `ID000123`, `000123`, or `123`).

## Running the Website
1) Change directory to the location of baseGUI directory
```bash
cd baseGUI
```
make sure to put the correct filepath to baseGUI

2) Run python command: "python manage.py runserver" (make sure Django installed as at least above version)
```bash
python manage.py runserver
```
3) Go to a web browser (like Google Chrome, Firefox, etc.) and type:
```bash
http://127.0.0.1:8000/
```
This will run the website locally.

## Setup
1) Prepare data (skip if `normalized_files/` already exists):
```bash
python database_normalizer.py  # follow prompts for books.csv (tab-separated) and borrowers.csv
```
2) Build the SQLite database:
```bash
python database_creator.py
```
3) Run the CLI :
```bash
python main.py
```

## Menu Actions
- `1` Search for Book: case-insensitive substring match on ISBN/Title/Author with availability.
- `2` Check Out Book: validates ISBN/card, max 3 active loans, no unpaid fines, and book availability.
- `3` Check In Book: search by ISBN, Card ID, or borrower name; pick entries to return.
- `4` Refresh Fines: recalculates fines for all late loans; leaves paid fines untouched.
- `5` View Fines: lists fines (optionally includes paid, marked `(paid)`).
- `6` Pay Fines: pays all unpaid fines for a Card ID if all fined books are returned.
- `7` List Checked Out Books: shows active loans, optionally filtered by Card ID.
- `B` Backdate Due Date (admin): set a new due date for the most recent loan of an ISBN.
- `Q` Quit.

## Notes
- Dates use `YYYY-MM-DD`.
- Fine rate is $0.25/day, rounded to cents. Paid fines are never overwritten when refreshing.
- Card IDs are normalized automatically to the `ID######` format.
