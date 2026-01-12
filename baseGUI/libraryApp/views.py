import sqlite3
from datetime import datetime, date

from django.shortcuts import render, HttpResponse
from core.db_search import search
from core.db_checkout import checkout_gui, find_book
from core.db_check_in import get_loan_entries
from core.db_check_in import check_in2
from core.db_borrower import create_borrower
from core.db_fines import list_fines, pay_fines, refresh_fines
from core.db_admin import backdate_due
from core.db_loans import list_checked_out
from core.card_utils import normalize_card_id
#from core.card_utils import normalize_card_id

# Create your views here.
# Page Base views
def home(req):
    return render(req, "home.html")

def booksearch(req):
    query = req.GET.get("search_book", "")
    results = []

    if query:
        results = search(query)

    return render(req, "booksearch.html", {"query": query, "results": results})

# Handle User Search book loans and check in.
def checkin(req):
    user_search = req.GET.get("search_loan", "").strip() # from HTML (get)
    user_select = req.POST.getlist("selected_loans") # from HTML (post)
    results = None
    checkedInDict = None

    # if user has searched, get the entries
    if user_search:
        results = get_loan_entries(user_search)
    # if user selected entries to check in, stop showing table, show loan ids entered into + checkin date
    if user_select:
        checkedInDict = check_in2(user_select)
        results = None
    return render(req, "checkin.html", {
        "results": results,
        "checkedIn": checkedInDict
    })

def checkout(req):
    user_book = req.GET.get("find_book", "").strip()
    user_card_id = req.GET.get("checkout", "").strip()
    result = None
    loan = None
    error = None
    
    if user_book:
        find_result = find_book(user_book)
        if isinstance(find_result, dict) and "error" in find_result:
            error = find_result["error"]
        else:
            result = find_result
    
    if user_card_id:
        checkout_result = checkout_gui(user_book, user_card_id)
        if isinstance(checkout_result, dict) and "error" in checkout_result:
            error = checkout_result["error"]
            if result is None:
                result = find_book(user_book)
        else:
            loan = checkout_result
            result = None
    
    return render(req, "checkout.html", {
        "result": result,
        "loan": loan,
        "user_book": user_book,
        "error": error
    })

def borrowers(req):
    context = {}

    if req.method == "POST":
        name = req.POST.get("name", "").strip()
        ssn = req.POST.get("ssn", "").strip()
        address = req.POST.get("address", "").strip()
        phone = req.POST.get("phone", "").strip()

        errors = []

        # 1. Required fields
        if not name or not ssn or not address:
            errors.append("Name, SSN, and address are required.")

        if not errors:
            
            try:
                success, message = create_borrower(name, ssn, address, phone)
            except Exception as e:
                success = False
                message = str(e)

            if success:
                context["success"] = message 
            else:
                errors.append(message)

        if errors:
            context["errors"] = errors
            context["form"] = {
                "name": name,
                "ssn": ssn,
                "address": address,
                "phone": phone,
            }

    return render(req, "borrowers.html", context)

