import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def clear_old_leave_requests(apps, schema_editor):
    LeaveRequest = apps.get_model("core", "LeaveRequest")
    LeaveRequest.objects.all().delete()


def create_yearly_leave_type(apps, schema_editor):
    LeaveType = apps.get_model("core", "LeaveType")
    LeaveType.objects.get_or_create(
        code="yearly",
        defaults={
            "name": "Yearly Leave",
            "description": "Annual leave entitlement — one month (30 days) per calendar year.",
            "days_per_year": 30,
            "is_active": True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_userprofile_profile_picture"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="leavetype",
            name="code",
            field=models.SlugField(blank=True, max_length=50, unique=True),
        ),
        migrations.AddField(
            model_name="leavetype",
            name="days_per_year",
            field=models.PositiveIntegerField(default=30, help_text="Allowed days per calendar year (30 = one month)."),
        ),
        migrations.AddField(
            model_name="leavetype",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(clear_old_leave_requests, migrations.RunPython.noop),
        migrations.AddField(
            model_name="leaverequest",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="leave_requests",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="leaverequest",
            name="leave_type",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.leavetype"),
        ),
        migrations.AlterField(
            model_name="leaverequest",
            name="status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AlterModelOptions(
            name="leavetype",
            options={"ordering": ["name"]},
        ),
        migrations.AlterModelOptions(
            name="leaverequest",
            options={"ordering": ["-created_at"]},
        ),
        migrations.RunPython(create_yearly_leave_type, migrations.RunPython.noop),
    ]
