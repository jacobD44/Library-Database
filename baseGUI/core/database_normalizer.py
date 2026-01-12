import os
import pandas as pd

pd.set_option('display.max_columns', None) # Show all columns when printing dataframes

debug = False # Set to True to enable debug mode
norm_files_dir = "normalized_files"
if not os.path.exists(norm_files_dir): # Create directory if doesn't exist
    os.makedirs(norm_files_dir)

def get_csv_path(prompt):
    while True:
        file_path = input(prompt)
        if os.path.isfile(file_path) and file_path.lower().endswith('.csv'):
            return file_path
        else:
            print(f"Error: '{file_path}' is not a valid CSV file. Please try again.")

# Normalize book dataframe
def normalize_books(df):
    # 1NF: Atomic Values, No nested relations
    # Authors not atomic, also a nested relation, so we need to split authors into a separate rows,
    #  Then create separate book_author dataframe
    df['Author'] = df['Author'].str.split(',')
    df = df.explode('Author')
    df['Author'] = df['Author'].str.strip()
    # Standardize case for Author and Title
    df['Author'] = df['Author'].str.title() 
    df['Title'] = df['Title'].str.title()


    # Issue: What if multiple authors w/ same name? For now, assume names unique.
    # Let ISBN10 be primary/foreign key.
    book_authors = df[['ISBN10','Author']].drop_duplicates().reset_index(drop=True)
    df = df.drop(columns=['Author'])
    df = df[['ISBN10', 'Title', 'Cover', 'Publisher', 'Pages']]
    df = df.drop_duplicates().reset_index(drop=True)
    
    # 2NF: No partial dependencies
    # Author should have Author_id, need to add. MAKE SURE author name is not in book_authors.
    authors = book_authors[['Author']].drop_duplicates().reset_index(drop=True)
    authors['Author_id'] = authors.index + 1
    authors = authors[['Author_id', 'Author']]

    book_authors = book_authors.merge(authors, on='Author', how='left')
    book_authors = book_authors[['Author_id','ISBN10']]

    # 3NF: No transitive dependencies
    # Relations do not depend on non-key attributes.
    # authors: Author_id -> Author
    # book_authors: Author_id, ISBN13
    # books: ISBN13 -> ISBN10, Title, Cover, Publisher, Pages

    return df, book_authors, authors

books_csv_path = get_csv_path("Enter the path to the Books CSV file: ")
borrowers_csv_path = get_csv_path("Enter the path to the Borrowers CSV file: ")

#step 2: Build dataframes for the CSV files
books_df = pd.read_csv(books_csv_path, sep='\t', encoding = 'utf-8') # books is tab-separated
borrowers_df = pd.read_csv(borrowers_csv_path, sep=',', encoding = 'utf-8') # borrowers is comma-separated

if debug:
    print("Books DataFrame:")
    print(books_df.head())
    print("\nBorrowers DataFrame:")
    print(borrowers_df.head())

# Normalize DataFrames into 1NF -> 2NF -> 3NF
# Normalized into book, book_author, borrower, loan tables
# Note: borrowers_df is already in 3NF (if we set ID0000id as primary key)
books_df, book_authors_df, authors_df = normalize_books(books_df)
borrowers_df.columns = ['Card_id', 'Ssn', 'Fname', 'Lname', 'Email', 'Address', 'City', 'State', 'Phone']

if debug:
    print("Normalized Books DataFrame:")
    print(books_df.head())
    print("\nNormalized Book Authors DataFrame:")
    print(book_authors_df.head())
    print("\nNormalized Authors DataFrame:")
    print(authors_df.head())

# Save normalized DataFrames to CSV files in normalized_files folder
books_df.to_csv(os.path.join(norm_files_dir, 'book.csv'), index=False)
book_authors_df.to_csv(os.path.join(norm_files_dir, 'book_authors.csv'), index=False)
authors_df.to_csv(os.path.join(norm_files_dir, 'authors.csv'), index=False)
borrowers_df.to_csv(os.path.join(norm_files_dir, 'borrower.csv'), index=False)