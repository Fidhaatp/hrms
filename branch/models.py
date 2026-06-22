from django.conf import settings
from django.db import models
from django.utils import timezone


class ActiveBranchQuerySet(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class ActiveBranchManagerProfileQuerySet(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Branch(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=255)
    opening_date = models.DateField()
    nationality = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    active = ActiveBranchQuerySet()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        return not self.is_deleted

    def deactivate(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

    def reactivate(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

    def soft_delete(self):
        """Backward-compatible alias."""
        self.deactivate()


class BranchMonthlyTarget(models.Model):
    """Monthly sales target for a branch — split among staff by the branch manager."""

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="monthly_targets",
    )
    period_month = models.PositiveSmallIntegerField()
    period_year = models.PositiveSmallIntegerField()
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="branch_targets_assigned",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-period_year", "-period_month"]
        unique_together = [("branch", "period_month", "period_year")]
        verbose_name = "Branch monthly target"
        verbose_name_plural = "Branch monthly targets"

    def __str__(self):
        return f"{self.branch.name} — {self.period_month:02d}/{self.period_year}"


class BranchManager(models.Model):
    """Branch manager account linked to a branch."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="branch_manager_profile",
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="managers",
    )
    phone = models.CharField(max_length=20)
    join_date = models.DateField()
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    active = ActiveBranchManagerProfileQuerySet()

    class Meta:
        verbose_name = "Branch manager"
        verbose_name_plural = "Branch managers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.get_username()} — {self.branch.name}"

    def deactivate(self):
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

    def reactivate(self):
        if self.branch.is_deleted:
            raise ValueError("Cannot reactivate manager while branch is deactivated.")
        self.is_active = True
        self.deactivated_at = None
        self.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])

    @property
    def email(self):
        return self.user.email

    @property
    def username(self):
        return self.user.get_username()

    @property
    def display_name(self):
        user = self.user
        return user.get_full_name() or user.get_username()

    @property
    def initials(self):
        from core.profile_utils import get_initials

        return get_initials(self.display_name)

    @property
    def profile_picture_url(self):
        profile = getattr(self.user, "profile", None)
        if profile and profile.profile_picture:
            return profile.profile_picture.url
        return None
