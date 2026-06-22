from django.db import migrations


SERVICES = [
    "FAMILY VISA",
    "FAMILY VISA RENEWAL",
    "EMPLOYMENT VISA",
    "RENEW EMPLOYMENT VISA",
    "DOMESTIC VISA",
    "RENEW DOMESTIC VISA",
    "TRADE LICENSE",
    "INVESTER VISA",
    "TRADE LICENSE AMENTMENT",
    "TRADE LICENSE RENEWAL",
    "TAJIR ABUDHABI",
    "TAX",
    "DRIVING LICENSE GOLDEN CHANCE",
    "DRIVING LICENSE NORMAL",
]


def slugify_code(value):
    return value.lower().replace("&", "and").replace("/", "-").replace(" ", "-")[:50]


def seed_lead_services(apps, schema_editor):
    LeadService = apps.get_model("core", "LeadService")
    for index, name in enumerate(SERVICES):
        code = slugify_code(name)
        service, created = LeadService.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "description": "",
                "is_active": True,
                "sort_order": index,
            },
        )
        update_fields = []
        if service.name != name:
            service.name = name
            update_fields.append("name")
        if not service.is_active:
            service.is_active = True
            update_fields.append("is_active")
        if service.sort_order != index:
            service.sort_order = index
            update_fields.append("sort_order")
        if update_fields:
            service.save(update_fields=update_fields)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0037_lead_payment_verification"),
    ]

    operations = [
        migrations.RunPython(seed_lead_services, migrations.RunPython.noop),
    ]

