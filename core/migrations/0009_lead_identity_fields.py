from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_lead_pipeline"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="takhlees_id",
            field=models.CharField(blank=True, max_length=64, verbose_name="Takhlees ID"),
        ),
        migrations.AddField(
            model_name="lead",
            name="passport_no",
            field=models.CharField(blank=True, max_length=64, verbose_name="Passport No"),
        ),
        migrations.AddField(
            model_name="lead",
            name="eid_no",
            field=models.CharField(blank=True, max_length=64, verbose_name="EID No"),
        ),
    ]
