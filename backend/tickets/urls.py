from django.urls import path

from tickets import views

urlpatterns = [
    path("categories/", views.category_list),
    path("tickets/", views.ticket_list),
    path("tickets/<int:pk>/correct/", views.ticket_correct),
    path("classify/", views.classify_preview),
    path("stats/", views.stats),
]
