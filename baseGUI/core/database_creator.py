from sqlalchemy import create_engine, inspect
from schema_definitions import metadata
import pandas as pd
import os

db_engine = create_engine('sqlite:///library.db', echo = True)

metadata.drop_all(db_engine)
metadata.create_all(db_engine)

normalization_dir = "normalized_files"

def load_to_table(file_name, table_name):
    df = pd.read_csv(os.path.join(normalization_dir, file_name))

    rename_map = {"ISBN10":"Isbn", "Author":"Name"}
    df.rename(columns=rename_map, inplace = True, errors = "ignore")

    # Build Borrower display name from first/last if needed
    if table_name == "borrower" and "Bname" not in df.columns:
        if "Fname" in df.columns and "Lname" in df.columns:
            df["Bname"] = (df["Fname"].fillna("") + " " + df["Lname"].fillna("")).str.strip()

    inspector = inspect(db_engine)
    table_columns = [col["name"] for col in inspector.get_columns(table_name)]
    df = df[[col for col in df.columns if col in table_columns]]

    df.to_sql(table_name, con = db_engine, if_exists = 'append', index = False)
    print(f"Inserted {len(df)} rows into {table_name}\n")

load_to_table("book.csv", "book")
load_to_table("authors.csv", "authors")
load_to_table("book_authors.csv", "book_authors")
load_to_table("borrower.csv", "borrower")

print("All data has been uploaded to tables")
