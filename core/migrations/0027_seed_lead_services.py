from django.db import migrations


def seed_lead_services(apps, schema_editor):
    LeadService = apps.get_model("core", "LeadService")
    LeadServiceDocumentType = apps.get_model("core", "LeadServiceDocumentType")

    visa, _ = LeadService.objects.get_or_create(
        code="visa-processing",
        defaults={
            "name": "Visa Processing",
            "description": "New visa and renewal applications",
            "sort_order": 1,
            "is_active": True,
        },
    )
    pro, _ = LeadService.objects.get_or_create(
        code="pro-services",
        defaults={
            "name": "PRO Services",
            "description": "Government and PRO-related work",
            "sort_order": 2,
            "is_active": True,
        },
    )

    visa_docs = [
        ("passport", "Passport copy", "Clear scan of passport bio page", True, 1),
        ("photo", "Passport photo", "White background, recent photo", True, 2),
        ("offer-letter", "Offer letter", "Signed offer or employment letter", False, 3),
    ]
    for code, name, help_text, required, order in visa_docs:
        LeadServiceDocumentType.objects.get_or_create(
            service=visa,
            code=code,
            defaults={
                "name": name,
                "help_text": help_text,
                "is_required": required,
                "sort_order": order,
                "is_active": True,
            },
        )

    pro_docs = [
        ("trade-license", "Trade license copy", "Valid trade license", True, 1),
        ("emirates-id", "Emirates ID copy", "Front and back if applicable", True, 2),
        ("moa", "MOA / Agreement", "Memorandum of association if required", False, 3),
    ]
    for code, name, help_text, required, order in pro_docs:
        LeadServiceDocumentType.objects.get_or_create(
            service=pro,
            code=code,
            defaults={
                "name": name,
                "help_text": help_text,
                "is_required": required,
                "sort_order": order,
                "is_active": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0026_lead_services"),
    ]

    operations = [
        migrations.RunPython(seed_lead_services, migrations.RunPython.noop),
    ]
