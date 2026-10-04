from django import forms
from django.core.exceptions import ValidationError

from .models import Actividad, Companion, Dia, Gasto, Photo, Viaje


class ViajeForm(forms.ModelForm):
    class Meta:
        model = Viaje
        fields = [
            "titulo",
            "descripcion",
            "fecha_inicio",
            "fecha_fin",
            "pais",
            "ciudad",
            "presupuesto",
            "publico",
        ]
        widgets = {
            "titulo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. Expedición Torres del Paine",
                }
            ),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "fecha_inicio": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "pais": forms.TextInput(attrs={"class": "form-control", "placeholder": "Chile"}),
            "ciudad": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Puerto Natales"}
            ),
            "presupuesto": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Ej. 500000"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")
        presupuesto = cleaned_data.get("presupuesto")

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            self.add_error("fecha_fin", "La fecha de término debe ser posterior al inicio.")
        if presupuesto is not None and presupuesto < 0:
            self.add_error("presupuesto", "El presupuesto no puede ser negativo.")
        return cleaned_data


class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = ["dia", "categoria", "monto", "fecha", "concepto", "moneda"]
        widgets = {
            "categoria": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej. Alojamiento, Comida"}
            ),
            "monto": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Monto en pesos chilenos (ej. 45.000)",
                    "step": "1",
                }
            ),
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "concepto": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej. Hotel Patagonia"}
            ),
            "moneda": forms.Select(attrs={"class": "form-control"}),
        }

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        if monto < 0:
            raise ValidationError("El monto no puede ser negativo.")
        return monto


class DiaForm(forms.ModelForm):
    actividad_nombre = forms.CharField(
        required=False,
        max_length=200,
        label="Título de la actividad",
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 w-full h-10 px-3 rounded-lg bg-surface-container-lowest",
                "placeholder": "Ej. Visita al museo",
            }
        ),
    )
    actividad_descripcion = forms.CharField(
        required=False,
        label="Descripción de la actividad",
        widget=forms.Textarea(
            attrs={
                "rows": 2,
                "class": "mt-1 w-full px-3 py-2 rounded-lg bg-surface-container-lowest",
                "placeholder": "¿Qué hiciste?",
            }
        ),
    )

    class Meta:
        model = Dia
        fields = [
            "numero_dia",
            "fecha",
            "titulo",
            "descripcion",
            "ubicacion_gps",
            "foto_principal",
        ]
        widgets = {
            "numero_dia": forms.NumberInput(
                attrs={
                    "min": "1",
                    "class": "mt-1 w-full h-10 px-3 rounded-lg bg-surface-container-lowest",
                }
            ),
            "fecha": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "mt-1 w-full h-10 px-3 rounded-lg bg-surface-container-lowest",
                }
            ),
            "titulo": forms.TextInput(
                attrs={
                    "class": "mt-1 w-full h-10 px-3 rounded-lg bg-surface-container-lowest",
                }
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "mt-1 w-full px-3 py-2 rounded-lg bg-surface-container-lowest",
                }
            ),
            "ubicacion_gps": forms.TextInput(
                attrs={
                    "class": "mt-1 w-full h-10 px-3 rounded-lg bg-surface-container-lowest",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("actividad_descripcion") and not cleaned_data.get(
            "actividad_nombre"
        ):
            self.add_error(
                "actividad_nombre",
                "Escribe un título para poder guardar la descripción de la actividad.",
            )
        return cleaned_data


class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = [
            "nombre",
            "descripcion",
            "hora",
            "ubicacion",
            "categoria",
            "costo",
            "rating",
        ]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "mt-1 w-full h-10 px-3 rounded-lg bg-surface-container-lowest",
                }
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "mt-1 w-full px-3 py-2 rounded-lg bg-surface-container-lowest",
                }
            ),
            "hora": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "mt-1 w-full h-10 px-3 rounded-lg bg-surface-container-lowest",
                }
            ),
            "ubicacion": forms.TextInput(
                attrs={
                    "class": "mt-1 w-full h-10 px-3 rounded-lg bg-surface-container-lowest",
                }
            ),
            "categoria": forms.TextInput(
                attrs={
                    "class": "mt-1 w-full h-10 px-3 rounded-lg bg-surface-container-lowest",
                }
            ),
            "costo": forms.NumberInput(
                attrs={
                    "placeholder": "Costo en pesos chilenos",
                    "step": "1",
                    "class": "mt-1 w-full h-10 px-3 rounded-lg bg-surface-container-lowest",
                }
            ),
            "rating": forms.NumberInput(
                attrs={
                    "class": "mt-1 w-full h-10 px-3 rounded-lg bg-surface-container-lowest",
                }
            ),
        }

    def clean_costo(self):
        costo = self.cleaned_data["costo"]
        if costo < 0:
            raise ValidationError("El costo no puede ser negativo.")
        return costo


class RegistroActividadForm(forms.ModelForm):
    fecha = forms.DateField(
        label="Fecha",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "mt-1 w-full h-12 rounded-lg bg-surface-container-low px-space-md text-on-surface"
            }
        ),
    )

    class Meta:
        model = Actividad
        fields = ["nombre", "costo"]
        labels = {
            "nombre": "Actividad",
            "costo": "Monto gastado (CLP)",
        }
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "mt-1 w-full h-12 rounded-lg bg-surface-container-low px-space-md text-on-surface",
                    "placeholder": "¿Qué actividad realizaste?",
                }
            ),
            "costo": forms.NumberInput(
                attrs={
                    "class": "mt-1 w-full h-12 rounded-lg bg-surface-container-low px-space-md text-on-surface",
                    "min": "0",
                    "step": "1",
                    "placeholder": "0",
                }
            ),
        }

    def __init__(self, *args, viaje, **kwargs):
        super().__init__(*args, **kwargs)
        self._viaje = viaje
        self.fields["costo"].required = False
        self.fields["costo"].initial = 0

    def clean_costo(self):
        costo = self.cleaned_data.get("costo")
        if costo is None:
            return 0
        if costo < 0:
            raise ValidationError("El monto gastado no puede ser negativo.")
        return costo

    def save(self, commit=True):
        self.instance.viaje = self._viaje
        self.instance.fecha = self.cleaned_data["fecha"]
        self.instance.dia = None
        return super().save(commit=commit)


class CompanionForm(forms.ModelForm):
    class Meta:
        model = Companion
        fields = ["nombre", "relacion", "email"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre del acompañante",
                }
            ),
            "relacion": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Amigo, Familiar",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "correo@ejemplo.com",
                }
            ),
        }


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ["imagen", "descripcion"]
        widgets = {
            "imagen": forms.ClearableFileInput(attrs={"class": "hidden"}),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "w-full rounded-lg border border-outline/40 bg-surface-container-low px-space-md py-space-sm font-body-md text-on-surface placeholder:text-outline focus:border-secondary focus:outline-none focus:ring-2 focus:ring-secondary/20",
                    "rows": 4,
                    "placeholder": "Breve descripción de la foto (opcional)",
                }
            ),
        }
