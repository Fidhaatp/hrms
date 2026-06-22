from django.conf import settings
from django.db import models
from django.utils import timezone


class BranchAccountant(models.Model):
    """Branch accountant profile linked to a branch."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="branch_accountant_profile",
    )
    branch = models.ForeignKey(
        "branch.Branch",
        on_delete=models.PROTECT,
        related_name="accountants",
    )
    phone = models.CharField(max_length=20, blank=True)
    join_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Branch accountant"
        verbose_name_plural = "Branch accountants"

    def __str__(self):
        return f"{self.user.get_username()} — {self.branch.name}"

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.get_username()
