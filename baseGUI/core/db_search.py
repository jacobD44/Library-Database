import sqlite3


# TODO: Check/display status of each book returned from search
def search(search_key):
    connection = sqlite3.connect('library.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    query = """SELECT B.isbn, B.title, GROUP_CONCAT(A.name, ', ') AS authors,
                CASE
                    WHEN BL.Isbn IS NULL THEN 'IN'
                    ELSE 'OUT'
                END AS status,
                BL.Card_id AS Borrower_id
               FROM book B
               JOIN book_authors BA ON B.Isbn = BA.Isbn
               JOIN authors A ON BA.Author_id = A.Author_id
               LEFT JOIN book_loans BL ON B.Isbn = BL.Isbn AND BL.Date_in IS NULL
               WHERE
                    LOWER(B.Isbn) LIKE '%' || LOWER(?) || '%' OR
                    LOWER(B.Title) LIKE '%' || LOWER(?) || '%' OR
                    LOWER(A.Name) LIKE '%' || LOWER(?) || '%'
               GROUP BY B.Isbn, B.Title, status"""
    
    args = (search_key, search_key, search_key)
    cursor.execute(query, args)

    results = cursor.fetchall()
    connection.close()
    idx = 1
    print(f"")

    for row in results:
        print(f"{idx} - {row['Isbn']} - {(row['Title'] or ''):.100} - {(row['authors'] or ''):.100} - {(row['status'] or '')}")
        idx += 1
    return results