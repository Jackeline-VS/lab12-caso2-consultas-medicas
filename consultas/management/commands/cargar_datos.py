"""Datos de prueba: 8 médicos, 15 pacientes, 30 citas, grupos y permisos."""
from datetime import date, timedelta, time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from consultas.models import Cita, Consulta, Especialidad, Medico, Paciente
from consultas.roles import (
    GRUPO_ADMINS, GRUPO_MEDICOS, GRUPO_PACIENTES, GRUPO_RECEPCIONISTAS,
    GRUPOS, PERMISOS_POR_GRUPO,
)

CLAVE = "Uncp2026*"
MANANA, TARDE = (time(8, 0), time(13, 0)), (time(14, 0), time(18, 0))

ESPECIALIDADES = ["Medicina General", "Odontología", "Psicología", "Nutrición", "Obstetricia"]
# username, nombre, apellido, especialidad, consultorio, horario
MEDICOS = [
    ("med1", "Jorge", "Salazar", "Medicina General", "Consultorio 101", MANANA),
    ("med2", "Lucia", "Ramos", "Medicina General", "Consultorio 102", MANANA),
    ("med3", "Pedro", "Castillo", "Odontología", "Consultorio 201", MANANA),
    ("med4", "Elena", "Vega", "Odontología", "Consultorio 202", MANANA),
    ("med5", "Raul", "Torres", "Psicología", "Consultorio 301", TARDE),
    ("med6", "Marta", "Lozano", "Psicología", "Consultorio 302", TARDE),
    ("med7", "Ivan", "Campos", "Nutrición", "Consultorio 401", TARDE),
    ("med8", "Sofia", "Medina", "Obstetricia", "Consultorio 501", TARDE),
]
NOMBRES = ["Ana", "Luis", "Maria", "Carlos", "Rosa", "Diego", "Lucia", "Mario",
           "Paula", "Jose", "Karen", "Hugo", "Elsa", "Raul", "Nora"]
APELLIDOS = ["Quispe", "Mendoza", "Rojas", "Huaman", "Paucar", "Gomez", "Flores", "Rivera",
             "Soto", "Vargas", "Cruz", "Ortiz", "Peña", "Rios", "Leon"]
DIAGNOSTICOS = [
    "Cuadro gripal leve sin complicaciones",
    "Caries dental en pieza molar",
    "Cuadro de estrés académico moderado",
    "Control nutricional y plan de alimentación",
    "Control prenatal de rutina",
]


class Command(BaseCommand):
    help = "Carga datos de prueba (idempotente)."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        grupos = {n: Group.objects.get_or_create(name=n)[0] for n in GRUPOS}

        permisos = Permission.objects.filter(content_type__app_label="consultas")
        grupos[GRUPO_ADMINS].permissions.set(permisos)
        extra = {
            GRUPO_MEDICOS: ["view_cita", "view_paciente"],
            GRUPO_RECEPCIONISTAS: ["add_paciente", "change_paciente", "view_paciente", "view_cita"],
            GRUPO_PACIENTES: [],
        }
        for nombre, codenames in PERMISOS_POR_GRUPO.items():
            if nombre != GRUPO_ADMINS:
                grupos[nombre].permissions.set(
                    permisos.filter(codename__in=codenames + extra[nombre])
                )

        def usuario(username, nombre, apellido, grupo, admin=False):
            u, creado = User.objects.get_or_create(
                username=username,
                defaults=dict(
                    first_name=nombre, last_name=apellido,
                    email=f"{username}@uncp.edu.pe",
                    is_staff=admin, is_superuser=admin,
                ),
            )
            if creado:
                u.set_password(CLAVE)
                u.save()
            u.groups.add(grupos[grupo])
            return u

        usuario("admin1", "Ana", "Quispe", GRUPO_ADMINS, admin=True)
        rec = usuario("rec1", "Rosa", "Paucar", GRUPO_RECEPCIONISTAS)

        esp = {n: Especialidad.objects.get_or_create(nombre=n)[0] for n in ESPECIALIDADES}
        medicos = []
        for i, (uname, nom, ape, e, cons, (ini, fin)) in enumerate(MEDICOS):
            medico, _ = Medico.objects.get_or_create(
                usuario=usuario(uname, nom, ape, GRUPO_MEDICOS),
                defaults=dict(cmp=str(10001 + i), especialidad=esp[e], consultorio=cons,
                              hora_inicio=ini, hora_fin=fin),
            )
            medicos.append(medico)

        pacientes = []
        for i in range(15):
            estudiante = i % 3 != 0
            nombre, apellido = NOMBRES[i], APELLIDOS[i]
            u = usuario(f"pac{i + 1}", nombre, apellido, GRUPO_PACIENTES) if i < 3 else None
            paciente, _ = Paciente.objects.get_or_create(
                dni=f"7000{i + 1:04d}",
                defaults=dict(
                    usuario=u, nombres=nombre, apellidos=apellido,
                    fecha_nacimiento=(date(2001 + i % 5, 1 + i % 12, 1 + i % 27)
                                      if estudiante else date(1975 + i, 1 + i % 12, 1 + i % 27)),
                    tipo="estudiante" if estudiante else "docente",
                    codigo_uncp=f"2022{i + 1:04d}I" if estudiante else "",
                    email=f"{apellido.lower()}{i + 1}@uncp.edu.pe",
                    alergias="Penicilina" if i % 5 == 0 else "",
                ),
            )
            pacientes.append(paciente)

        if Cita.objects.exists():
            self.stdout.write("Las citas ya existen: no se duplican.")
            return

        hoy = timezone.localdate()
        for i in range(30):
            medico, paciente = medicos[i % 8], pacientes[i % 15]
            tarde = i % 8 >= 4
            dia = hoy + timedelta(days=i - 12)
            while dia.weekday() == 6 or (tarde and dia.weekday() == 5):
                dia += timedelta(days=1)  # sin domingos; sábado solo por la mañana
            hora = time(14 + (i // 8) % 4, 0) if tarde else time(9 + (i // 8) % 4, 0)
            if dia < hoy:
                estado = Cita.Estado.COMPLETADA
            elif i % 7 == 0:
                estado = Cita.Estado.CANCELADA
            else:
                estado = Cita.Estado.PROGRAMADA
            cita = Cita.objects.create(
                paciente=paciente, medico=medico, fecha=dia, hora=hora,
                motivo=f"Consulta de control y evaluación general número {i + 1}",
                estado=estado, creada_por=rec,
            )
            if estado == Cita.Estado.COMPLETADA:
                Consulta.objects.create(
                    cita=cita, diagnostico=DIAGNOSTICOS[i % 5],
                    tratamiento="Reposo, hidratación y control en una semana",
                    medicamentos="Paracetamol 500 mg cada 8 horas" if i % 2 == 0 else "",
                )
        self.stdout.write(self.style.SUCCESS(
            "Datos cargados. Usuarios: admin1, rec1, med1-med8, pac1-pac3 | clave: " + CLAVE
        ))
