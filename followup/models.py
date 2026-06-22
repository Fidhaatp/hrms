from django.conf import settings
from django.db import models
from django.utils import timezone


class ActiveFollowUpManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class FollowUp(models.Model):
    """Follow-up team profile linked to a common User account."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followup_profile",
    )
    branch = models.ForeignKey(
        "branch.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="followup_members",
    )
    phone = models.CharField(max_length=20)
    join_date = models.DateField()
    date_of_birth = models.DateField()
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    active = ActiveFollowUpManager()

    class Meta:
        verbose_name = "Follow-up profile"
        verbose_name_plural = "Follow-up profiles"
        ordering = ["-created_at"]

    def __str__(self):
        return self.user.get_username()

    @property
    def email(self):
        return self.user.email

    @property
    def username(self):
        return self.user.get_username()

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.get_username()

    @property
    def initials(self):
        from core.profile_utils import get_initials

        return get_initials(self.display_name)

    def deactivate(self):
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

    def reactivate(self):
        self.is_active = True
        self.deactivated_at = None
        self.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])