def fines(req):
    include_paid_flag = req.POST.get("include_paid", req.GET.get("include_paid", "0"))
    include_paid = include_paid_flag == "1"
    success_message = None
    error_message = None
    card_id_value = req.POST.get("card_id", req.GET.get("card_id", "")).strip()
    borrower_name = None
    current_loans = []
    outstanding_total = None
    today_str = date.today().isoformat()
    user_fines_detail = []
    admin_all_fines = []

    if req.method == "POST":
        action = req.POST.get("action")
        if action == "refresh":
            refresh_fines()
            success_message = "Fines have been refreshed."
        elif action == "pay":
            if not card_id_value:
                error_message = "Card ID is required to pay fines."
            else:
                paid, message = pay_fines(card_id_value)
                if paid:
                    success_message = message
                else:
                    error_message = message
        elif action == "checkin":
            loan_id = req.POST.get("loan_id", "").strip()
            if not loan_id:
                error_message = "Loan ID is required to check in."
            elif not loan_id.isdigit():
                error_message = "Invalid loan ID."
            else:
                try:
                    check_in2([loan_id])
                    success_message = f"Checked in loan {loan_id}."
                except Exception as exc:
                    error_message = f"Could not check in loan {loan_id}: {exc}"
        elif action == "update_loan_dates":
            loan_id = req.POST.get("loan_id", "").strip()
            date_out_str = req.POST.get("date_out", "").strip()
            due_date_str = req.POST.get("due_date", "").strip()
            date_in_str = req.POST.get("date_in", "").strip()
            if not loan_id or not loan_id.isdigit():
                error_message = "Valid loan ID is required."
            else:
                try:
                    datetime.strptime(date_out_str, "%Y-%m-%d")
                    datetime.strptime(due_date_str, "%Y-%m-%d")
                    if date_in_str:
                        datetime.strptime(date_in_str, "%Y-%m-%d")
                except ValueError:
                    error_message = "Dates must be in YYYY-MM-DD format."
                else:
                    connection = sqlite3.connect("library.db")
                    cursor = connection.cursor()
                    cursor.execute(
                        """
                        UPDATE book_loans
                        SET Date_out = ?, Due_date = ?, Date_in = ?
                        WHERE Loan_id = ?
                        """,
                        (date_out_str, due_date_str, date_in_str if date_in_str else None, loan_id),
                    )
                    connection.commit()
                    connection.close()
                    refresh_fines()
                    success_message = f"Updated loan {loan_id} and recalculated fines."

    # Load borrower details and current loans if a card ID is provided
    normalized_card = normalize_card_id(card_id_value) if card_id_value else None
    connection = sqlite3.connect("library.db")
    cursor = connection.cursor()
    if normalized_card:
        cursor.execute("SELECT Bname FROM borrower WHERE Card_id = ?", (normalized_card,))
        row = cursor.fetchone()
        if row:
            borrower_name = row[0]
            cursor.execute(
                """
                SELECT bl.Loan_id, bl.Isbn, b.Title, bl.Date_out, bl.Due_date
                FROM book_loans bl
                JOIN book b ON bl.Isbn = b.Isbn
                WHERE bl.Card_id = ? AND bl.Date_in IS NULL
                ORDER BY bl.Due_date ASC
                """,
                (normalized_card,),
            )
            current_loans = cursor.fetchall()

            fine_conditions = []
            fine_params = [normalized_card]
            if not include_paid:
                fine_conditions.append("f.Paid = 0")

            fine_clause = ""
            if fine_conditions:
                fine_clause = " AND " + " AND ".join(fine_conditions)

            cursor.execute(
                f"""
                SELECT bl.Loan_id, bk.Title, bl.Date_out, bl.Due_date, f.Fine_amt, f.Paid
                FROM fines f
                JOIN book_loans bl ON f.Loan_id = bl.Loan_id
                JOIN book bk ON bl.Isbn = bk.Isbn
                WHERE bl.Card_id = ?{fine_clause}
                ORDER BY bl.Due_date ASC
                """,
                fine_params,
            )
            user_fines_detail = cursor.fetchall()
        else:
            error_message = error_message or f"No borrower found for Card ID {normalized_card}."

    # Admin overview of all fines
    admin_conditions = []
    admin_params = []
    if not include_paid:
        admin_conditions.append("f.Paid = 0")

    admin_clause = ""
    if admin_conditions:
        admin_clause = " WHERE " + " AND ".join(admin_conditions)

    cursor.execute(
        f"""
        SELECT bl.Loan_id, bl.Card_id, br.Bname, bk.Title, bl.Date_out, bl.Due_date, f.Fine_amt, f.Paid
        FROM fines f
        JOIN book_loans bl ON f.Loan_id = bl.Loan_id
        JOIN borrower br ON bl.Card_id = br.Card_id
        JOIN book bk ON bl.Isbn = bk.Isbn
        {admin_clause}
        ORDER BY bl.Card_id, bl.Loan_id
        """,
        admin_params,
    )
    admin_all_fines = cursor.fetchall()

    cursor.execute(
        """
        SELECT bl.Loan_id, bl.Card_id, br.Bname, bk.Title, bl.Date_out, bl.Due_date, bl.Date_in
        FROM book_loans bl
        JOIN borrower br ON bl.Card_id = br.Card_id
        JOIN book bk ON bl.Isbn = bk.Isbn
        WHERE bl.Date_in IS NULL
        ORDER BY bl.Due_date ASC
        """
    )
    admin_checked_out = cursor.fetchall()
    connection.close()

    fines_list = list_fines(include_paid=include_paid, card_id=normalized_card)
    for entry in fines_list:
        if not entry[3]:  # unpaid
            outstanding_total = entry[2]
            break

    return render(req, "fines.html", {
        "fines": fines_list,
        "include_paid": include_paid,
        "success_message": success_message,
        "error_message": error_message,
        "card_id_value": normalized_card or card_id_value,
        "borrower_name": borrower_name,
        "current_loans": current_loans,
        "outstanding_total": outstanding_total,
        "today_str": today_str,
        "user_fines_detail": user_fines_detail,
        "admin_all_fines": admin_all_fines,
        "admin_checked_out": admin_checked_out,
    })
