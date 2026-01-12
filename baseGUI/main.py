from core.db_search import search
from core.db_checkout import checkout
from core.db_check_in import check_in
from core.db_borrower import create_borrower
from core.db_fines import list_fines, pay_fines, refresh_fines
from core.db_admin import backdate_due
from core.db_loans import list_checked_out
from core.card_utils import normalize_card_id


def main():
    while True:
        print("\n________________________")
        print("Library DB Menu")
        print("________________________")
        print("1. Search for Book")
        print("2. Check Out Book")
        print("3. Check In Book")
        print("4. Create Borrower")
        print("5. Refresh Fines")
        print("6. View Fines")
        print("7. Pay Fines")
        print("8. List Checked Out Books")
        print("B. Backdate Due Date (admin)")
        print("Q. Quit")
        print("________________________")
        usr_select = input("Select an option (1-8, B, or Q): ").strip()

        if usr_select == '1':
            print("Search for Book selected.")
            search_key = input("Enter search key (ISBN, Title, or Author): ").strip()
            search(search_key)
        elif usr_select == '2':
            print("Check Out Book selected.")
            isbn_input = input("Enter ISBN: ").strip()
            card_input = input("Enter Card ID: ").strip()
            checkout(isbn_input, card_input)
        elif usr_select == '3':
            print("Check In Book selected.")
            print("Enter (Isbn, Card_id, and/or Borrower name substring), separate by spaces.")
            search_input = input("Enter Search for Check In: ").strip()
            check_in(search_input)
        elif usr_select == '4':
            print("Create Borrower selected.")
            name = input("Enter Name: ").strip()
            ssn = input("Enter SSN: ").strip()
            address = input("Enter Address: ").strip()
            phone = input("Enter Phone (optional): ").strip()
            if phone == "":
                phone = None
            create_borrower(name, ssn, address, phone)
        elif usr_select == '5':
            print("Refreshing fines for all late loans...")
            refresh_fines()
        elif usr_select == '6':
            include_paid = input("Include paid fines? (y/N): ").strip().lower() == "y"
            list_fines(include_paid=include_paid)
        elif usr_select == '7':
            card_input = input("Enter Card ID to pay fines: ").strip()
            success, message = pay_fines(card_input)
            if message:
                print(message)
        elif usr_select == '8':
            card_filter = input("Enter Card ID to filter (or press Enter for all): ").strip()
            card_filter = card_filter if card_filter else None
            list_checked_out(card_filter)
        elif usr_select.upper() == 'B':
            isbn_input = input("Enter ISBN to backdate: ").strip()
            new_due = input("Enter new due date (YYYY-MM-DD): ").strip()
            backdate_due(isbn_input, new_due)
        elif usr_select.upper() == 'Q':
            print("Exiting the program.")
            break
        else:
            print("Invalid selection. Please choose a valid option.")

if __name__ == "__main__":
    main()
