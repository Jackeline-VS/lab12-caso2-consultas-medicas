"""Django Admin para gestión operativa (RF5)."""
from django.contrib import admin, messages

from .models import (
    AccesoHistorial, Cita, Consulta, Especialidad, Medico, NotaConsulta, Paciente,
)


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "cmp", "especialidad", "consultorio", "hora_inicio", "hora_fin")
    list_filter = ("especialidad",)
    search_fields = ("cmp", "usuario__first_name", "usuario__last_name")
    list_select_related = ("usuario", "especialidad")


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = (
        "dni", "apellidos", "nombres", "tipo", "email", "edad_paciente", "dias_ultima_consulta",
    )
    list_filter = ("tipo",)
    search_fields = ("dni", "nombres", "apellidos")

    @admin.display(description="Edad")
    def edad_paciente(self, obj):
        return obj.edad

    @admin.display(description="Días desde última consulta")
    def dias_ultima_consulta(self, obj):
        dias = obj.dias_desde_ultima_consulta
        return "Sin consultas" if dias is None else dias


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    """Agenda diaria por médico: filtre por fecha y médico."""

    list_display = ("fecha", "hora", "paciente", "medico", "estado")
    list_filter = ("fecha", "estado", "medico", "medico__especialidad")
    search_fields = (
        "paciente__dni", "paciente__nombres", "paciente__apellidos",
        "medico__usuario__last_name",
    )
    list_select_related = ("paciente", "medico__usuario", "medico__especialidad")
    date_hierarchy = "fecha"
    ordering = ("fecha", "hora")
    actions = ["marcar_completadas"]

    @admin.action(description="Marcar citas como completadas")
    def marcar_completadas(self, request, queryset):
        n = queryset.filter(estado=Cita.Estado.PROGRAMADA).update(
            estado=Cita.Estado.COMPLETADA
        )
        self.message_user(request, f"{n} cita(s) marcadas como completadas.", messages.SUCCESS)
