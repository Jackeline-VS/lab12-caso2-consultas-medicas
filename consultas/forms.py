"""Formularios del Caso 2 (RF1 y RF2): validaciones, validación cruzada y sanitización."""
import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import strip_tags

from .models import Cita, Consulta, Especialidad, Medico, NotaConsulta, Paciente
from .roles import DURACION_CITA_MIN, dentro_de_horario, minutos

SOLO_LETRAS = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]+$")


def sanitizar_texto(valor):
    """Quita etiquetas HTML y espacios sobrantes (evita XSS almacenado)."""
    valor = strip_tags(valor or "")
    valor = re.sub(r"[ \t]+", " ", valor)
    return valor.strip()


class PacienteForm(forms.ModelForm):
    """Registro de pacientes (RF1)."""

    class Meta:
        model = Paciente
        fields = [
            "dni", "nombres", "apellidos", "fecha_nacimiento",
            "tipo", "codigo_uncp", "email", "alergias",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "alergias": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_nombres(self):
        valor = sanitizar_texto(self.cleaned_data["nombres"])
        if not SOLO_LETRAS.match(valor):
            raise ValidationError("Use solo letras en los nombres.")
        return valor

    def clean_apellidos(self):
        valor = sanitizar_texto(self.cleaned_data["apellidos"])
        if not SOLO_LETRAS.match(valor):
            raise ValidationError("Use solo letras en los apellidos.")
        return valor

    def clean_alergias(self):
        return sanitizar_texto(self.cleaned_data.get("alergias"))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("tipo") == Paciente.Tipo.ESTUDIANTE and not cleaned.get("codigo_uncp"):
            self.add_error("codigo_uncp", "El código UNCP es obligatorio para estudiantes.")
        return cleaned
