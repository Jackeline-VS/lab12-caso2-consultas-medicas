"""Grupos, permisos y reglas de autorización del Caso 2."""

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
