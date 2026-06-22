from django.contrib import admin

from .models import Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "basic_salary", "other_salary", "total_salary", "join_date", "is_active")
    search_fields = ("user__username", "user__email", "phone")
    list_filter = ("is_active",)
