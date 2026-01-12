CREATE DATABASE libraryDB_unnormalized;
USE libraryDB_unnormalized;
-- Create books table
CREATE TABLE books (
    ISBN10 VARCHAR(10),
    ISBN13 VARCHAR(13),
    Title VARCHAR(255),
    Author VARCHAR(255),
    Cover VARCHAR(255),
    Publisher VARCHAR(255),
    Pages INT
);
-- Create borrowers table
CREATE TABLE borrowers (
    ID0000id VARCHAR(8),
    ssn VARCHAR(11),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    phone VARCHAR(15)
);

-- Load data from books.csv into the books table
LOAD DATA LOCAL INFILE 'C:\Users\yuoso\Desktop\CS 4347 Database Systems\project\books.csv'
INTO TABLE books
FIELDS TERMINATED BY '	'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(ISBN10, ISBN13, Title, Author, Cover, Publisher, Pages);

-- Load data from borrowers.csv into the borrowers table
LOAD DATA LOCAL INFILE 'C:\Users\yuoso\Desktop\CS 4347 Database Systems\project\borrowers.csv'
INTO TABLE borrowers
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(ID0000id,ssn,first_name,last_name,email,address,city,state,phone);

-- Verify data loading
SELECT * FROM books LIMIT 10;
SELECT * FROM borrowers LIMIT 10;