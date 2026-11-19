# Caso 2 - Plataforma de Gestión de Consultas Médicas

**Práctica Grupal Semana 12** - Desarrollo de Aplicaciones Web (IS093A) - UNCP,
Facultad de Ingeniería de Sistemas.
Temas: formularios, Django Admin, middleware, sesiones, autenticación y autorización.

**Autora:** Jackeline Vivanco Solano (código 2022100549I)

## Requisitos
- Python 3.10 o superior
- Git

## Instalación (Windows, PowerShell)
```powershell
git clone https://github.com/Jackeline-VS/lab12-caso2-consultas-medicas.git
cd lab12-caso2-consultas-medicas
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations consultas
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Abrir http://127.0.0.1:8000/admin/

> `db.sqlite3` y `venv/` no se versionan (ver `.gitignore`).

## Grupos y permisos
| Grupo | Permisos |
|---|---|
| Admins | Todos (incluye `generar_reportes`) |
| Médicos | `ver_historial_clinico`, `cancelar_cita` |
| Recepcionistas | `agendar_cita`, `cancelar_cita` |
| Pacientes | `agendar_cita`, `cancelar_cita`, `ver_historial_clinico` (solo el propio) |

Sesión con timeout de **20 minutos** de inactividad (información sensible).

## Estructura
```
config/        settings, urls, wsgi/asgi
consultas/     app: models, roles, (forms, views, admin, middleware)
templates/     plantillas
```

## Flujo de trabajo Git
- `main`: rama estable, solo recibe Pull Requests.
- `dev/integrante-1`: modelos, formularios, validaciones, admin, plantillas.
- `dev/integrante-2`: settings, middleware, autenticación, grupos y permisos.

## Datos de prueba
```powershell
python manage.py cargar_datos
```
Usuarios (clave `Uncp2026*`): `admin1`, `rec1` (recepcionista), `med1`-`med8` (médicos),
`pac1`-`pac3` (pacientes).

## Reglas de negocio implementadas
- DNI de 8 dígitos, CMP de 5-6 dígitos, fecha de nacimiento no futura, email `@uncp.edu.pe` para estudiantes.
- Cita: motivo de al menos 20 caracteres, médico filtrado por especialidad, slot libre,
  sin citas superpuestas del médico (30 min), un paciente no puede tener 2 citas el mismo día.
- La consulta registrada no se modifica (solo se agregan notas).
- Historial clínico: solo médicos y el propio paciente; cada acceso queda auditado.
- Trazabilidad de cambios en el admin: botón "Historial" de cada registro (quién, cuándo, qué).

## Middleware
1. `AuditoriaMedicaMiddleware`: registra peticiones, accesos a historiales y accesos no autorizados.
2. `HorarioAtencionMiddleware`: bloquea agendar fuera de L-V 8-18 / Sáb 8-13.
3. `AlertasMedicoMiddleware`: al iniciar sesión avisa al médico de sus citas pendientes.

## Seguridad
CSRF en todos los formularios POST, contraseñas con PBKDF2, cookies HttpOnly,
timeout de 20 min por inactividad, sanitización de textos clínicos.

## Avance
- [x] Esqueleto, sesiones y cookies seguras (20 min)
- [x] Modelos y grupos/permisos
- [x] Formularios con validaciones cruzadas (RF1, RF2)
- [x] Django Admin: agenda, filtros, acciones y campos calculados (RF5)
- [x] Middleware de auditoría, horario y alertas (RF4)
- [x] Login, permisos por rol y vistas protegidas (RF3)
- [x] Reportes: citas por especialidad, médicos y pacientes frecuentes
- [x] Datos de prueba (8 médicos, 15 pacientes, 30 citas)
- [ ] Capturas y diagrama de roles (informe PDF)
