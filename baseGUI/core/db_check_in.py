import sqlite3
import re
from datetime import datetime, timedelta

from core.card_utils import normalize_card_id
from core.db_fines import refresh_fines

# Make sure selected entries are valid
def validate_selected_entries(selected_entries, max_available):
    count = 0
    valid_entries = []

    for entry in selected_entries:
        if count >= 3:
            print("Maximum of 3 entries can be checked in at once. Only selecting first 3.")
            break
        if entry in valid_entries:
            print(f"Entry number {entry} has already been selected.")
        elif not entry.isdigit():
            print(f"Invalid entry number: {entry}.")
        elif int(entry) < 1 or int(entry) > max_available:
            print(f"Entry number {entry} is out of range.")
        else:
            count += 1
            valid_entries.append(entry)
        
    return valid_entries

# Parse search input to get ISBN, Card ID, or Name (or substring of name)
def parse_search_input(search_input):
    search_parts = search_input.split()
    isbn = None
    card_id = None
    name = None
    for part in search_parts:
        if re.match(r"\d{9}[\dX]", part):  # Simple regex for ISBN-10
            isbn = part.upper()
        elif re.match(r"(ID)?\d+", part, re.IGNORECASE):
            card_id = normalize_card_id(part)
        elif re.match(r"[A-Za-z]+", part):
            name = part
    print(f"Parsed Input - ISBN: {isbn}, Card ID: {card_id}, Name: {name}")
    return isbn, card_id, name

def get_loan_entries(search_key):
    isbn, card_id, name = parse_search_input(search_key)
    connection = sqlite3.connect("library.db")
    cursor = connection.cursor()

    # Locate BOOK_LOANS entry with matching Isbn and Card_id.
    search_query = """
        SELECT bl.Loan_id, bl.Isbn, bl.Card_id, bl.Date_out, bl.Due_date, bl.Date_in
        FROM book_loans AS bl
        JOIN borrower AS b ON bl.Card_id = b.Card_id
        WHERE 
            (:isbn IS NULL OR bl.Isbn = :isbn) AND
            (:card_id IS NULL OR bl.Card_id = :card_id) AND
            (:name IS NULL OR LOWER(b.Bname) LIKE '%' || LOWER(:name) || '%')
    """
    cursor.execute(search_query, (isbn, card_id, name))
    loan_entries = cursor.fetchall() # tuples from matches in book_loans
    connection.close()
    return loan_entries

# Check in function intended for GUI use, no selection restriction necessary.
def check_in2(entries):
    connection = sqlite3.connect("library.db")
    cursor = connection.cursor()
    #selected_entries = validate_selected_entries(entries, len)

    if not entries:
        print("No valid entries selected for check-in.")
        connection.close()
        return
    
    print(f"Selected entries for check-in: {entries}")
    
    checkedIn = []
    for entry_num in entries:
        loan_id = int(entry_num)
        date_in = datetime.now().strftime("%Y-%m-%d")

        update_query = """
            UPDATE book_loans
            SET Date_in = ?
            WHERE Loan_id = ?
        """
        cursor.execute(update_query, (date_in, loan_id))
        checkedIn.append((loan_id,date_in))
    
    connection.commit()
    refresh_fines()
    connection.close()
    return checkedIn

# Main check in function
def check_in(search_key):
    isbn, card_id, name = parse_search_input(search_key)
    connection = sqlite3.connect("library.db")
    cursor = connection.cursor()

    # Locate BOOK_LOANS entry with matching Isbn and Card_id.
    search_query = """
        SELECT bl.Loan_id, bl.Isbn, bl.Card_id, bl.Date_out, bl.Due_date, bl.Date_in
        FROM book_loans AS bl
        JOIN borrower AS b ON bl.Card_id = b.Card_id
        WHERE 
            (:isbn IS NULL OR bl.Isbn = :isbn) AND
            (:card_id IS NULL OR bl.Card_id = :card_id) AND
            (:name IS NULL OR LOWER(b.Bname) LIKE '%' || LOWER(:name) || '%')
    """
    cursor.execute(search_query, (isbn, card_id, name))

    loan_entries = cursor.fetchall() # tuples from matches in book_loans
    print(f"Found {len(loan_entries)} matching loan entries.")
    print(f"___________________________________________________________________")
    for i, entry in enumerate(loan_entries):
        print(f"Entry {i+1}: Loan ID: {entry[0]}, ISBN: {entry[1]}, Card ID: {entry[2]}, Date Out: {entry[3]}, Due Date: {entry[4]}, Date In: {entry[5]}")
    print(f"___________________________________________________________________")

    # Select 1-3 checkouts to check in when located checked out books.
    print("Enter the Entry number of checkout to check in, separated by space (up to 3):")
    selected_entries = input().strip().split()
    selected_entries = validate_selected_entries(selected_entries, len(loan_entries))

    if not selected_entries:
        print("No valid entries selected for check-in.")
        connection.close()
        return
    
    print(f"Selected entries for check-in: {selected_entries}")
    
    for entry_num in selected_entries:
        entry_index = int(entry_num) - 1
        loan_id = loan_entries[entry_index][0]
        date_in = datetime.now().strftime("%Y-%m-%d")

        update_query = """
            UPDATE book_loans
            SET Date_in = ?
            WHERE Loan_id = ?
        """
        cursor.execute(update_query, (date_in, loan_id))
        print(f"Checked in Loan ID: {loan_id} on {date_in}.")
    
    connection.commit()
    refresh_fines()
    connection.close()
