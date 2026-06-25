from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """Common profile for all portal users — links Django User to an app role."""

    class UserType(models.TextChoices):
        ADMIN = "admin", "Admin"
        HR = "hr", "HR Manager"
        FINANCE = "finance", "Finance Manager"
        MARKETING = "marketing", "Marketing Manager"
        STAFF = "staff", "Branch Staff"
        BACKOFFICE = "backoffice", "Back Office Staff"
        BRANCH = "branch", "Branch Manager"
        BRANCH_ACCOUNTANT = "branch_accountant", "Branch Accountant"
        FOLLOWUP = "followup", "Follow Up Staff"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    user_type = models.CharField(max_length=20, choices=UserType.choices)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(
        upload_to="profiles/%Y/%m/",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User profile"
        verbose_name_plural = "User profiles"

    def __str__(self):
        return f"{self.user.get_username()} ({self.get_user_type_display()})"

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.get_username()

    @property
    def initials(self):
        from core.profile_utils import get_initials

        return get_initials(self.display_name)

    def get_dashboard_url_name(self):
        routes = {
            self.UserType.ADMIN: "admin_portal:dashboard",
            self.UserType.HR: "hr:dashboard",
            self.UserType.FINANCE: "finance:index",
            self.UserType.MARKETING: "marketing:index",
            self.UserType.STAFF: "staff:index",
            self.UserType.BACKOFFICE: "backoffice:index",
            self.UserType.BRANCH: "branch:index",
            self.UserType.BRANCH_ACCOUNTANT: "accountant:index",
            self.UserType.FOLLOWUP: "followup:index",
        }
        return routes.get(self.user_type, "core:home")

    def get_profile_url_name(self):
        routes = {
            self.UserType.ADMIN: "admin_portal:profile",
            self.UserType.HR: "hr:profile",
            self.UserType.FINANCE: "finance:profile",
            self.UserType.MARKETING: "marketing:profile",
            self.UserType.STAFF: "staff:profile",
            self.UserType.BACKOFFICE: "backoffice:profile",
            self.UserType.BRANCH: "branch:profile",
            self.UserType.BRANCH_ACCOUNTANT: "accountant:profile",
            self.UserType.FOLLOWUP: "followup:profile",
        }
        return routes.get(self.user_type, self.get_dashboard_url_name())


class LeaveCategory(models.Model):
    """Leave entitlement bucket — e.g. yearly leave with days per year."""

    YEARLY_CODE = "yearly"

    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True)
    days_per_year = models.PositiveIntegerField(
        default=30,
        help_text="Allowed days per calendar year (30 = one month).",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Leave category"
        verbose_name_plural = "Leave categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class LeaveType(models.Model):
    """Kind of leave — sick, casual, etc. (HR adds these; not tied to day counts)."""

    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Leave type"
        verbose_name_plural = "Leave types"
        ordering = ["name"]

    def __str__(self):
        return self.name


class LeaveRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class WorkflowStage(models.TextChoices):
        PENDING_MANAGER = "pending_manager", "Pending Branch Manager"
        PENDING_HR = "pending_hr", "Pending HR"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leave_requests",
    )
    leave_category = models.ForeignKey(
        LeaveCategory,
        on_delete=models.PROTECT,
        related_name="leave_requests",
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="leave_requests",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    workflow_stage = models.CharField(
        max_length=20,
        choices=WorkflowStage.choices,
        default=WorkflowStage.PENDING_MANAGER,
    )
    manager_reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leave_manager_reviews",
    )
    manager_reviewed_at = models.DateTimeField(null=True, blank=True)
    manager_note = models.TextField(blank=True)
    hr_reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leave_hr_reviews",
    )
    hr_reviewed_at = models.DateTimeField(null=True, blank=True)
    hr_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.user.get_username()} — {self.leave_type.name} / "
            f"{self.leave_category.name} ({self.start_date} to {self.end_date})"
        )

    @property
    def days_count(self):
        return (self.end_date - self.start_date).days + 1

    def days_in_year(self, year):
        from datetime import date

        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        start = max(self.start_date, year_start)
        end = min(self.end_date, year_end)
        if start > end:
            return 0
        return (end - start).days + 1

    @property
    def workflow_label(self):
        return self.get_workflow_stage_display()

    def approve_by_manager(self, reviewer, note=""):
        from django.utils import timezone

        self.workflow_stage = self.WorkflowStage.PENDING_HR
        self.manager_reviewed_by = reviewer
        self.manager_reviewed_at = timezone.now()
        self.manager_note = note
        self.save(
            update_fields=[
                "workflow_stage",
                "manager_reviewed_by",
                "manager_reviewed_at",
                "manager_note",
                "updated_at",
            ]
        )

    def reject_by_manager(self, reviewer, note=""):
        from django.utils import timezone

        self.workflow_stage = self.WorkflowStage.REJECTED
        self.status = self.Status.REJECTED
        self.manager_reviewed_by = reviewer
        self.manager_reviewed_at = timezone.now()
        self.manager_note = note
        self.save(
            update_fields=[
                "workflow_stage",
                "status",
                "manager_reviewed_by",
                "manager_reviewed_at",
                "manager_note",
                "updated_at",
            ]
        )

    def approve_by_hr(self, reviewer, note=""):
        from django.utils import timezone

        self.workflow_stage = self.WorkflowStage.APPROVED
        self.status = self.Status.APPROVED
        self.hr_reviewed_by = reviewer
        self.hr_reviewed_at = timezone.now()
        self.hr_note = note
        self.save(
            update_fields=[
                "workflow_stage",
                "status",
                "hr_reviewed_by",
                "hr_reviewed_at",
                "hr_note",
                "updated_at",
            ]
        )

    def reject_by_hr(self, reviewer, note=""):
        from django.utils import timezone

        self.workflow_stage = self.WorkflowStage.REJECTED
        self.status = self.Status.REJECTED
        self.hr_reviewed_by = reviewer
        self.hr_reviewed_at = timezone.now()
        self.hr_note = note
        self.save(
            update_fields=[
                "workflow_stage",
                "status",
                "hr_reviewed_by",
                "hr_reviewed_at",
                "hr_note",
                "updated_at",
            ]
        )


