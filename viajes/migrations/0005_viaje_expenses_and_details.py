import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("viajes", "0004_rename_lugar_actividad_ubicacion_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="viaje",
            old_name="destino",
            new_name="titulo",
        ),
        migrations.AlterField(
            model_name="viaje",
            name="titulo",
            field=models.CharField(max_length=150),
        ),
        migrations.AddField(
            model_name="viaje",
            name="pais",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="viaje",
            name="ciudad",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="viaje",
            name="publico",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="viaje",
            name="presupuesto",
            field=models.DecimalField(
                decimal_places=2, default=0.0, max_digits=12
            ),
        ),
        migrations.AlterField(
            model_name="actividad",
            name="costo",
            field=models.DecimalField(
                decimal_places=2, default=0.0, max_digits=12
            ),
        ),
        migrations.CreateModel(
            name="Gasto",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("categoria", models.CharField(max_length=100)),
                ("monto", models.DecimalField(decimal_places=2, max_digits=12)),
                ("fecha", models.DateField()),
                ("concepto", models.CharField(max_length=200)),
                ("moneda", models.CharField(default="CLP", max_length=10)),
                (
                    "viaje",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="gastos",
                        to="viajes.viaje",
                    ),
                ),
            ],
        ),
    ]
