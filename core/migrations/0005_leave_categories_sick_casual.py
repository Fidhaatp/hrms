from django.db import migrations


def add_sick_casual_leave_types(apps, schema_editor):
    LeaveType = apps.get_model("core", "LeaveType")
    defaults = [
        {
            "code": "sick",
            "name": "Sick Leave",
            "description": "Medical or health-related leave.",
            "days_per_year": 12,
        },
        {
            "code": "casual",
            "name": "Casual Leave",
            "description": "Short personal leave.",
            "days_per_year": 12,
        },
    ]
    for item in defaults:
        LeaveType.objects.get_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "description": item["description"],
                "days_per_year": item["days_per_year"],
                "is_active": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_leave_system"),
    ]

    operations = [
        migrations.RunPython(add_sick_casual_leave_types, migrations.RunPython.noop),
    ]
