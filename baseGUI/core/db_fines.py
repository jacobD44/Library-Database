import csv
import os
import sqlite3
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import List, Optional, Tuple

from core.card_utils import normalize_card_id

DAILY_RATE = Decimal("0.25")
DATE_FORMAT = "%Y-%m-%d"
DATA_DIR = Path("normalized_files")


def _parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, DATE_FORMAT).date()


def _calculate_fine(due_date: str, date_in: Optional[str], today: Optional[date] = None) -> Decimal:
    """Return the fine for a single loan based on due and return dates."""
    reference_date = _parse_date(date_in) if date_in else (today or date.today())
    days_late = (reference_date - _parse_date(due_date)).days
    if days_late <= 0:
        return Decimal("0.00")
    return (DAILY_RATE * days_late).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def refresh_fines(today: Optional[date] = None) -> None:
    """Upsert fines for late loans. Paid fines are left untouched."""
    connection = sqlite3.connect("library.db")
    cursor = connection.cursor()

    cursor.execute("SELECT Loan_id, Due_date, Date_in FROM book_loans")
    rows = cursor.fetchall()

    inserted = 0
    updated = 0
    skipped_paid = 0

    for loan_id, due_date, date_in in rows:
        fine_amount = _calculate_fine(due_date, date_in, today)
        if fine_amount == Decimal("0.00"):
            continue

        cursor.execute("SELECT Paid, Fine_amt FROM fines WHERE Loan_id = ?", (loan_id,))
        existing = cursor.fetchone()

        if existing:
            paid_flag, existing_amount = existing
            if paid_flag:
                skipped_paid += 1
                continue
            existing_decimal = Decimal(str(existing_amount))
            if existing_decimal != fine_amount:
                cursor.execute(
                    "UPDATE fines SET Fine_amt = ? WHERE Loan_id = ?",
                    (str(fine_amount), loan_id),
                )
                updated += 1
        else:
            cursor.execute(
                "INSERT INTO fines (Loan_id, Fine_amt, Paid) VALUES (?, ?, 0)",
                (loan_id, str(fine_amount)),
            )
            inserted += 1

    connection.commit()
    connection.close()
    print(f"Fines refreshed: {inserted} inserted, {updated} updated, {skipped_paid} skipped (already paid).")


def _ensure_borrower_names() -> None:
    """Fill missing borrower.Bname from normalized borrower CSV."""
    csv_path = DATA_DIR / "borrower.csv"
    if not csv_path.exists():
        return

    connection = sqlite3.connect("library.db")
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM borrower WHERE Bname IS NULL OR Bname = ''")
    missing_count = cursor.fetchone()[0]
    if missing_count == 0:
        connection.close()
        return

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        updates = []
        for row in reader:
            card = row.get("Card_id")
            fname = row.get("Fname", "") or ""
            lname = row.get("Lname", "") or ""
            if card:
                bname = f"{fname} {lname}".strip()
                updates.append((bname, card))

    if updates:
        cursor.executemany("UPDATE borrower SET Bname = ? WHERE Card_id = ? AND (Bname IS NULL OR Bname = '')", updates)
        connection.commit()
    connection.close()


def list_fines(
    include_paid: bool = False,
    as_of: Optional[date] = None,
    card_id: Optional[str] = None,
) -> List[Tuple[str, str, Decimal, bool]]:
    """Return and display fines grouped by borrower card_id."""
    _ensure_borrower_names()
    refresh_fines(today=as_of)
    connection = sqlite3.connect("library.db")
    cursor = connection.cursor()

    base_query = """
        SELECT bl.Card_id, b.Bname, f.Paid, SUM(CAST(f.Fine_amt AS NUMERIC)) AS total_fine
        FROM fines f
        JOIN book_loans bl ON f.Loan_id = bl.Loan_id
        JOIN borrower b ON bl.Card_id = b.Card_id
    """
    conditions = []
    params = []
    if not include_paid:
        conditions.append("f.Paid = 0")
    if card_id:
        conditions.append("bl.Card_id = ?")
        params.append(card_id)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " GROUP BY bl.Card_id, b.Bname, f.Paid"
    cursor.execute(base_query, params)
    rows = cursor.fetchall()

    if not rows:
        print("No fines to display.")
        connection.close()
        return []

    print("Card ID | Borrower | Total Fine")
    print("--------------------------------")
    normalized_rows: List[Tuple[str, str, Decimal, bool]] = []
    for card_id, name, paid_flag, total in rows:
        total_decimal = Decimal(str(total or 0)).quantize(Decimal("0.01"))
        normalized_rows.append((card_id, name, total_decimal, bool(paid_flag)))
        status = " (paid)" if paid_flag else ""
        print(f"{card_id} | {name} | ${total_decimal}{status}")

    connection.close()
    return normalized_rows


def pay_fines(card_id: str) -> Tuple[bool, str]:
    """Mark all unpaid fines for a borrower as paid if all books are returned."""
    refresh_fines()
    card_id = normalize_card_id(card_id)
    connection = sqlite3.connect("library.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT SUM(CAST(f.Fine_amt AS NUMERIC)) AS outstanding
        FROM fines f
        JOIN book_loans bl ON f.Loan_id = bl.Loan_id
        WHERE bl.Card_id = ? AND f.Paid = 0
        """,
        (card_id,),
    )
    outstanding = cursor.fetchone()[0]
    if outstanding is None:
        message = f"No unpaid fines for Card ID {card_id}."
        print(message)
        connection.close()
        return False, message

    cursor.execute(
        """
        SELECT COUNT(*) FROM fines f
        JOIN book_loans bl ON f.Loan_id = bl.Loan_id
        WHERE bl.Card_id = ? AND f.Paid = 0 AND bl.Date_in IS NULL
        """,
        (card_id,),
    )
    still_out = cursor.fetchone()[0]
    if still_out:
        message = "Cannot accept payment: at least one fined book is not yet returned."
        print(message)
        connection.close()
        return False, message

    cursor.execute(
        """
        UPDATE fines
        SET Paid = 1
        WHERE Loan_id IN (SELECT Loan_id FROM book_loans WHERE Card_id = ?) AND Paid = 0
        """,
        (card_id,),
    )
    connection.commit()
    connection.close()

    paid_amount = Decimal(str(outstanding)).quantize(Decimal("0.01"))
    message = f"Payment accepted. Cleared ${paid_amount} in fines for Card ID {card_id}."
    print(message)
    return True, message
