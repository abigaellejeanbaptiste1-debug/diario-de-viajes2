import django.db.models.deletion
from django.db import migrations, models


def associate_photos_with_trips(apps, schema_editor):
    Photo = apps.get_model("viajes", "Photo")
    database = schema_editor.connection.alias
    photos = Photo.objects.using(database).select_related("dia").iterator()
    for photo in photos:
        photo.viaje_id = photo.dia.viaje_id
        photo.save(using=database, update_fields=["viaje"])


class Migration(migrations.Migration):
    dependencies = [
        ("viajes", "0010_actividad_fecha_actividad_viaje_alter_actividad_dia"),
    ]

    operations = [
        migrations.AddField(
            model_name="photo",
            name="viaje",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="fotos",
                to="viajes.viaje",
            ),
        ),
        migrations.RunPython(
            associate_photos_with_trips,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="photo",
            name="dia",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="fotos",
                to="viajes.dia",
            ),
        ),
    ]
