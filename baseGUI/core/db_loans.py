import sqlite3
from typing import List, Tuple

from core.card_utils import normalize_card_id


def list_checked_out(card_id: str | None = None) -> List[Tuple]:
    """List books that are currently checked out. Optionally filter by Card_id."""
    card_id = normalize_card_id(card_id) if card_id else None
    connection = sqlite3.connect("library.db")
    cursor = connection.cursor()

    base_query = """
        SELECT bl.Loan_id, bl.Isbn, b.Title, bl.Card_id, br.Bname, bl.Date_out, bl.Due_date
        FROM book_loans bl
        JOIN book b ON bl.Isbn = b.Isbn
        JOIN borrower br ON bl.Card_id = br.Card_id
        WHERE bl.Date_in IS NULL
    """
    params: Tuple = ()
    if card_id:
        base_query += " AND bl.Card_id = ?"
        params = (card_id,)

    base_query += " ORDER BY bl.Due_date ASC"
    cursor.execute(base_query, params)
    rows = cursor.fetchall()

    if not rows:
        print("No books are currently checked out." if not card_id else f"No books are currently checked out for Card ID {card_id}.")
        connection.close()
        return []

    print("Loan ID | ISBN | Title | Card ID | Borrower | Date Out | Due Date")
    print("-------------------------------------------------------------------")
    for loan_id, isbn, title, card, borrower, date_out, due_date in rows:
        print(f"{loan_id} | {isbn} | {title} | {card} | {borrower} | {date_out} | {due_date}")

    connection.close()
    return rows
