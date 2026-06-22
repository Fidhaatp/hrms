from django.contrib import admin

from marketing.models import Marketing


@admin.register(Marketing)
class MarketingAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "join_date", "is_active")
    list_filter = ("is_active",)
    search_fields = ("user__username", "user__email", "phone")
