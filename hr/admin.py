from django.contrib import admin

from .models import Hr


@admin.register(Hr)
class HrAdmin(admin.ModelAdmin):
    list_display = ("username", "phone", "join_date", "date_of_birth")
    search_fields = ("username__username", "phone")
