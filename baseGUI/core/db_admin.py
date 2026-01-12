import sqlite3
from datetime import datetime

from core.db_fines import refresh_fines

DATE_FORMAT = "%Y-%m-%d"


def backdate_due(isbn: str, new_due_date: str) -> bool:
    """Update the Due_date of the most recent loan for the given ISBN."""
    try:
        datetime.strptime(new_due_date, DATE_FORMAT)
    except ValueError:
        print(f"Invalid date format. Use {DATE_FORMAT} (e.g., 2024-10-15).")
        return False

    connection = sqlite3.connect("library.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT Loan_id, Date_out, Due_date, Date_in
        FROM book_loans
        WHERE Isbn = ?
        ORDER BY Date_out DESC
        LIMIT 1
        """,
        (isbn,),
    )
    row = cursor.fetchone()

    if not row:
        print(f"No loans found for ISBN {isbn}.")
        connection.close()
        return False

    loan_id, date_out, old_due, date_in = row
    cursor.execute(
        "UPDATE book_loans SET Due_date = ? WHERE Loan_id = ?",
        (new_due_date, loan_id),
    )
    connection.commit()
    connection.close()

    refresh_fines()
    print(
        f"Updated Loan {loan_id} (ISBN {isbn}) Due_date from {old_due} to {new_due_date}."
        f" Date_out: {date_out}, Date_in: {date_in}"
    )
    return True

