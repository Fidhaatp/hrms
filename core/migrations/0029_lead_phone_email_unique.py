from django.db import migrations, models


def dedupe_lead_contact_fields(apps, schema_editor):
    Lead = apps.get_model("core", "Lead")
    seen_phones = {}
    for lead in Lead.objects.order_by("id"):
        phone = (lead.phone or "").strip()
        if phone in seen_phones:
            lead.phone = f"{phone}-dup{lead.pk}"
            lead.save(update_fields=["phone"])
        else:
            seen_phones[phone] = lead.pk

    seen_emails = {}
    for lead in Lead.objects.order_by("id"):
        email = (lead.email or "").strip()
        if not email:
            lead.email = None
            lead.save(update_fields=["email"])
            continue
        email_key = email.lower()
        if email_key in seen_emails:
            lead.email = f"dup{lead.pk}+{email_key}"
            lead.save(update_fields=["email"])
        else:
            seen_emails[email_key] = lead.pk


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0028_lead_service_zip"),
    ]

    operations = [
        migrations.RunPython(dedupe_lead_contact_fields, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="lead",
            name="email",
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="lead",
            name="phone",
            field=models.CharField(max_length=30, unique=True),
        ),
    ]
