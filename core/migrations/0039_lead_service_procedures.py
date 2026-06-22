from django.db import migrations, models
import django.db.models.deletion


SERVICE_PROCEDURES = {
    "FAMILY VISA": [
        "Marraige Certificate attestation",
        "translation",
        "Sponsor File Open",
        "Entry Permit",
        "Change of Status",
        "medical",
        "health insurance",
        "Emirates ID and Residency",
    ],
    "FAMILY VISA RENEWAL": [
        "Emirates ID and Residency",
    ],
    "EMPLOYMENT VISA": [
        "work permit package (offer letter and and contract)",
        "Duabi Insurance",
        "Fee Payment",
        "Entry permit",
        "change of status (If person is inside)",
        "insurance",
        "medical",
        "id and residancy",
    ],
    "RENEW EMPLOYMENT VISA": [
        "Echannel renwal",
        "contract renewal",
        "Dubai insurance",
        "contract submission",
        "Emirates id and Residency",
    ],
    "DOMESTIC VISA": [
        "Dubai insurance",
        "entry permit",
        "change of status (if inside)",
        "insurance",
        "medical",
        "Emirates ID",
        "Residancy",
    ],
    "RENEW DOMESTIC VISA": [
        "medical",
        "contract renewal",
        "emirates id",
        "Dubai insurance",
        "residancy renewal",
    ],
    "TRADE LICENSE": [
        "reserving economic name + initial approval",
        "LLC agreement and submition",
        "tenancy",
        "License Issue",
        "add real Beneficiary",
        "Echannel registration",
    ],
    "INVESTER VISA": [
        "entry permit",
        "change of status",
        "insurance",
        "medical",
        "emirates id and Residency",
    ],
    "TRADE LICENSE AMENTMENT": [
        "trade name reservation",
        "newspaper advertisement",
        "moa with submission",
        "License payment",
        "License updation in icp",
        "License updation in MOHRE",
    ],
    "TRADE LICENSE RENEWAL": [
        "License renewal",
        "Echannel renwal",
        "License updation in icp",
        "License updation in MOHRE",
    ],
    "TAJIR ABUDHABI": [
        "Reserving economic name",
        "initial approval",
        "real Beneficiary",
        "license payment",
        "Echannel registration",
    ],
    "TAX": [
        "copotrate tax",
        "vat registration",
    ],
    "DRIVING LICENSE GOLDEN CHANCE": [
        "eye test",
        "file open and translation",
        "thiory class, simulator and exam booking",
        "road test date booking and learning permit",
        "Driving class",
        "certificate issue",
        "issue license",
    ],
    "DRIVING LICENSE NORMAL": [
        "eye test",
        "file open",
        "theory class, simulator exam booking",
        "parking class and test",
        "road test date booking and learning permit",
        "Driving class",
        "certificate issue",
        "issue license",
    ],
}


def _slug(value):
    return value.lower().replace("&", "and").replace("/", "-").replace(" ", "-")[:50]


def seed_service_procedures(apps, schema_editor):
    LeadService = apps.get_model("core", "LeadService")
    LeadServiceProcedure = apps.get_model("core", "LeadServiceProcedure")

    for service_name, procedures in SERVICE_PROCEDURES.items():
        service = LeadService.objects.filter(name__iexact=service_name).first()
        if not service:
            continue
        for index, step_name in enumerate(procedures):
            code = _slug(step_name)
            obj, _ = LeadServiceProcedure.objects.get_or_create(
                service_id=service.pk,
                code=code,
                defaults={
                    "name": step_name,
                    "sort_order": index,
                    "is_active": True,
                },
            )
            fields = []
            if obj.name != step_name:
                obj.name = step_name
                fields.append("name")
            if obj.sort_order != index:
                obj.sort_order = index
                fields.append("sort_order")
            if not obj.is_active:
                obj.is_active = True
                fields.append("is_active")
            if fields:
                obj.save(update_fields=fields)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0038_seed_requested_lead_services"),
    ]

    operations = [
        migrations.CreateModel(
            name="LeadServiceProcedure",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("code", models.SlugField(blank=True, max_length=50)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "service",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="procedures", to="core.leadservice"),
                ),
            ],
            options={
                "verbose_name": "Lead service procedure",
                "verbose_name_plural": "Lead service procedures",
                "ordering": ["sort_order", "name"],
                "constraints": [
                    models.UniqueConstraint(fields=("service", "code"), name="uniq_lead_service_procedure_code")
                ],
            },
        ),
        migrations.CreateModel(
            name="LeadProcedureStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending back office"), ("approved", "Approved"), ("rejected", "Rejected")],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("document", models.FileField(blank=True, upload_to="leads/procedure_docs/%Y/%m/")),
                ("followup_note", models.TextField(blank=True)),
                ("review_note", models.TextField(blank=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("lead", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="procedure_steps", to="core.lead")),
                (
                    "procedure",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lead_steps", to="core.leadserviceprocedure"),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_procedure_steps", to="auth.user"),
                ),
                (
                    "submitted_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="submitted_procedure_steps", to="auth.user"),
                ),
            ],
            options={
                "verbose_name": "Lead procedure step",
                "verbose_name_plural": "Lead procedure steps",
                "ordering": ["created_at"],
                "constraints": [models.UniqueConstraint(fields=("lead", "procedure"), name="uniq_lead_procedure_step")],
            },
        ),
        migrations.RunPython(seed_service_procedures, migrations.RunPython.noop),
    ]

