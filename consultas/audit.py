"""Auditoría médica (RF4): quién accedió a qué historial, con IP y fecha."""
import logging

from .models import AccesoHistorial

logger = logging.getLogger("auditoria")


def obtener_ip(request):
    # REMOTE_ADDR: X-Forwarded-For puede ser falsificado por el cliente.
    return request.META.get("REMOTE_ADDR")


def auditar(request, accion, paciente=None, detalle=""):
    usuario = request.user if request.user.is_authenticated else None
    ip = obtener_ip(request)
    AccesoHistorial.objects.create(
        usuario=usuario, paciente=paciente, accion=accion, ruta=request.path, ip=ip
    )
    logger.info(
        "ACCION=%s usuario=%s paciente=%s ip=%s %s",
        accion, usuario.username if usuario else "anonimo",
        paciente.dni if paciente else "-", ip, detalle,
    )
