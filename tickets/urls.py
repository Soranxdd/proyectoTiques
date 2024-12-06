from django.urls import path
from .views import TicketListView, TicketDetailView, TicketsAsignadosListView, TecnicoTicketDetailView
from . import views

urlpatterns = [
    path('vendedor/consulta_tickets', TicketListView.as_view(), name='consulta_tickets'),
    path('vendedor/ticket_detail/<int:pk>', TicketDetailView.as_view(), name='detail'),
    path('vendedor/<int:ticket_id>/asignar_tecnico/', views.asignar_tecnico, name='asignar_tecnico'),
    path('tecnico/tickets_asignados/', TicketsAsignadosListView.as_view(), name='tickets_asignados'),
    path('tecnico/ticket_detail/<int:pk>', TecnicoTicketDetailView.as_view(), name='tecnico_detail'),
    path('ticket/<int:pk>/aceptar/', views.aceptar_ticket, name='aceptar_ticket'),
    path('ticket/<int:ticket_id>/registrar_avance/', views.registrar_avance, name='registrar_avance'),
    path('ticket/<int:ticket_id>/listo/', views.marcar_listo, name='marcar_listo'),
    path('ticket/<int:ticket_id>/prioridad/', views.marcar_prioridad, name='marcar_prioridad')
]