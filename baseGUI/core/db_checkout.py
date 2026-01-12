import sqlite3
from datetime import datetime, timedelta

from core.card_utils import normalize_card_id
from core.db_fines import refresh_fines

def find_book(isbn):
    connection = sqlite3.connect("library.db")
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM book WHERE Isbn = ?", (isbn,))
    
    if cursor.fetchone()[0] == 0:
        print(f"Book with ISBN {isbn} does not exist.")
        connection.close()
        return {"error":f"Book with ISBN {isbn} does not exist."}
    
    availability_query = """
        SELECT COUNT(*) FROM book_loans
        WHERE Isbn = ? AND Date_in IS NULL
    """
    cursor.execute(availability_query, (isbn,))
    if cursor.fetchone()[0] > 0:
        print("Book is currently checked out and not available.")
        connection.close()
        return {"error":"Book is currently checked out and not available."}
    cursor.execute("SELECT * FROM book WHERE ISBN = ?", (isbn,))
    book = cursor.fetchone()
    connection.close()
    print(book)
    return book

def checkout_gui(isbn, card_id):
    card_id = normalize_card_id(card_id)
    connection = sqlite3.connect("library.db")
    cursor = connection.cursor()

    refresh_fines()
    
    # Input Validation: Valid Card_id
    cursor.execute("SELECT COUNT(*) FROM borrower WHERE Card_id = ?", (card_id,))
    if cursor.fetchone()[0] == 0:
        connection.close()
        return {"error": f"Borrower with Card_id {card_id} does not exist."}
    
    # Input Validation: Valid Isbn
    cursor.execute("SELECT COUNT(*) FROM book WHERE Isbn = ?", (isbn,))
    if cursor.fetchone()[0] == 0:
        connection.close()
        return {"error": f"Book with ISBN {isbn} does not exist."}

    # Check for any unpaid fines on Card_id
    unpaid_query = """
        SELECT COUNT(*) FROM fines F
        JOIN book_loans BL ON F.Loan_id = BL.Loan_id
        WHERE BL.Card_id = ? AND F.Paid = 0
    """
    cursor.execute(unpaid_query, (card_id,))
    if cursor.fetchone()[0] > 0:
        connection.close()
        return {"error": "Borrower has unpaid fines. Please pay fines before checking out new books."}

    # Check for maximum active loans (3) on Card_id
    max_loan_query = """
        SELECT COUNT(*) FROM book_loans
        WHERE Card_id = ? AND Date_in IS NULL
    """
    cursor.execute(max_loan_query, (card_id,))
    active_loans = cursor.fetchone()[0]
    if active_loans >= 3:
        connection.close()
        return {"error": f"Borrower already has {active_loans} active loan(s). Maximum allowed is 3."}

    # Check book availability on Isbn
    availability_query = """
        SELECT COUNT(*) FROM book_loans
        WHERE Isbn = ? AND Date_in IS NULL
    """
    cursor.execute(availability_query, (isbn,))
    if cursor.fetchone()[0] > 0:
        connection.close()
        return {"error": "Book is currently checked out and not available."}
    
    # Passed all checks, now checkout the book
    date_out = datetime.now().strftime("%Y-%m-%d")
    due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    cursor.execute("SELECT Title FROM book WHERE Isbn = ?", (isbn,))
    title = cursor.fetchone()[0]
    
    insert_query = """
        INSERT INTO book_loans (Isbn, Card_id, Date_out, Due_date, Date_in)
        VALUES (?, ?, ?, ?, ?)
    """
    cursor.execute(insert_query, (isbn, card_id, date_out, due_date, None))
    connection.commit()
    connection.close()

    return (isbn, card_id, date_out, due_date, title)

def checkout(isbn, card_id):
    card_id = normalize_card_id(card_id)
    connection = sqlite3.connect("library.db")
    cursor = connection.cursor()

    refresh_fines()
    
    # Input Validation: Valid Card_id
    cursor.execute("SELECT COUNT(*) FROM borrower WHERE Card_id = ?", (card_id,))
    if cursor.fetchone()[0] == 0:
        print(f"Borrower with Card_id {card_id} does not exist.")
        connection.close()
        return False
    
    # Input Validation: Valid Isbn
    cursor.execute("SELECT COUNT(*) FROM book WHERE Isbn = ?", (isbn,))
    if cursor.fetchone()[0] == 0:
        print(f"Book with ISBN {isbn} does not exist.")
        connection.close()
        return False

    # Check for any unpaid fines on Card_id
    unpaid_query = """
        SELECT COUNT(*) FROM fines F
        JOIN book_loans BL ON F.Loan_id = BL.Loan_id
        WHERE BL.Card_id = ? AND F.Paid = 0
    """
    cursor.execute(unpaid_query, (card_id,))
    if cursor.fetchone()[0] > 0:
        print("Borrower has unpaid fines. Please pay fines before checking out new books.")
        connection.close()
        return False

    # Check for maximum active loans (3) on Card_id
    max_loan_query = """
        SELECT COUNT(*) FROM book_loans
        WHERE Card_id = ? AND Date_in IS NULL
    """
    cursor.execute(max_loan_query, (card_id,))
    active_loans = cursor.fetchone()[0]
    if active_loans >= 3:
        print(f"Borrower already has {active_loans} active loan(s). Maximum allowed is 3.")
        connection.close()
        return False

    # Check book availability on Isbn
    availability_query = """
        SELECT COUNT(*) FROM book_loans
        WHERE Isbn = ? AND Date_in IS NULL
    """
    cursor.execute(availability_query, (isbn,))
    if cursor.fetchone()[0] > 0:
        print("Book is currently checked out and not available.")
        connection.close()
        return False
    
    # Passed all checks, now checkout the book
    date_out = datetime.now().strftime("%Y-%m-%d")
    due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

    insert_query = """
        INSERT INTO book_loans (Isbn, Card_id, Date_out, Due_date)
        VALUES (?, ?, ?, ?)
    """
    cursor.execute(insert_query, (isbn, card_id, date_out, due_date))
    connection.commit()
    connection.close()

    print(f"Successfully checked out book with Isbn {isbn} on {date_out}. Due date: {due_date}")
    return True