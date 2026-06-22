from django.contrib import admin

from .models import Branch, BranchManager, BranchMonthlyTarget


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "phone", "email", "is_deleted", "opening_date")
    list_filter = ("is_deleted", "state", "city")
    search_fields = ("name", "email", "phone", "city")

    def get_queryset(self, request):
        return Branch.objects.all()


@admin.register(BranchManager)
class BranchManagerAdmin(admin.ModelAdmin):
    list_display = ("user", "branch", "phone", "is_active", "join_date")
    search_fields = ("user__username", "user__email", "phone", "branch__name")
    list_filter = ("is_active", "branch")


@admin.register(BranchMonthlyTarget)
class BranchMonthlyTargetAdmin(admin.ModelAdmin):
    list_display = ("branch", "period_month", "period_year", "target_amount", "assigned_by", "updated_at")
    list_filter = ("period_year", "period_month", "branch")
    search_fields = ("branch__name",)
