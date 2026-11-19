"""Context processor: perfil del usuario para las plantillas."""
from .roles import perfil_medico, perfil_paciente


def perfiles(request):
    user = request.user
    if not user.is_authenticated:
        return {}
    paciente = perfil_paciente(user)
    return {
        "es_medico": perfil_medico(user) is not None,
        "mi_paciente_id": paciente.pk if paciente else None,
    }
