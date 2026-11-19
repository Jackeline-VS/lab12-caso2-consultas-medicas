"""Middleware propios del Caso 2 (RF4)."""
import logging
import re

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time

from .audit import obtener_ip
from .models import AccesoHistorial, Cita, Paciente
from .roles import dentro_de_horario, perfil_medico

logger = logging.getLogger("auditoria")
RE_HISTORIAL = re.compile(r"^/historial/(\d+)/$")


class AuditoriaMedicaMiddleware:
    """Registra cada petición y los accesos a historiales clínicos (confidencialidad)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(("/static/", "/favicon")):
            return response

        usuario = request.user if request.user.is_authenticated else None
        nombre = usuario.username if usuario else "anonimo"
        ip = obtener_ip(request)
        logger.info(
            "REQUEST %s %s -> %s | usuario=%s ip=%s",
            request.method, request.path, response.status_code, nombre, ip,
        )

        coincide = RE_HISTORIAL.match(request.path)
        if coincide:
            paciente = Paciente.objects.filter(pk=coincide.group(1)).first()
            accion = {200: "VER_HISTORIAL", 403: "ACCESO_DENEGADO_HISTORIAL"}.get(
                response.status_code
            )
            if accion:
                AccesoHistorial.objects.create(
                    usuario=usuario, paciente=paciente, accion=accion,
                    ruta=request.path, ip=ip,
                )
                log = logger.warning if response.status_code == 403 else logger.info
                log(
                    "HISTORIAL %s usuario=%s paciente=%s ip=%s",
                    accion, nombre, paciente.dni if paciente else "?", ip,
                )
        elif response.status_code == 403:
            logger.warning("ACCESO NO AUTORIZADO usuario=%s ip=%s ruta=%s", nombre, ip, request.path)
            AccesoHistorial.objects.create(
                usuario=usuario, accion="ACCESO_NO_AUTORIZADO", ruta=request.path, ip=ip
            )
        elif (
            response.status_code == 302
            and usuario is None
            and response["Location"].startswith(reverse("login"))
        ):
            logger.warning("INTENTO SIN AUTENTICAR ip=%s ruta=%s", ip, request.path)
        return response


class HorarioAtencionMiddleware:
    """Impide agendar citas fuera del horario de atención (L-V 8-18, Sáb 8-13)."""

    RUTA = "/citas/nueva/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.path == self.RUTA and request.user.is_authenticated:
            fecha = parse_date(request.POST.get("fecha", ""))
            hora = parse_time(request.POST.get("hora", ""))
            if fecha and hora and not dentro_de_horario(fecha, hora):
                logger.warning(
                    "HORARIO FUERA DE ATENCION usuario=%s fecha=%s hora=%s",
                    request.user.username, fecha, hora,
                )
                messages.error(
                    request,
                    "Las citas solo se agendan en horario de atención "
                    "(L-V 8:00-18:00, Sáb 8:00-13:00).",
                )
                return redirect(request.path)
        return self.get_response(request)
