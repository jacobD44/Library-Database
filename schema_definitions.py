# schema_definitions.py (minimal)
from sqlalchemy import MetaData, Table, Column, String, Integer, ForeignKey, Numeric, Boolean

metadata = MetaData()

Book = Table(
    "book", metadata,
    Column("Isbn", String(10), primary_key=True),
    Column("Title", String(255), nullable=False),
)

Authors = Table(
    "authors", metadata,
    Column("Author_id", Integer, primary_key=True),
    Column("Name", String(255)),
)

BookAuthors = Table(
    "book_authors", metadata,
    Column("Isbn", String(10), ForeignKey("book.Isbn"), nullable=False),
    Column("Author_id", Integer, ForeignKey("authors.Author_id"), nullable=False),
)

Borrower = Table(
    "borrower", metadata,
    Column("Card_id", String(8), primary_key=True),
    Column("Bname", String(255)),
        Column("Ssn", String(11), nullable=False),
    Column("Address", String(255), nullable=False),
    Column("Phone", String(20)),
)

BookLoans = Table(
    "book_loans", metadata,
    #loan_id needs to be a foreign key which you get from the fines table
    Column("Loan_id", Integer, primary_key=True),
    Column("Isbn", String(10), ForeignKey("book.Isbn"), nullable=False),
    Column("Card_id", String(8), ForeignKey("borrower.Card_id"), nullable=False),
    Column("Date_out", String(10), nullable=False),
    Column("Due_date", String(10), nullable=False),
    Column("Date_in", String(10)),
)

Fines = Table(
    "fines", metadata,
    Column("Loan_id", Integer, ForeignKey("book_loans.Loan_id"), primary_key=True),
    Column("Fine_amt", Numeric(10, 2), nullable=False),
    Column("Paid", Boolean, nullable=False, default=False),
)
