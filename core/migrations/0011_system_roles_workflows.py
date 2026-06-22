from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("branch", "0005_branchmanager_is_active"),
        ("core", "0010_hr_workflow_requests"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="leaverequest",
            name="workflow_stage",
            field=models.CharField(
                choices=[
                    ("pending_manager", "Pending Branch Manager"),
                    ("pending_hr", "Pending HR"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                ],
                default="pending_manager",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="leaverequest",
            name="manager_reviewed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="leave_manager_reviews",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="leaverequest",
            name="manager_reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="leaverequest",
            name="manager_note",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="leaverequest",
            name="hr_reviewed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="leave_hr_reviews",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="leaverequest",
            name="hr_reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="leaverequest",
            name="hr_note",
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name="EmployeeCompliance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("visa_expiry", models.DateField(blank=True, null=True)),
                ("insurance_expiry", models.DateField(blank=True, null=True)),
                ("contract_end", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="compliance", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name_plural": "Employee compliance records"},
        ),
        migrations.CreateModel(
            name="AttendanceRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("status", models.CharField(choices=[("present", "Present"), ("absent", "Absent"), ("leave", "On Leave")], default="present", max_length=20)),
                ("check_in", models.TimeField(blank=True, null=True)),
                ("notes", models.CharField(blank=True, max_length=255)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_records", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-date"], "unique_together": {("user", "date")}},
        ),
        migrations.CreateModel(
            name="EmployeeTarget",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("period_month", models.PositiveSmallIntegerField()),
                ("period_year", models.PositiveSmallIntegerField()),
                ("target_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("achieved_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="targets", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-period_year", "-period_month"], "unique_together": {("user", "period_month", "period_year")}},
        ),
        migrations.CreateModel(
            name="EmployeeIncentive",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("month", models.PositiveSmallIntegerField()),
                ("year", models.PositiveSmallIntegerField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="incentives", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-year", "-month"]},
        ),
        migrations.CreateModel(
            name="Announcement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("body", models.TextField()),
                ("target_roles", models.CharField(blank=True, help_text="Comma-separated role keys (staff, branch, hr, …). Empty = all.", max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="announcements_created", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Award",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("award_type", models.CharField(choices=[("employee_of_month", "Employee of the Month"), ("branch_of_month", "Branch of the Month")], max_length=30)),
                ("month", models.PositiveSmallIntegerField()),
                ("year", models.PositiveSmallIntegerField()),
                ("note", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("winner_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="awards_won", to=settings.AUTH_USER_MODEL)),
                ("winner_branch", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="awards_won", to="branch.branch")),
            ],
            options={"ordering": ["-year", "-month"]},
        ),
        migrations.CreateModel(
            name="RecruitmentRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("position_title", models.CharField(max_length=255)),
                ("headcount", models.PositiveSmallIntegerField(default=1)),
                ("reason", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("branch_request", "Branch Request"), ("hr_review", "HR Review"), ("interview", "Interview"), ("joining", "Joining"), ("closed", "Closed")], default="branch_request", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recruitment_requests", to="branch.branch")),
                ("requested_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="recruitment_requests_created", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.RunPython(
            code=lambda apps, schema_editor: apps.get_model("core", "LeaveRequest").objects.filter(
                status="pending"
            ).update(workflow_stage="pending_hr"),
            reverse_code=migrations.RunPython.noop,
        ),
    ]
