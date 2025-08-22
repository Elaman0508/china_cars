from django.contrib import admin
from .models import Car

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("brand", "model", "year", "category", "price", "created_at")
    list_filter = ("category", "year")
    search_fields = ("brand", "model")
