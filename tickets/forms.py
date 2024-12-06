from django import forms
from .models import Equipo, HistorialTicket, Ticket
from django.core.exceptions import ValidationError

class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ['tipo', 'marca', 'observaciones', 'incluye_cargador']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'incluye_cargador': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        
    def clean_marca(self):
        # Validar que la marca no esté vacía y tenga un mínimo de caracteres
        marca = self.cleaned_data.get('marca')
        print(marca)
        if not marca:
            raise ValidationError("El campo 'Marca' no puede estar vacío.")
        if len(marca) < 2:
            raise ValidationError("La marca debe tener al menos 2 caracteres.")
        return marca

    def clean_observaciones(self):
        # Validar que las observaciones tengan al menos 10 caracteres
        observaciones = self.cleaned_data.get('observaciones')
        print(observaciones)
        if not observaciones:
            raise ValidationError("El campo 'Observaciones' no puede estar vacío.")
        if len(observaciones) < 6:
            raise ValidationError("Las observaciones deben tener al menos 6 caracteres.")
        return observaciones

    def clean(self):
        # Validación general (dependencias entre campos)
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        incluye_cargador = cleaned_data.get('incluye_cargador')

        # Si el tipo es 'notebook', se requiere que 'incluye_cargador' sea True
        if tipo == 'notebook' and not incluye_cargador:
            self.add_error('incluye_cargador', "Debe marcar 'Incluye Cargador' para un equipo de tipo Notebook.")
        
        return cleaned_data
        
class RegistrarReparacionForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['estado', 'descripcion_reparacion', 'prioridad']
        
class HistorialForm(forms.ModelForm):
    class Meta:
        model = HistorialTicket
        fields = ['descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe el avance realizado...'}),
        }