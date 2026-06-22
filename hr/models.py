from django.conf import settings
from django.db import models


class Hr(models.Model):
    """HR-specific profile linked to the common User account."""

    username = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hr_profile",
    )
    phone = models.CharField(max_length=20)
    join_date = models.DateField()
    date_of_birth = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "HR profile"
        verbose_name_plural = "HR profiles"

    def __str__(self):
        return self.username.get_username()

    @property
    def display_name(self):
        user = self.username
        return user.get_full_name() or user.get_username()

    @property
    def login_username(self):
        return self.username.get_username()

    @property
    def initials(self):
        name = self.display_name.replace("_", " ").replace(".", " ").strip()
        parts = [p for p in name.split() if p]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return (name[:2] if len(name) >= 2 else name[:1] or "?").upper()
