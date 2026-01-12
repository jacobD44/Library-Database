# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class Authors(models.Model):
    author_id = models.AutoField(db_column='Author_id', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='Name', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'authors'


class Book(models.Model):
    isbn = models.CharField(db_column='Isbn', primary_key=True)  # Field name made lowercase.
    title = models.CharField(db_column='Title')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'book'

class BookAuthors(models.Model):
    isbn = models.ForeignKey(Book, models.DO_NOTHING, db_column='Isbn')  # Field name made lowercase.
    author = models.ForeignKey(Authors, models.DO_NOTHING, db_column='Author_id')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'book_authors'

class BookLoans(models.Model):
    loan_id = models.AutoField(db_column='Loan_id', primary_key=True)  # Field name made lowercase.
    isbn = models.ForeignKey(Book, models.DO_NOTHING, db_column='Isbn')  # Field name made lowercase.
    card = models.ForeignKey('Borrower', models.DO_NOTHING, db_column='Card_id')  # Field name made lowercase.
    date_out = models.CharField(db_column='Date_out')  # Field name made lowercase.
    due_date = models.CharField(db_column='Due_date')  # Field name made lowercase.
    date_in = models.CharField(db_column='Date_in', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'book_loans'

class Borrower(models.Model):
    card_id = models.CharField(db_column='Card_id', primary_key=True)  # Field name made lowercase.
    bname = models.CharField(db_column='Bname', blank=True, null=True)  # Field name made lowercase.
    ssn = models.CharField(db_column='Ssn')  # Field name made lowercase.
    address = models.CharField(db_column='Address')  # Field name made lowercase.
    phone = models.CharField(db_column='Phone', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'borrower'

class Fines(models.Model):
    loan = models.OneToOneField(BookLoans, models.DO_NOTHING, db_column='Loan_id', primary_key=True)  # Field name made lowercase.
    fine_amt = models.TextField(db_column='Fine_amt')  # Field name made lowercase. This field type is a guess.
    paid = models.BooleanField(db_column='Paid')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'fines'