from django import forms
from .models import Viaje, Dia, Actividad, Photo, Companion

class ViajeForm(forms.ModelForm):
    class Meta:
        model = Viaje
        fields = ['destino', 'descripcion', 'fecha_inicio', 'fecha_fin', 'presupuesto']
        widgets = {
            'destino': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. París'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'presupuesto': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
        }


class DiaForm(forms.ModelForm):
    class Meta:
        model = Dia
        fields = [
            'numero_dia', 
            'fecha', 
            'titulo', 
            'descripcion', 
            'ubicacion_gps', 
            'foto_principal'
        ]
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = [
            'nombre', 
            'descripcion', 
            'hora', 
            'ubicacion', 
            'categoria', 
            'costo', 
            'rating'
        ]
        widgets = {
            'hora': forms.TimeInput(attrs={'type': 'time'}),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

class CompanionForm(forms.ModelForm):
      class Meta:
           model = Companion
           fields = ['nombre', 'relacion', 'email']
           widgets = {
        'nombre': forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del acompañante',
            }
        ),
        'relacion': forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Amigo, Familiar',
            }
        ),
        'email': forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com',
            }
        ),
    }


class PhotoForm(forms.ModelForm):
  class Meta:
    model = Photo
    fields = ['imagen', 'descripcion']
    widgets = {
        'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        'descripcion': forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Breve descripción de la foto (opcional)',
            }
        ),
    }