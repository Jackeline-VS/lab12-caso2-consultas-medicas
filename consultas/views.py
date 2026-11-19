"""Vistas del Caso 2: permisos por codename + reglas a nivel de objeto."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from .audit import auditar
from .forms import CitaForm, ConsultaForm, NotaConsultaForm, PacienteForm
from .models import Cita, Consulta, Medico, Paciente
from .roles import GRUPO_ADMINS, GRUPO_RECEPCIONISTAS, en_grupo, perfil_medico, perfil_paciente


def permiso_requerido(codename):
    """Exige login y el permiso `consultas.<codename>` (si no, 403 auditado)."""

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.has_perm(f"consultas.{codename}"):
                raise PermissionDenied
            return vista(request, *args, **kwargs)

        return login_required(envoltura)

    return decorador


def ve_todo(user):
    return user.is_superuser or en_grupo(user, GRUPO_ADMINS) or en_grupo(user, GRUPO_RECEPCIONISTAS)


@login_required
def inicio(request):
    return render(request, "consultas/inicio.html")


@login_required
def citas(request):
    user = request.user
    medico, paciente = perfil_medico(user), perfil_paciente(user)
    qs = Cita.objects.select_related("paciente", "medico__usuario", "medico__especialidad")
    todo = ve_todo(user)
    if todo:
        pass
    elif medico:
        qs = qs.filter(medico=medico)
    elif paciente:
        qs = qs.filter(paciente=paciente)
    else:
        raise PermissionDenied

    fecha = parse_date(request.GET.get("fecha", ""))
    if fecha:
        qs = qs.filter(fecha=fecha)

    lista = list(qs)
    for c in lista:
        programada = c.estado == Cita.Estado.PROGRAMADA
        propia = (medico and c.medico_id == medico.id) or (paciente and c.paciente_id == paciente.id)
        c.puede_cancelar = programada and user.has_perm("consultas.cancelar_cita") and (todo or propia)
        c.puede_atender = programada and medico is not None and c.medico_id == medico.id
        c.puede_historial = medico is not None or (paciente and c.paciente_id == paciente.id)
    return render(request, "consultas/citas.html", {"citas": lista, "fecha": fecha})


@permiso_requerido("agendar_cita")
def cita_nueva(request):
    paciente_fijo = None
    if not ve_todo(request.user):
        paciente_fijo = perfil_paciente(request.user)
        if paciente_fijo is None:
            raise PermissionDenied
    if request.method == "POST":
        form = CitaForm(request.POST, paciente_fijo=paciente_fijo)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.paciente = paciente_fijo or form.cleaned_data["paciente"]
            cita.creada_por = request.user
            cita.save()
            auditar(request, "CITA_AGENDADA", cita.paciente, f"{cita.fecha} {cita.hora:%H:%M}")
            messages.success(request, "Cita agendada correctamente.")
            return redirect("citas")
    else:
        form = CitaForm(paciente_fijo=paciente_fijo)
    return render(request, "consultas/cita_form.html", {
        "form": form, "titulo": "Agendar cita médica", "boton": "Agendar",
    })


@require_POST
@permiso_requerido("cancelar_cita")
def cita_cancelar(request, pk):
    cita = get_object_or_404(
        Cita.objects.select_related("paciente", "medico"), pk=pk, estado=Cita.Estado.PROGRAMADA
    )
    medico, paciente = perfil_medico(request.user), perfil_paciente(request.user)
    propia = (medico and cita.medico_id == medico.id) or (paciente and cita.paciente_id == paciente.id)
    if not (ve_todo(request.user) or propia):
        raise PermissionDenied
    cita.estado = Cita.Estado.CANCELADA
    cita.save(update_fields=["estado"])
    auditar(request, "CITA_CANCELADA", cita.paciente, f"{cita.fecha} {cita.hora:%H:%M}")
    messages.success(request, "Cita cancelada.")
    return redirect("citas")


@login_required
def consulta_registrar(request, cita_id):
    medico = perfil_medico(request.user)
    if medico is None:
        raise PermissionDenied
    cita = get_object_or_404(
        Cita.objects.select_related("paciente", "medico__usuario"),
        pk=cita_id, estado=Cita.Estado.PROGRAMADA,
    )
    if cita.medico_id != medico.id:
        raise PermissionDenied  # un médico solo atiende sus propias citas
    form = ConsultaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            consulta = form.save(commit=False)
            consulta.cita = cita
            consulta.save()
            cita.estado = Cita.Estado.COMPLETADA
            cita.save(update_fields=["estado"])
            auditar(request, "CONSULTA_REGISTRADA", cita.paciente)
        messages.success(request, "Consulta registrada. La cita quedó completada.")
        return redirect("historial", paciente_id=cita.paciente_id)
    return render(request, "consultas/formulario.html", {
        "form": form, "titulo": f"Registrar consulta de {cita.paciente}",
        "subtitulo": f"Cita del {cita.fecha:%d/%m/%Y} a las {cita.hora:%H:%M}",
        "boton": "Guardar consulta",
    })


@login_required
def historial(request, paciente_id):
    """Historial clínico: solo médicos y el propio paciente (confidencial)."""
    paciente = get_object_or_404(Paciente.objects.select_related("usuario"), pk=paciente_id)
    medico = perfil_medico(request.user)
    propio = paciente.usuario_id == request.user.id
    if not request.user.has_perm("consultas.ver_historial_clinico") or not (propio or medico):
        raise PermissionDenied

    if request.method == "POST":
        if medico is None:
            raise PermissionDenied
        consulta = get_object_or_404(
            Consulta, pk=request.POST.get("consulta_id"), cita__paciente=paciente
        )
        nota_form = NotaConsultaForm(request.POST)
        if nota_form.is_valid():
            nota = nota_form.save(commit=False)
            nota.consulta, nota.autor = consulta, request.user
            nota.save()
            auditar(request, "NOTA_AGREGADA", paciente)
            messages.success(request, "Nota agregada a la consulta.")
        else:
            messages.error(request, "La nota debe tener al menos 5 caracteres.")
        return redirect("historial", paciente_id=paciente.pk)

    consultas = (
        Consulta.objects.filter(cita__paciente=paciente)
        .select_related("cita__medico__usuario", "cita__medico__especialidad")
        .prefetch_related("notas__autor")
    )
    return render(request, "consultas/historial.html", {"paciente": paciente, "consultas": consultas})


@permiso_requerido("add_paciente")
def paciente_nuevo(request):
    form = PacienteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        paciente = form.save()
        auditar(request, "PACIENTE_REGISTRADO", paciente)
        messages.success(request, "Paciente registrado correctamente.")
        return redirect("citas")
    return render(request, "consultas/formulario.html", {
        "form": form, "titulo": "Registrar paciente", "boton": "Registrar",
    })


@permiso_requerido("generar_reportes")
def reportes(request):
    por_especialidad = (
        Cita.objects.values("medico__especialidad__nombre")
        .annotate(total=Count("id")).order_by("-total")
    )
    medicos_top = (
        Medico.objects.select_related("usuario", "especialidad")
        .annotate(total=Count("citas__consulta")).order_by("-total")[:5]
    )
    pacientes_frecuentes = (
        Paciente.objects.annotate(total=Count("citas")).order_by("-total", "apellidos")[:5]
    )
    return render(request, "consultas/reportes.html", {
        "por_especialidad": por_especialidad,
        "medicos_top": medicos_top,
        "pacientes_frecuentes": pacientes_frecuentes,
    })
