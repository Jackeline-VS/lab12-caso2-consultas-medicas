"""Grupos, permisos y reglas de autorización del Caso 2."""
from .models import Medico, Paciente

GRUPO_ADMINS = "Admins"
GRUPO_MEDICOS = "Médicos"
GRUPO_RECEPCIONISTAS = "Recepcionistas"
GRUPO_PACIENTES = "Pacientes"
GRUPOS = (GRUPO_ADMINS, GRUPO_MEDICOS, GRUPO_RECEPCIONISTAS, GRUPO_PACIENTES)

# Permisos granulares por grupo (codename dentro de la app "consultas")
PERMISOS_POR_GRUPO = {
    GRUPO_ADMINS: ["ver_historial_clinico", "agendar_cita", "cancelar_cita", "generar_reportes"],
    GRUPO_MEDICOS: ["ver_historial_clinico", "cancelar_cita"],
    GRUPO_RECEPCIONISTAS: ["agendar_cita", "cancelar_cita"],
    GRUPO_PACIENTES: ["agendar_cita", "cancelar_cita", "ver_historial_clinico"],  # solo lo propio
}

# Horario de atención: weekday() 0=lunes ... 5=sábado
HORARIO_ATENCION = {
    **{d: ("08:00", "18:00") for d in range(0, 5)},  # L-V
    5: ("08:00", "13:00"),  # Sáb
}


def en_grupo(user, nombre):
    return user.is_authenticated and user.groups.filter(name=nombre).exists()


DURACION_CITA_MIN = 30  # cada cita médica dura 30 minutos


def minutos(hora):
    return hora.hour * 60 + hora.minute


def dentro_de_horario(fecha, hora):
    """True si fecha/hora caen dentro del horario de atención (L-V 8-18, Sáb 8-13)."""
    rango = HORARIO_ATENCION.get(fecha.weekday())
    if not rango:
        return False  # domingo
    inicio, fin = rango
    return inicio <= hora.strftime("%H:%M") < fin


def perfil_medico(user):
    if not user.is_authenticated:
        return None
    return Medico.objects.select_related("especialidad").filter(usuario=user).first()


def perfil_paciente(user):
    if not user.is_authenticated:
        return None
    return Paciente.objects.filter(usuario=user).first()
