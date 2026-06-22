from django.contrib import admin

from .models import FollowUp


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "join_date", "date_of_birth", "is_active")
    search_fields = ("user__username", "user__email", "phone")
    list_filter = ("is_active",)
