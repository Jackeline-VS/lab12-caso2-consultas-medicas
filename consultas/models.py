"""Modelos de la Plataforma de Gestión de Consultas Médicas."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.utils import timezone


def validar_no_futura(valor):
    if valor > timezone.localdate():
        raise ValidationError("La fecha no puede ser futura.")


class Especialidad(models.Model):
    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "especialidades"

    def __str__(self):
        return self.nombre


class Medico(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="medico"
    )
    cmp = models.CharField(
        "CMP",
        max_length=6,
        unique=True,
        validators=[RegexValidator(r"^\d{5,6}$", "El CMP debe tener 5 o 6 dígitos (ej: 12345).")],
    )
    especialidad = models.ForeignKey(
        Especialidad, on_delete=models.PROTECT, related_name="medicos"
    )
    consultorio = models.CharField(max_length=40)
    hora_inicio = models.TimeField(default="08:00")
    hora_fin = models.TimeField(default="13:00")

    class Meta:
        ordering = ["usuario__last_name"]

    def __str__(self):
        return f"Dr(a). {self.usuario.get_full_name() or self.usuario.username} - {self.especialidad}"


class Paciente(models.Model):
    class Tipo(models.TextChoices):
        ESTUDIANTE = "estudiante", "Estudiante"
        DOCENTE = "docente", "Docente"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paciente",
    )
    dni = models.CharField(
        "DNI",
        max_length=8,
        unique=True,
        validators=[RegexValidator(r"^\d{8}$", "El DNI debe tener exactamente 8 dígitos numéricos.")],
    )
    nombres = models.CharField(max_length=80)
    apellidos = models.CharField(max_length=80)
    fecha_nacimiento = models.DateField(validators=[validar_no_futura])
    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    codigo_uncp = models.CharField("código UNCP", max_length=15, blank=True)
    email = models.EmailField()
    alergias = models.TextField("alergias conocidas", blank=True)

    class Meta:
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} ({self.dni})"

    def clean(self):
        if self.tipo == self.Tipo.ESTUDIANTE and not self.email.lower().endswith("@uncp.edu.pe"):
            raise ValidationError(
                {"email": "Los estudiantes deben usar su correo institucional @uncp.edu.pe."}
            )

    # --- Campos calculados (RF5) ---
    @property
    def edad(self):
        hoy = timezone.localdate()
        n = self.fecha_nacimiento
        return hoy.year - n.year - ((hoy.month, hoy.day) < (n.month, n.day))

    @property
    def dias_desde_ultima_consulta(self):
        ultima = (
            Consulta.objects.filter(cita__paciente=self)
            .order_by("-creado_en")
            .values_list("creado_en", flat=True)
            .first()
        )
        if not ultima:
            return None
        return (timezone.localdate() - timezone.localtime(ultima).date()).days


class Cita(models.Model):
    class Estado(models.TextChoices):
        PROGRAMADA = "programada", "Programada"
        CANCELADA = "cancelada", "Cancelada"
        COMPLETADA = "completada", "Completada"

    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name="citas")
    medico = models.ForeignKey(Medico, on_delete=models.PROTECT, related_name="citas")
    fecha = models.DateField()
    hora = models.TimeField()
    motivo = models.TextField(
        validators=[MinLengthValidator(20, "El motivo debe tener al menos 20 caracteres.")]
    )
    estado = models.CharField(
        max_length=12, choices=Estado.choices, default=Estado.PROGRAMADA
    )
    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="citas_creadas",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha", "hora"]
        permissions = [
            ("agendar_cita", "Puede agendar citas"),
            ("cancelar_cita", "Puede cancelar citas"),
            ("generar_reportes", "Puede generar reportes"),
        ]

    def __str__(self):
        return f"{self.fecha} {self.hora:%H:%M} - {self.paciente} con {self.medico}"


class Consulta(models.Model):
    """Registro clínico post-atención. Una vez guardado NO se modifica (solo notas)."""

    cita = models.OneToOneField(Cita, on_delete=models.PROTECT, related_name="consulta")
    diagnostico = models.TextField()
    tratamiento = models.TextField()
    medicamentos = models.TextField(blank=True)
    proxima_cita_control = models.DateField(null=True, blank=True)
    adjuntos_descripcion = models.TextField(
        "adjuntos (descripción simulada)", blank=True
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en"]
        permissions = [
            ("ver_historial_clinico", "Puede ver el historial clínico"),
        ]

    def __str__(self):
        return f"Consulta de {self.cita.paciente} ({self.creado_en:%Y-%m-%d})"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError(
                "Una consulta registrada no puede modificarse; agregue una nota."
            )
        super().save(*args, **kwargs)


class NotaConsulta(models.Model):
    consulta = models.ForeignKey(Consulta, on_delete=models.PROTECT, related_name="notas")
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    texto = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado_en"]


class AccesoHistorial(models.Model):
    """Auditoría médica: quién accedió a qué historial (confidencialidad)."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    paciente = models.ForeignKey(
        Paciente, on_delete=models.SET_NULL, null=True, blank=True
    )
    accion = models.CharField(max_length=60)
    ruta = models.CharField(max_length=200, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name_plural = "accesos a historiales"

    def __str__(self):
        return f"{self.fecha:%Y-%m-%d %H:%M} {self.usuario} -> {self.accion}"
