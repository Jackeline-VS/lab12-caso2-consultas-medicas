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


class CitaForm(forms.ModelForm):
    """Agendamiento de citas con validaciones cruzadas (RF2)."""

    especialidad = forms.ModelChoiceField(
        queryset=Especialidad.objects.all(), label="Especialidad"
    )

    class Meta:
        model = Cita
        fields = ["paciente", "medico", "fecha", "hora", "motivo"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "hora": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "motivo": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, paciente_fijo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.paciente_fijo = paciente_fijo
        self.fields["medico"].queryset = Medico.objects.select_related(
            "usuario", "especialidad"
        )
        if paciente_fijo is not None:
            del self.fields["paciente"]  # el paciente agenda solo para sí mismo
        self.order_fields(["especialidad", "paciente", "medico", "fecha", "hora", "motivo"])

    def clean_motivo(self):
        motivo = sanitizar_texto(self.cleaned_data["motivo"])
        if len(motivo) < 20:
            raise ValidationError("El motivo debe tener al menos 20 caracteres.")
        return motivo

    def clean(self):
        cleaned = super().clean()
        paciente = self.paciente_fijo or cleaned.get("paciente")
        especialidad = cleaned.get("especialidad")
        medico = cleaned.get("medico")
        fecha = cleaned.get("fecha")
        hora = cleaned.get("hora")

        if medico and especialidad and medico.especialidad_id != especialidad.id:
            self.add_error("medico", f"El médico elegido no pertenece a {especialidad}.")

        if fecha and fecha < timezone.localdate():
            self.add_error("fecha", "No se pueden agendar citas en fechas pasadas.")
        elif fecha and hora:
            ahora = timezone.localtime()
            if fecha == ahora.date() and hora <= ahora.time():
                self.add_error("hora", "Esa hora ya pasó. Elija una hora posterior.")
            elif not dentro_de_horario(fecha, hora):
                self.add_error(
                    "hora", "Fuera del horario de atención (L-V 8:00-18:00, Sáb 8:00-13:00)."
                )
            elif medico:
                if not (medico.hora_inicio <= hora < medico.hora_fin):
                    self.add_error(
                        "hora",
                        f"El médico atiende de {medico.hora_inicio:%H:%M} a {medico.hora_fin:%H:%M}.",
                    )
                else:
                    self._validar_agenda_medico(medico, fecha, hora)

        if paciente and fecha and Cita.objects.filter(
            paciente=paciente, fecha=fecha, estado=Cita.Estado.PROGRAMADA
        ).exists():
            self.add_error(None, "El paciente ya tiene una cita programada ese día.")
        return cleaned

    def _validar_agenda_medico(self, medico, fecha, hora):
        """Slot ocupado y citas superpuestas del médico (cada cita dura 30 min)."""
        for otra in Cita.objects.filter(
            medico=medico, fecha=fecha, estado=Cita.Estado.PROGRAMADA
        ):
            if otra.hora == hora:
                self.add_error("hora", "Ese horario ya está ocupado para el médico.")
                return
            if abs(minutos(otra.hora) - minutos(hora)) < DURACION_CITA_MIN:
                self.add_error(
                    "hora",
                    f"Se superpone con otra cita del médico a las {otra.hora:%H:%M} "
                    f"(cada cita dura {DURACION_CITA_MIN} min).",
                )
                return
