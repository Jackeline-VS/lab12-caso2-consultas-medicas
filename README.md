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

## Avance
- [x] Esqueleto del proyecto y configuración de sesiones/cookies (20 min)
- [x] Modelos: Especialidad, Medico, Paciente, Cita, Consulta, NotaConsulta, AccesoHistorial
- [x] Grupos, permisos y horario de atención (constantes)
- [ ] Formulario de cita con validaciones cruzadas (RF2)
- [ ] Middleware: auditoría médica, horario, alertas (RF4)
- [ ] Login diferenciado y control de permisos (RF3)
- [ ] Django Admin: agenda, estadísticas, acciones masivas (RF5)
- [ ] Datos de prueba (8 médicos, 15 pacientes, 30 citas)
- [ ] Diagrama de roles y permisos