class EmployeeCompliance(models.Model):
    """Visa, insurance, and contract tracking for HR dashboard."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="compliance",
    )
    visa_expiry = models.DateField(null=True, blank=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    contract_end = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Employee compliance records"

    def __str__(self):
        return f"Compliance — {self.user.get_username()}"


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LEAVE = "leave", "On Leave"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    check_in = models.TimeField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date"]
        unique_together = [("user", "date")]

    def __str__(self):
        return f"{self.user.get_username()} — {self.date} ({self.get_status_display()})"


class EmployeeTarget(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="targets",
    )
    period_month = models.PositiveSmallIntegerField()
    period_year = models.PositiveSmallIntegerField()
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    achieved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["-period_year", "-period_month"]
        unique_together = [("user", "period_month", "period_year")]

    @property
    def achievement_percent(self):
        if not self.target_amount:
            return 0
        return round(float(self.achieved_amount) / float(self.target_amount) * 100, 1)


class EmployeeIncentive(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="incentives",
    )
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-year", "-month"]


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    target_roles = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated role keys (staff, branch, hr, …). Empty = all.",
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="announcements_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Award(models.Model):
    class AwardType(models.TextChoices):
        EMPLOYEE_OF_MONTH = "employee_of_month", "Employee of the Month"
        BRANCH_OF_MONTH = "branch_of_month", "Branch of the Month"

    award_type = models.CharField(max_length=30, choices=AwardType.choices)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    winner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="awards_won",
    )
    winner_branch = models.ForeignKey(
        "branch.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="awards_won",
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-year", "-month"]


class RecruitmentRequest(models.Model):
    class Status(models.TextChoices):
        BRANCH_REQUEST = "branch_request", "Branch Request"
        HR_REVIEW = "hr_review", "HR Review"
        INTERVIEW = "interview", "Interview"
        JOINING = "joining", "Joining"
        CLOSED = "closed", "Closed"

    branch = models.ForeignKey(
        "branch.Branch",
        on_delete=models.CASCADE,
        related_name="recruitment_requests",
    )
    position_title = models.CharField(max_length=255)
    headcount = models.PositiveSmallIntegerField(default=1)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.BRANCH_REQUEST,
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recruitment_requests_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class LeadSource(models.Model):
    """Where a lead came from — HR manages options (Website, Referral, etc.)."""

    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lead source"
        verbose_name_plural = "Lead sources"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class LeadService(models.Model):
    """Service type for a lead — HR manages options (Visa, PRO, etc.)."""

    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lead service"
        verbose_name_plural = "Lead services"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class LeadServiceDocumentType(models.Model):
    """Required/optional document upload for a lead service — configured by HR."""

    service = models.ForeignKey(
        LeadService,
        on_delete=models.CASCADE,
        related_name="document_types",
    )
    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=50, blank=True)
    help_text = models.CharField(max_length=255, blank=True)
    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lead service document type"
        verbose_name_plural = "Lead service document types"
        ordering = ["sort_order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["service", "code"],
                name="uniq_lead_service_doc_type_code",
            ),
        ]

    def __str__(self):
        return f"{self.service.name} — {self.name}"


class LeadServiceProcedure(models.Model):
    """Operational procedure template for a lead service (dynamic per service)."""

    service = models.ForeignKey(
        LeadService,
        on_delete=models.CASCADE,
        related_name="procedures",
    )
    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lead service procedure"
        verbose_name_plural = "Lead service procedures"
        ordering = ["sort_order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["service", "code"],
                name="uniq_lead_service_procedure_code",
            ),
        ]

    def __str__(self):
        return f"{self.service.name} — {self.name}"


class LeadStatus(models.Model):
    """Follow-up pipeline status — HR manages options (New, Contacted, etc.)."""

    class BadgeStyle(models.TextChoices):
        NEW = "new", "New"
        ACTIVE = "active", "Active"
        PENDING = "pending", "Pending"
        WON = "won", "Won"
        CLOSED = "closed", "Closed"

    NEW_CODE = "new"
    CONTACTED_CODE = "contacted"
    QUALIFIED_CODE = "qualified"
    CONVERTED_CODE = "converted"
    LOST_CODE = "lost"

    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True)
    badge_style = models.CharField(
        max_length=20,
        choices=BadgeStyle.choices,
        default=BadgeStyle.NEW,
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Applied automatically when staff adds a new lead.",
    )
    counts_as_converted = models.BooleanField(
        default=False,
        help_text="Include in conversion-rate metrics.",
    )
    sends_to_followup = models.BooleanField(
        default=False,
        help_text="When staff sets this status, the lead is sent to the follow-up team.",
    )
    sends_to_backoffice = models.BooleanField(
        default=False,
        help_text="When follow-up sets this status, the lead is sent to back office for processing.",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lead status"
        verbose_name_plural = "Lead statuses"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class LeadLostReasonType(models.Model):
    """Why a lead was marked Lost — HR manages options; staff picks one when setting Lost."""

    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=50, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lost reason"
        verbose_name_plural = "Lost reasons"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Lead(models.Model):
    """Lead pipeline: Staff → Back office check → Follow-up → Branch roadmap."""

    class BackofficeStatus(models.TextChoices):
        PENDING = "pending", "Pending check"
        VERIFIED = "verified", "Correct lead"
        REJECTED = "rejected", "Not correct"

    class PipelineStage(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        FOLLOWUP = "followup", "With follow-up"
        BRANCH = "branch", "With branch"

    class StaffStage(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUALIFIED = "qualified", "Qualified"
        CONVERTED = "converted", "Converted"
        LOST = "lost", "Lost"

    class HandoverStatus(models.TextChoices):
        PENDING = "pending", "Not handed over"
        HANDED_OVER = "handed_over", "Handed over"

    class ClientType(models.TextChoices):
        COMPANY = "company", "Company"
        INDIVIDUAL = "individual", "Individual"

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="leads_created",
    )
    name = models.CharField(max_length=255)
    company = models.CharField(
        max_length=20,
        choices=ClientType.choices,
        default=ClientType.COMPANY,
    )
    phone = models.CharField(max_length=30, unique=True)
    email = models.EmailField(blank=True, null=True, unique=True)
    source = models.ForeignKey(
        LeadSource,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="leads",
    )
    service = models.ForeignKey(
        LeadService,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="leads",
    )
    service_documents_zip = models.FileField(
        "Service documents (ZIP)",
        upload_to="leads/service_zips/%Y/%m/",
        blank=True,
    )
    payment_verified = models.BooleanField(
        default=False,
        help_text="Staff confirmed customer payment before converting the lead.",
    )
    payment_screenshot = models.ImageField(
        "Payment screenshot",
        upload_to="leads/payment_screenshots/%Y/%m/",
        blank=True,
    )
    service_zip_verified = models.BooleanField(
        default=False,
        help_text="Follow-up confirmed staff ZIP when no extracted files are available.",
    )
    sent_to_followup_at = models.DateTimeField(null=True, blank=True)
    sent_to_backoffice_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    takhlees_id = models.CharField("Takhlees ID", max_length=64, blank=True)
    passport_no = models.CharField("Passport No", max_length=64, blank=True)
    eid_no = models.CharField("EID No", max_length=64, blank=True)

    backoffice_status = models.CharField(
        max_length=20,
        choices=BackofficeStatus.choices,
        default=BackofficeStatus.PENDING,
    )
    backoffice_checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads_backoffice_checked",
    )
    backoffice_checked_at = models.DateTimeField(null=True, blank=True)
    backoffice_notes = models.TextField(blank=True)

    staff_status = models.ForeignKey(
        LeadStatus,
        on_delete=models.PROTECT,
        related_name="leads_staff_status",
        help_text="Status set by branch staff on their portal.",
    )
    followup_status = models.ForeignKey(
        LeadStatus,
        on_delete=models.PROTECT,
        related_name="leads_followup_status",
        null=True,
        blank=True,
        help_text="Status set by the follow-up team (separate from staff status).",
    )
    followup_assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads_followup_assigned",
    )
    pipeline_stage = models.CharField(
        max_length=20,
        choices=PipelineStage.choices,
        default=PipelineStage.SUBMITTED,
    )
    branch = models.ForeignKey(
        "branch.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
    )
    next_followup_date = models.DateField(null=True, blank=True)
    service_expire_date = models.DateField(
        null=True,
        blank=True,
        help_text="Service expiry date set by follow-up; shown on portal calendars.",
    )

    doc_passport_collected = models.BooleanField(
        default=False,
        help_text="Follow-up collected passport copy.",
    )
    doc_certificates_collected = models.BooleanField(
        default=False,
        help_text="Follow-up collected certificates.",
    )
    doc_photos_collected = models.BooleanField(
        default=False,
        help_text="Follow-up collected photos.",
    )
    doc_collection_notes = models.TextField(
        blank=True,
        help_text="Missing documents or collection notes from follow-up.",
    )

    staff_stage = models.CharField(
        max_length=20,
        choices=StaffStage.choices,
        default=StaffStage.NEW,
    )
    staff_conversion_note = models.TextField(blank=True)
    lost_reason_type = models.ForeignKey(
        LeadLostReasonType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
        help_text="Reason type when staff marks the lead as Lost.",
    )
    handover_status = models.CharField(
        max_length=20,
        choices=HandoverStatus.choices,
        default=HandoverStatus.PENDING,
    )
    handover_note = models.TextField(blank=True)
    handed_over_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.display_id} — {self.name}"

    @property
    def display_id(self):
        return f"L-{self.pk:04d}"

    @property
    def initials(self):
        from core.profile_utils import get_initials

        return get_initials(self.name)

    @property
    def staff_zip_documents_checked(self):
        """True when follow-up checked every file from the staff ZIP."""
        extracted = list(self.extracted_documents.all())
        if extracted:
            return all(doc.followup_checked for doc in extracted)
        if self.service_documents_zip:
            return self.service_zip_verified
        return False

    @property
    def service_zip_filename(self):
        if not self.service_documents_zip:
            return ""
        return self.service_documents_zip.name.rsplit("/", 1)[-1]

    @property
    def payment_confirmed(self):
        return bool(self.payment_verified and self.payment_screenshot)

    @property
    def payment_screenshot_filename(self):
        if not self.payment_screenshot:
            return ""
        return self.payment_screenshot.name.rsplit("/", 1)[-1]

    def staff_status_history_payload(self, limit=12):
        rows = []
        for entry in self.staff_status_history.select_related(
            "to_status", "lost_reason_type", "created_by"
        ).order_by("-created_at")[:limit]:
            rows.append(
                {
                    "from_status": entry.from_status_name or "—",
                    "to_status": entry.to_status.name,
                    "reason": entry.lost_reason_type.name if entry.lost_reason_type_id else "",
                    "note": entry.note,
                    "by": entry.created_by.get_username() if entry.created_by_id else "System",
                    "at": entry.created_at.strftime("%d %b %Y, %I:%M %p"),
                }
            )
        return rows

    def procedure_steps_payload(self):
        templates = list(
            self.service.procedures.filter(is_active=True).order_by("sort_order", "name")
        ) if self.service_id else []
        step_map = {
            step.procedure_id: step
            for step in self.procedure_steps.select_related("procedure", "reviewed_by")
        }
        rows = []
        for idx, template in enumerate(templates, start=1):
            step = step_map.get(template.pk)
            rows.append(
                {
                    "procedure_id": template.pk,
                    "order": idx,
                    "name": template.name,
                    "status": step.status if step else "not_started",
                    "status_label": step.get_status_display() if step else "Not started",
                    "step_id": step.pk if step else None,
                    "doc_name": step.document_filename if step and step.document else "",
                    "doc_url": step.document.url if step and step.document else "",
                    "backoffice_doc_name": step.backoffice_document_filename if step and step.backoffice_document else "",
                    "backoffice_doc_url": step.backoffice_document.url if step and step.backoffice_document else "",
                    "followup_note": step.followup_note if step else "",
                    "review_note": step.review_note if step else "",
                    "reviewed_by": step.reviewed_by.get_username() if step and step.reviewed_by_id else "",
                    "can_submit_now": False,
                }
            )
        # Determine the next actionable step: first non-approved.
        for row in rows:
            if row["status"] != LeadProcedureStep.Status.APPROVED:
                row["can_submit_now"] = row["status"] != LeadProcedureStep.Status.PENDING
                break
        return rows

    def _active_service_procedure_templates(self):
        if not self.service_id:
            return []
        return list(self.service.procedures.filter(is_active=True).order_by("sort_order", "name"))

    def procedure_lead_status(self):
        """Overall lead procedure progress: completed only when every step is approved."""
        templates = self._active_service_procedure_templates()
        if not templates:
            return None
        step_map = {step.procedure_id: step for step in self.procedure_steps.all()}
        for template in templates:
            step = step_map.get(template.pk)
            if not step or step.status != LeadProcedureStep.Status.APPROVED:
                return "pending"
        return "completed"

    @property
    def procedure_lead_status_label(self):
        status = self.procedure_lead_status()
        if status is None:
            return "—"
        return "Completed" if status == "completed" else "Pending"

    @property
    def procedure_lead_status_badge(self):
        status = self.procedure_lead_status()
        if status == "completed":
            return "won"
        if status == "pending":
            return "pending"
        return "new"

    def procedure_progress_counts(self):
        """Approved count, total steps, and the current non-approved procedure."""
        templates = self._active_service_procedure_templates()
        if not templates:
            return {
                "total": 0,
                "approved": 0,
                "current_order": 0,
                "current_template": None,
                "current_step": None,
            }
        step_map = {step.procedure_id: step for step in self.procedure_steps.all()}
        approved = 0
        current_order = 0
        current_template = None
        current_step = None
        for idx, template in enumerate(templates, start=1):
            step = step_map.get(template.pk)
            if step and step.status == LeadProcedureStep.Status.APPROVED:
                approved += 1
                continue
            current_order = idx
            current_template = template
            current_step = step
            break
        if current_template is None:
            current_order = len(templates)
            current_template = templates[-1]
            current_step = step_map.get(current_template.pk)
        return {
            "total": len(templates),
            "approved": approved,
            "current_order": current_order,
            "current_template": current_template,
            "current_step": current_step,
        }

    @property
    def active_procedure_status(self):
        """Current procedure step with progress for list tables."""
        templates = self._active_service_procedure_templates()
        if not templates:
            return {
                "name": "—",
                "label": "—",
                "badge": "new",
                "hint": "",
                "progress": "",
                "step_label": "",
                "stage": "—",
            }

        counts = self.procedure_progress_counts()
        total = counts["total"]
        approved = counts["approved"]
        progress = f"{approved} of {total} approved"
        step_label = f"Step {counts['current_order']} of {total}"

        if approved == total:
            last = templates[-1]
            return {
                "name": last.name,
                "label": "Completed",
                "badge": "won",
                "hint": "",
                "progress": progress,
                "step_label": f"Step {total} of {total}",
                "stage": f"Step {total} of {total}",
            }

        template = counts["current_template"]
        step = counts["current_step"]
        name = template.name
        base = {
            "name": name,
            "progress": progress,
            "step_label": step_label,
            "stage": step_label,
        }

        if not step:
            if approved > 0:
                return {
                    **base,
                    "label": "Awaiting follow-up",
                    "badge": "pending",
                    "hint": "",
                }
            return {
                **base,
                "label": "Not started",
                "badge": "new",
                "hint": "",
            }
        if step.status == LeadProcedureStep.Status.PENDING:
            return {
                **base,
                "label": "Pending review",
                "badge": "pending",
                "hint": "",
            }
        if step.status == LeadProcedureStep.Status.REJECTED:
            return {
                **base,
                "label": "Rejected",
                "badge": "closed",
                "hint": "",
            }
        return {
            **base,
            "label": "In progress",
            "badge": "pending",
            "hint": "",
        }

    @property
    def status_badge(self):
        if self.backoffice_status == self.BackofficeStatus.REJECTED:
            return "closed"
        if self.backoffice_status == self.BackofficeStatus.PENDING:
            return "pending"
        if self.followup_status_id:
            return self.followup_status.badge_style
        return LeadStatus.BadgeStyle.NEW

    @property
    def team_status_display(self):
        """Which team owns the lead — same label across staff, HR, back office, branch."""
        if self.backoffice_status == self.BackofficeStatus.REJECTED:
            return "Not correct"
        if self.backoffice_status == self.BackofficeStatus.PENDING:
            return "Pending check"
        if self.pipeline_stage == self.PipelineStage.BRANCH:
            return "At branch"
        return "Follow up"

    @property
    def team_status_badge(self):
        if self.backoffice_status == self.BackofficeStatus.REJECTED:
            return "closed"
        if self.backoffice_status == self.BackofficeStatus.PENDING:
            return "pending"
        if self.pipeline_stage == self.PipelineStage.BRANCH:
            return "won"
        return "active"

    @property
    def followup_queue_display(self):
        """Follow-up portal: handoff stage (not the same as ZIP doc check)."""
        if self.backoffice_status == self.BackofficeStatus.REJECTED:
            return "Rejected by back office"
        if self.sent_to_backoffice_at:
            if self.backoffice_status == self.BackofficeStatus.PENDING:
                return "Sent to back office"
            if self.backoffice_status == self.BackofficeStatus.VERIFIED:
                return "Back office verified"
        if self.service_documents_zip and not self.staff_zip_documents_checked:
            return "Check documents"
        return "With follow-up"

    @property
    def followup_queue_badge(self):
        if self.backoffice_status == self.BackofficeStatus.REJECTED:
            return "closed"
        if self.sent_to_backoffice_at:
            if self.backoffice_status == self.BackofficeStatus.PENDING:
                return "won"
            return "won"
        if self.service_documents_zip and not self.staff_zip_documents_checked:
            return "pending"
        return "active"

    @property
    def service_expire_chip_style(self):
        """CSS modifier for service expiry chip: unset, expired, soon, upcoming, ok."""
        if not self.service_expire_date:
            return "unset"
        from django.utils import timezone

        delta = (self.service_expire_date - timezone.localdate()).days
        if delta < 0:
            return "expired"
        if delta <= 7:
            return "soon"
        if delta <= 30:
            return "upcoming"
        return "ok"

    @property
    def service_expire_chip_hint(self):
        if not self.service_expire_date:
            return ""
        from django.utils import timezone

        delta = (self.service_expire_date - timezone.localdate()).days
        if delta < 0:
            days = abs(delta)
            return f"Expired {days} day{'s' if days != 1 else ''} ago"
        if delta == 0:
            return "Expires today"
        if delta == 1:
            return "Expires tomorrow"
        if delta <= 7:
            return f"In {delta} days"
        return ""

    @property
    def staff_status_label(self):
        if self.backoffice_status == self.BackofficeStatus.REJECTED:
            return "Not correct — rejected"
        if self.handover_status == self.HandoverStatus.HANDED_OVER:
            return f"Handed over — {self.get_staff_stage_display()}"
        if self.backoffice_status == self.BackofficeStatus.PENDING:
            return f"{self.get_staff_stage_display()} · Pending BO check"
        return self.get_staff_stage_display()

    @property
    def staff_stage_badge(self):
        mapping = {
            self.StaffStage.NEW: "new",
            self.StaffStage.CONTACTED: "active",
            self.StaffStage.QUALIFIED: "pending",
            self.StaffStage.CONVERTED: "won",
            self.StaffStage.LOST: "closed",
        }
        return mapping.get(self.staff_stage, "new")

    @property
    def can_staff_handover(self):
        return (
            self.backoffice_status != self.BackofficeStatus.REJECTED
            and self.handover_status == self.HandoverStatus.PENDING
            and self.staff_stage in (self.StaffStage.QUALIFIED, self.StaffStage.CONVERTED)
        )

    @property
    def staff_can_edit_details(self):
        """Staff may update lead details only before Converted / sent to follow-up."""
        if self.sent_to_followup_at:
            return False
        if self.staff_stage == self.StaffStage.CONVERTED:
            return False
        if self.staff_status_id and self.staff_status.code == LeadStatus.CONVERTED_CODE:
            return False
        return True

    def staff_update_conversion(self, user, stage, note=""):
        from core.lead_utils import get_lead_status_by_code

        stage_to_code = {
            self.StaffStage.CONVERTED: LeadStatus.CONVERTED_CODE,
            self.StaffStage.QUALIFIED: LeadStatus.QUALIFIED_CODE,
            self.StaffStage.CONTACTED: LeadStatus.CONTACTED_CODE,
            self.StaffStage.LOST: LeadStatus.LOST_CODE,
        }
        self.staff_stage = stage
        self.staff_conversion_note = note
        status_code = stage_to_code.get(stage)
        if status_code:
            self.staff_status = get_lead_status_by_code(status_code)
        self.save(
            update_fields=[
                "staff_stage",
                "staff_conversion_note",
                "staff_status",
                "updated_at",
            ]
        )
        self.roadmap_entries.create(
            created_by=user,
            title=f"Staff conversion: {self.get_staff_stage_display()}",
            note=note or f"Lead stage updated to {self.get_staff_stage_display()}.",
        )

    def staff_handover_client(self, user, note=""):
        from django.utils import timezone

        if not self.can_staff_handover:
            raise ValueError("Lead must be Qualified or Converted before handover.")
        self.handover_status = self.HandoverStatus.HANDED_OVER
        self.handover_note = note
        self.handed_over_at = timezone.now()
        if self.backoffice_status == self.BackofficeStatus.VERIFIED:
            from core.lead_utils import get_lead_status_by_code

            self.pipeline_stage = self.PipelineStage.FOLLOWUP
            if self.followup_status and self.followup_status.code == LeadStatus.NEW_CODE:
                self.followup_status = get_lead_status_by_code(LeadStatus.CONTACTED_CODE)
            elif not self.followup_status_id:
                from core.lead_utils import get_followup_queue_default_status

                self.followup_status = get_followup_queue_default_status()
        self.save(
            update_fields=[
                "handover_status",
                "handover_note",
                "handed_over_at",
                "pipeline_stage",
                "followup_status",
                "updated_at",
            ]
        )
        self.roadmap_entries.create(
            created_by=user,
            title="Client handed over",
            note=note or "Staff handed over client to follow-up pipeline.",
        )

    def mark_backoffice_verified(self, user, notes=""):
        from django.utils import timezone

        from core.lead_utils import get_creator_branch

        self.backoffice_status = self.BackofficeStatus.VERIFIED
        self.backoffice_checked_by = user
        self.backoffice_checked_at = timezone.now()
        self.backoffice_notes = notes
        self.pipeline_stage = self.PipelineStage.FOLLOWUP
        if not self.branch_id:
            creator_branch = get_creator_branch(self.created_by)
            if creator_branch:
                self.branch = creator_branch
        self.save(
            update_fields=[
                "backoffice_status",
                "backoffice_checked_by",
                "backoffice_checked_at",
                "backoffice_notes",
                "pipeline_stage",
                "branch",
                "updated_at",
            ]
        )
        self.roadmap_entries.create(
            created_by=user,
            title="Back office verified",
            note=notes or "Lead marked as correct.",
        )

    def mark_backoffice_rejected(self, user, notes=""):
        from django.utils import timezone

        self.backoffice_status = self.BackofficeStatus.REJECTED
        self.backoffice_checked_by = user
        self.backoffice_checked_at = timezone.now()
        self.backoffice_notes = notes
        self.save(
            update_fields=[
                "backoffice_status",
                "backoffice_checked_by",
                "backoffice_checked_at",
                "backoffice_notes",
                "updated_at",
            ]
        )
        self.roadmap_entries.create(
            created_by=user,
            title="Back office — not correct",
            note=notes or "Lead rejected by back office.",
        )

    @property
    def primary_case(self):
        return self.cases.order_by("-updated_at").first()

    def sync_document_collection_flags(self):
        """Align checklist flags with uploaded files."""
        types = set(self.documents.values_list("doc_type", flat=True))
        self.doc_passport_collected = LeadDocument.DocType.PASSPORT in types
        self.doc_certificates_collected = LeadDocument.DocType.CERTIFICATE in types
        self.doc_photos_collected = LeadDocument.DocType.PHOTO in types
        self.save(
            update_fields=[
                "doc_passport_collected",
                "doc_certificates_collected",
                "doc_photos_collected",
                "updated_at",
            ]
        )


class LeadServiceDocument(models.Model):
    """Document uploaded when staff adds a lead for a specific service."""

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="service_documents",
    )
    document_type = models.ForeignKey(
        LeadServiceDocumentType,
        on_delete=models.PROTECT,
        related_name="uploads",
    )
    file = models.FileField(upload_to="leads/service_docs/%Y/%m/")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_service_documents_uploaded",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document_type__sort_order", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["lead", "document_type"],
                name="uniq_lead_service_document_type",
            ),
        ]

    def __str__(self):
        return f"{self.lead.display_id} — {self.document_type.name}"


class LeadExtractedDocument(models.Model):
    """File extracted from staff-uploaded service ZIP for follow-up review."""

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="extracted_documents",
    )
    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="leads/extracted/%Y/%m/")
    followup_checked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["original_name", "created_at"]

    def __str__(self):
        return f"{self.lead.display_id} — {self.original_name}"


class LeadDocument(models.Model):
    """Customer documents uploaded by follow-up (seen by back office for case processing)."""

    class DocType(models.TextChoices):
        PASSPORT = "passport", "Passport copy"
        CERTIFICATE = "certificate", "Certificate"
        PHOTO = "photo", "Photo"
        OTHER = "other", "Other"

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    doc_type = models.CharField(max_length=20, choices=DocType.choices)
    file = models.FileField(upload_to="leads/documents/%Y/%m/")
    title = models.CharField(max_length=120, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="lead_documents_uploaded",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.lead.display_id} — {self.get_doc_type_display()}"

    @property
    def display_name(self):
        return self.title or self.get_doc_type_display()


class LeadRoadmapEntry(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="roadmap_entries")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="lead_roadmap_entries",
    )
    title = models.CharField(max_length=255)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.lead.display_id}: {self.title}"


class LeadStaffStatusHistory(models.Model):
    """Audit log — each time staff changes lead status (with lost reason when applicable)."""

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="staff_status_history")
    from_status_name = models.CharField(max_length=255, blank=True)
    to_status = models.ForeignKey(
        LeadStatus,
        on_delete=models.PROTECT,
        related_name="staff_status_history_entries",
    )
    lost_reason_type = models.ForeignKey(
        LeadLostReasonType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="status_history_entries",
    )
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="lead_staff_status_changes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Staff status history"
        verbose_name_plural = "Staff status history"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.lead.display_id}: {self.from_status_name} → {self.to_status.name}"


class LeadContact(models.Model):
    """Tracks each time a staff member contacts a lead."""

    class ContactType(models.TextChoices):
        CALL = "call", "Call"
        EMAIL = "email", "Email"
        WHATSAPP = "whatsapp", "WhatsApp"

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="contacts")
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="lead_contacts",
    )
    contact_type = models.CharField(max_length=20, choices=ContactType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.lead.name} contacted via {self.get_contact_type_display()} by {self.staff.get_full_name() if self.staff else 'Unknown'}"


class LeadProcedureStep(models.Model):
    """Follow-up submits service procedure step; back office reviews it."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending back office"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="procedure_steps",
    )
    procedure = models.ForeignKey(
        LeadServiceProcedure,
        on_delete=models.PROTECT,
        related_name="lead_steps",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    document = models.FileField(upload_to="leads/procedure_docs/%Y/%m/", blank=True)
    backoffice_document = models.FileField(upload_to="leads/procedure_docs/backoffice/%Y/%m/", blank=True)
    followup_note = models.TextField(blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_procedure_steps",
    )
    review_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_procedure_steps",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lead procedure step"
        verbose_name_plural = "Lead procedure steps"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["lead", "procedure"],
                name="uniq_lead_procedure_step",
            ),
        ]

    def __str__(self):
        return f"{self.lead.display_id}: {self.procedure.name} ({self.get_status_display()})"

    @property
    def document_filename(self):
        if not self.document:
            return ""
        return self.document.name.rsplit("/", 1)[-1]

    @property
    def backoffice_document_filename(self):
        if not self.backoffice_document:
            return ""
        return self.backoffice_document.name.rsplit("/", 1)[-1]


class ApprovalStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class SalaryIncrementRequest(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="salary_increment_requests",
    )
    current_salary = models.DecimalField(max_digits=12, decimal_places=2)
    requested_salary = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    hr_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salary_increment_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Increment: {self.user.get_username()} ({self.get_status_display()})"


class RejoiningRequest(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rejoining_requests",
    )
    rejoining_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    hr_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejoining_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Rejoining: {self.user.get_username()} ({self.get_status_display()})"


class PaymentRequest(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_requests",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.CharField(max_length=255)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    hr_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment: {self.user.get_username()} ({self.get_status_display()})"


class MarketingCampaign(models.Model):
    class Channel(models.TextChoices):
        FACEBOOK = "facebook", "Facebook"
        GOOGLE = "google", "Google Ads"
        WHATSAPP = "whatsapp", "WhatsApp"
        OTHER = "other", "Other"

    name = models.CharField(max_length=255)
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.OTHER)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    leads_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ClientCase(models.Model):
    """
    Post-sale case processing (visa, admission, general services).
    Follow-up collects documents → Back office verifies, submits, tracks, updates customer.
    """

    class ProcessingStage(models.TextChoices):
        OPENED = "opened", "Case opened"
        DOCUMENTS_VERIFIED = "documents_verified", "Documents verified"
        APPLICATION_CREATED = "application_created", "Application created"
        APPLIED_UNIVERSITIES = "applied_universities", "File submitted"
        PORTALS_UPLOADED = "portals_uploaded", "Submitted online"
        TRACKING_RESPONSES = "tracking_responses", "Tracking response"
        CUSTOMER_UPDATED = "customer_updated", "Customer status updated"
        COMPLETED = "completed", "Case completed"

    # Alias for existing code paths
    Status = ProcessingStage

    class ServiceType(models.TextChoices):
        VISA = "visa", "Visa"
        ADMISSION = "admission", "Admission"
        GENERAL = "general", "General Service"

    lead = models.ForeignKey(
        "Lead",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cases",
    )
    branch = models.ForeignKey(
        "branch.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cases",
    )
    client_name = models.CharField(max_length=255)
    service_type = models.CharField(
        max_length=20,
        choices=ServiceType.choices,
        default=ServiceType.GENERAL,
    )
    status = models.CharField(
        max_length=30,
        choices=ProcessingStage.choices,
        default=ProcessingStage.OPENED,
    )
    application_reference = models.CharField(
        max_length=120,
        blank=True,
        help_text="Internal student / application reference.",
    )
    universities_applied = models.TextField(
        blank=True,
        help_text="Authorities or providers submitted to (one per line).",
    )
    university_response_summary = models.TextField(
        blank=True,
        help_text="Response or outcome from authority or provider.",
    )
    customer_status_update = models.TextField(
        blank=True,
        help_text="Latest update communicated to the customer.",
    )
    documents_verified = models.BooleanField(default=False)
    documents_verification_note = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_cases",
    )
    notes = models.TextField(blank=True)
    submission_reference = models.CharField(
        max_length=120,
        blank=True,
        help_text="External reference when submitted to authority/provider.",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    completion_notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cases_processed",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.client_name} ({self.get_status_display()})"

    @property
    def case_ref(self):
        return f"CASE-{self.pk:05d}"

    @classmethod
    def processing_stage_order(cls):
        return [c[0] for c in cls.ProcessingStage.choices]

    @property
    def processing_stage_index(self):
        order = self.processing_stage_order()
        try:
            return order.index(self.status)
        except ValueError:
            return 0

    def documents_ready_from_lead(self):
        lead = self.lead
        if not lead:
            return False
        return (
            lead.doc_passport_collected
            and lead.doc_certificates_collected
            and lead.doc_photos_collected
        )

    def log_processing(self, user, note="", stage=None):
        stage = stage or self.status
        self.processing_logs.create(
            stage=stage,
            note=note,
            created_by=user,
        )

    def apply_processing_update(self, user, **fields):
        from django.utils import timezone

        log_note = fields.pop("log_note", "")
        new_status = fields.pop("status", None)
        if new_status:
            self.status = new_status
            if new_status == self.ProcessingStage.PORTALS_UPLOADED:
                self.submitted_at = timezone.now()
            if new_status == self.ProcessingStage.COMPLETED:
                self.completed_at = timezone.now()
        for key, value in fields.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.processed_by = user
        if not self.assigned_to_id:
            self.assigned_to = user
        self.save()
        if log_note or new_status:
            self.log_processing(user, note=log_note, stage=self.status)


class CaseProcessingLog(models.Model):
    """Timeline of back-office work on a customer case."""

    case = models.ForeignKey(
        ClientCase,
        on_delete=models.CASCADE,
        related_name="processing_logs",
    )
    stage = models.CharField(max_length=30)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="case_processing_logs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.case.case_ref} — {self.stage}"

    @property
    def stage_label(self):
        try:
            return ClientCase.ProcessingStage(self.stage).label
        except ValueError:
            return self.stage


class TeamMemberDocuments(models.Model):
    """Onboarding documents for branch-linked team members and managers."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_documents",
    )
    aadhaar_card = models.FileField(
        upload_to="team_docs/%Y/%m/aadhaar/",
        blank=True,
        null=True,
    )
    offer_letter = models.FileField(
        upload_to="team_docs/%Y/%m/offer/",
        blank=True,
        null=True,
    )
    passport_image = models.FileField(
        upload_to="team_docs/%Y/%m/passport/",
        blank=True,
        null=True,
    )
    passport_expiry = models.DateField(null=True, blank=True)
    emirates_id_image = models.FileField(
        upload_to="team_docs/%Y/%m/emirates_id/",
        blank=True,
        null=True,
    )
    emirates_id_expiry = models.DateField(null=True, blank=True)
    insurance_image = models.FileField(
        upload_to="team_docs/%Y/%m/insurance/",
        blank=True,
        null=True,
    )
    insurance_expiry = models.DateField(null=True, blank=True)
    labour_card_image = models.FileField(
        upload_to="team_docs/%Y/%m/labour_card/",
        blank=True,
        null=True,
    )
    labour_card_expiry = models.DateField(null=True, blank=True)
    labour_contract_image = models.FileField(
        upload_to="team_docs/%Y/%m/labour_contract/",
        blank=True,
        null=True,
    )
    labour_contract_expiry = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Team member documents"
        verbose_name_plural = "Team member documents"

    def __str__(self):
        return f"Documents — {self.user.get_username()}"
