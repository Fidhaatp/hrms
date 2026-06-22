from django.contrib import admin

from .models import (
    Announcement,
    AttendanceRecord,
    Award,
    CaseProcessingLog,
    ClientCase,
    LeadDocument,
    EmployeeCompliance,
    EmployeeIncentive,
    EmployeeTarget,
    Lead,
    LeadLostReasonType,
    LeadRoadmapEntry,
    LeadProcedureStep,
    LeadStaffStatusHistory,
    LeadService,
    LeadServiceProcedure,
    LeadServiceDocument,
    LeadServiceDocumentType,
    LeadSource,
    LeadStatus,
    LeaveCategory,
    LeaveRequest,
    LeaveType,
    MarketingCampaign,
    RecruitmentRequest,
    UserProfile,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "user_type", "phone", "has_photo", "created_at")

    @admin.display(boolean=True, description="Photo")
    def has_photo(self, obj):
        return bool(obj.profile_picture)

    list_filter = ("user_type",)
    search_fields = ("user__username", "user__email", "phone")


@admin.register(LeaveCategory)
class LeaveCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "days_per_year", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(LeadService)
class LeadServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "sort_order", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(LeadServiceDocumentType)
class LeadServiceDocumentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "service", "code", "is_required", "sort_order", "is_active")
    list_filter = ("is_active", "is_required", "service")
    search_fields = ("name", "code", "service__name")


@admin.register(LeadServiceProcedure)
class LeadServiceProcedureAdmin(admin.ModelAdmin):
    list_display = ("name", "service", "code", "sort_order", "is_active")
    list_filter = ("is_active", "service")
    search_fields = ("name", "code", "service__name")


@admin.register(LeadServiceDocument)
class LeadServiceDocumentAdmin(admin.ModelAdmin):
    list_display = ("lead", "document_type", "uploaded_by", "created_at")
    raw_id_fields = ("lead", "uploaded_by", "document_type")


@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "sort_order", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(LeadStatus)
class LeadStatusAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "badge_style",
        "is_default",
        "counts_as_converted",
        "sort_order",
        "is_active",
    )
    list_filter = ("is_active", "badge_style", "counts_as_converted", "is_default")
    search_fields = ("name", "code")


class LeadRoadmapEntryInline(admin.TabularInline):
    model = LeadRoadmapEntry
    extra = 0
    readonly_fields = ("created_at",)


class LeadStaffStatusHistoryInline(admin.TabularInline):
    model = LeadStaffStatusHistory
    extra = 0
    readonly_fields = ("from_status_name", "to_status", "lost_reason_type", "note", "created_by", "created_at")
    can_delete = False


class LeadProcedureStepInline(admin.TabularInline):
    model = LeadProcedureStep
    extra = 0
    readonly_fields = (
        "procedure",
        "status",
        "document",
        "followup_note",
        "submitted_by",
        "review_note",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    )
    can_delete = False


@admin.register(LeadLostReasonType)
class LeadLostReasonTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "lead_id",
        "name",
        "company",
        "backoffice_status",
        "staff_status",
        "followup_status",
        "source",
        "service",
        "service_documents_zip",
        "pipeline_stage",
        "branch",
        "created_by",
        "created_at",
    )
    list_filter = ("backoffice_status", "followup_status", "source", "pipeline_stage", "branch")
    search_fields = ("name", "company", "phone", "email", "takhlees_id", "passport_no", "eid_no")
    inlines = [LeadStaffStatusHistoryInline, LeadProcedureStepInline, LeadRoadmapEntryInline]
    raw_id_fields = ("created_by", "backoffice_checked_by", "followup_assigned_to")

    @admin.display(description="ID")
    def lead_id(self, obj):
        return obj.display_id


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "leave_category",
        "leave_type",
        "start_date",
        "end_date",
        "days_display",
        "workflow_stage",
        "status",
        "created_at",
    )
    list_filter = ("status", "workflow_stage", "leave_category", "leave_type")
    search_fields = ("user__username", "reason")
    raw_id_fields = ("user", "manager_reviewed_by", "hr_reviewed_by")

    @admin.display(description="Days")
    def days_display(self, obj):
        return obj.days_count


admin.site.register(EmployeeCompliance)
admin.site.register(AttendanceRecord)
admin.site.register(EmployeeTarget)
admin.site.register(EmployeeIncentive)
admin.site.register(Announcement)
admin.site.register(Award)
admin.site.register(RecruitmentRequest)
admin.site.register(MarketingCampaign)
admin.site.register(ClientCase)


@admin.register(LeadDocument)
class LeadDocumentAdmin(admin.ModelAdmin):
    list_display = ("lead", "doc_type", "title", "uploaded_by", "created_at")
    list_filter = ("doc_type",)
    raw_id_fields = ("lead", "uploaded_by")
