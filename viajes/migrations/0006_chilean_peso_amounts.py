from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("viajes", "0005_viaje_expenses_and_details"),
    ]

    operations = [
        migrations.AlterField(
            model_name="viaje",
            name="presupuesto",
            field=models.DecimalField(
                decimal_places=0, default=0, max_digits=12
            ),
        ),
        migrations.AlterField(
            model_name="actividad",
            name="costo",
            field=models.DecimalField(
                decimal_places=0, default=0, max_digits=12
            ),
        ),
        migrations.AlterField(
            model_name="gasto",
            name="monto",
            field=models.DecimalField(decimal_places=0, max_digits=12),
        ),
        migrations.AlterField(
            model_name="gasto",
            name="moneda",
            field=models.CharField(
                choices=[("CLP", "Peso chileno (CLP)")],
                default="CLP",
                max_length=10,
            ),
        ),
    ]
