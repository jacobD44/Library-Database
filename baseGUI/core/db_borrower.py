import sqlite3

DB_PATH = "library.db"


def generate_new_card_id(cursor):
    """
    Generate a new Card_id using the existing max in the borrower table.
    Assumes Card_id looks like 'ID000001', 'ID000002', etc.
    """
    cursor.execute("SELECT Card_id FROM borrower ORDER BY Card_id DESC LIMIT 1")
    row = cursor.fetchone()

    # no existing borrowers yet
    if row is None or row[0] is None:
        return "ID000001"

    last_id = row[0]          
    try:
        # take everything after the first two characters "ID"
        last_num = int(last_id[2:])
    except ValueError:
        last_num = 0

    new_num = last_num + 1
    return f"ID{new_num:06d}"


def create_borrower(name, ssn, address, phone=None):
    """
    Create a new borrower in the system.
    Requirements:
    - name, ssn, and address must be provided (NOT NULL)
    - each SSN can only have one borrower (one card per SSN)
    - Card_id is auto-generated in the form 'ID0000xx'
    Returns: (success: bool, message: str)
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    print(ssn)
    # validate required fields
    if not name or not ssn or not address:
        connection.close()
        return False, "Name, SSN, and Address are required fields."

    # SSN must be exactly 9 digits
    if not ssn.isdigit() or len(ssn) != 9:
        connection.close()
        return False, "SSN must be exactly 9 digits."
    ssn = f"{ssn[0:3]}-{ssn[3:5]}-{ssn[5:9]}"

    # check if a borrower already exists with this SSN
    try:
        cursor.execute("SELECT COUNT(*) FROM borrower WHERE Ssn = ?", (ssn,))
    except sqlite3.OperationalError as e:
        connection.close()
        return (
            False,
            "Database error when checking SSN. "
            "Make sure your 'borrower' table has an 'Ssn' column. "
            f"Details: {e}",
        )

    if cursor.fetchone()[0] > 0:
        connection.close()
        return False, "A borrower with this SSN already exists."

    # generate new Card_id
    new_card_id = generate_new_card_id(cursor)

    insert_query = """
        INSERT INTO borrower (Card_id, Bname, Ssn, Address, Phone)
        VALUES (?, ?, ?, ?, ?)
    """

    try:
        cursor.execute(insert_query, (new_card_id, name, ssn, address, phone))
        connection.commit()
    except sqlite3.Error as e:
        connection.rollback()
        connection.close()
        return (
            False,
            f"Error: Unable to create borrower due to a database error. Details: {e}",
        )

    connection.close()

    # success
    return True, f"Successfully created new borrower. Card ID: {new_card_id}"

def find_borrower_by_ssn(ssn):
    """
    Optional helper: look up a borrower by SSN.
    Useful for debugging / verifying behavior.
    """
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    ssn = f"{ssn[0:3]}-{ssn[3:5]}-{ssn[5:9]}"

    cursor.execute("SELECT * FROM borrower WHERE Ssn = ?", (ssn,))
    row = cursor.fetchone()
    connection.close()

    if not row:
        print("No borrower found with that SSN.")
        return None

    print("Borrower record:")
    print(f"Card_id: {row['Card_id']}")
    print(f"Name   : {row['Bname']}")
    print(f"SSN    : {row['Ssn']}")
    print(f"Address: {row['Address']}")
    print(f"Phone  : {row['Phone']}")
    return row


if __name__ == "__main__":
    # Simple CLI for manual testing of borrowers
    print("=== Create New Borrower ===")
    name = input("Enter Name: ").strip()
    ssn = input("Enter SSN: ").strip()
    address = input("Enter Address: ").strip()
    phone = input("Enter Phone (optional): ").strip()

    if phone == "":
        phone = None

    create_borrower(name, ssn, address, phone)