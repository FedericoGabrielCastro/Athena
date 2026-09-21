from django.contrib import admin

from .models import Category, Ticket


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "priority", "confidence", "engine", "created_at")
    list_filter = ("category", "priority", "engine", "corrected")
    search_fields = ("title", "body")
