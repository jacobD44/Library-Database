from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("booksearch/", views.booksearch, name="booksearch"),
    path("checkin/", views.checkin, name="checkin"),
    path("checkout/", views.checkout, name="checkout"),
    path("borrowers/", views.borrowers, name="borrowers"),
    path("fines/", views.fines, name="fines"),
]