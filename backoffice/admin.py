from django.contrib import admin

from .models import BackOffice


@admin.register(BackOffice)
class BackOfficeAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "branch", "is_backoffice_head", "join_date", "is_active")
    search_fields = ("user__username", "user__email", "phone")
    list_filter = ("is_active", "is_backoffice_head")
