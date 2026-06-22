import django.db.models.deletion
from django.db import migrations, models


def split_category_and_type(apps, schema_editor):
    LeaveCategory = apps.get_model("core", "LeaveCategory")
    LeaveType = apps.get_model("core", "LeaveType")
    LeaveRequest = apps.get_model("core", "LeaveRequest")

    yearly, _ = LeaveCategory.objects.get_or_create(
        code="yearly",
        defaults={
            "name": "Yearly Leave",
            "description": "Annual leave entitlement — one month (30 days) per calendar year.",
            "days_per_year": 30,
            "is_active": True,
        },
    )

    type_defaults = [
        ("sick", "Sick Leave", "Medical or health-related leave."),
        ("casual", "Casual Leave", "Short personal leave."),
    ]
    type_by_code = {}
    for code, name, description in type_defaults:
        leave_type, _ = LeaveType.objects.get_or_create(
            code=code,
            defaults={"name": name, "description": description, "is_active": True},
        )
        type_by_code[code] = leave_type

    default_type = type_by_code["casual"]

    for cat in LeaveCategory.objects.exclude(code="yearly"):
        mapped_type = type_by_code.get(cat.code)
        for req in LeaveRequest.objects.filter(leave_category_id=cat.pk):
            req.leave_category = yearly
            if mapped_type:
                req.leave_type = mapped_type
            elif not req.leave_type_id:
                req.leave_type = default_type
            req.save(update_fields=["leave_category", "leave_type"])
        cat.delete()

    for req in LeaveRequest.objects.filter(leave_type__isnull=True):
        req.leave_type = default_type
        req.save(update_fields=["leave_type"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_leave_categories_sick_casual"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="LeaveType",
            new_name="LeaveCategory",
        ),
        migrations.AlterModelOptions(
            name="leavecategory",
            options={
                "ordering": ["name"],
                "verbose_name": "Leave category",
                "verbose_name_plural": "Leave categories",
            },
        ),
        migrations.CreateModel(
            name="LeaveType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("code", models.SlugField(blank=True, max_length=50, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Leave type",
                "verbose_name_plural": "Leave types",
                "ordering": ["name"],
            },
        ),
        migrations.RenameField(
            model_name="leaverequest",
            old_name="leave_type",
            new_name="leave_category",
        ),
        migrations.AddField(
            model_name="leaverequest",
            name="leave_type",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="leave_requests",
                to="core.leavetype",
            ),
        ),
        migrations.RunPython(split_category_and_type, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="leaverequest",
            name="leave_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="leave_requests",
                to="core.leavetype",
            ),
        ),
    ]
