from django import forms
from .models import Viaje

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