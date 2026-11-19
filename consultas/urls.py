from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("citas/", views.citas, name="citas"),
    path("citas/nueva/", views.cita_nueva, name="cita_nueva"),
    path("citas/<int:pk>/cancelar/", views.cita_cancelar, name="cita_cancelar"),
    path("citas/<int:cita_id>/consulta/", views.consulta_registrar, name="consulta_registrar"),
    path("historial/<int:paciente_id>/", views.historial, name="historial"),
    path("pacientes/nuevo/", views.paciente_nuevo, name="paciente_nuevo"),
    path("reportes/", views.reportes, name="reportes"),
]
