from django.contrib import admin

from finance.models import Finance


@admin.register(Finance)
class FinanceAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "join_date", "is_active")
    list_filter = ("is_active",)
    search_fields = ("user__username", "user__email", "phone")
