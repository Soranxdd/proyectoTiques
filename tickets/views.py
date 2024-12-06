from datetime import datetime
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from .models import Equipo, Ticket, HistorialTicket
from .forms import EquipoForm, HistorialForm, RegistrarReparacionForm
from django.utils.timezone import make_aware


# Create your views here.
# Listar tickets, vendedor
@method_decorator(login_required, name='dispatch')
class TicketListView(ListView):
    model = Ticket
    template_name = 'tickets/vendedor_consultar_tickets.html' # Ruta del template
    context_object_name = 'tickets'
    paginate_by = 10  # Mostrar 10 tickets por página

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtros opcionales
        filtro_fecha = self.request.GET.get('filtroFecha', None)
        filtro_estado = self.request.GET.get('filtroEstado', None)
        filtro_equipo = self.request.GET.get('filtroEquipo', None)

        # Aplicar los filtros si existen
        if filtro_fecha:
            queryset = queryset.filter(fecha_creacion__date=filtro_fecha)
        if filtro_estado:
            queryset = queryset.filter(estado=filtro_estado)
        if filtro_equipo:
            queryset = queryset.filter(equipo__icontains=filtro_equipo)

        return queryset

# Mostrar detalles de un ticket, vendedor
@method_decorator(login_required, name='dispatch')
class TicketDetailView(DetailView):
    model = Ticket
    template_name = 'tickets/vendedor_ticket_detail.html'
    context_object_name = 'ticket'

# Asignar tecnico, vendedor
@method_decorator(login_required, name='dispatch')
def asignar_tecnico(request, ticket_id):
    # Verificar que el usuario actual es un vendedor
    if not request.user.groups.filter(name='Vendedores').exists():
        messages.error(request, "No tienes permiso para asignar técnicos.")
        return redirect('home') 
    
    # Obtenemos el ticket segun el id del ticket
    ticket = get_object_or_404(Ticket, id=ticket_id)
    # Filtramos los usuarios dentro del grupo técnicos
    tecnicos = User.objects.filter(groups__name='Técnicos')

    # Si el formulario fue enviado (método POST), asignar el técnico al ticket
    if request.method == 'POST':
        # Guardamos el id enviado
        tecnico_id = request.POST.get('tecnico_id')
        # Obtenemos al tecnico segun su id
        tecnico = get_object_or_404(User, id=tecnico_id)
        
        # Guardar el estado anterior solo para el historial
        estado_anterior = ticket.estado 

        ticket.tecnico = tecnico    # Actualizar el técnico asignado
        ticket.estado = 'diagnostico'   # Cambiar el estado a "diagnostico"
        ticket.save()   #Guardar
        
        # Registrar en el historial
        descripcion = f"Técnico {tecnico.username} asignado al ticket. Estado cambiado de {estado_anterior} a {ticket.estado}."
        HistorialTicket.objects.create(
            ticket=ticket,
            descripcion=descripcion,
            usuario=request.user  # Usuario que realizo el cambio
        )
        
        return redirect('detail', ticket_id)  # Redirigir al detalle del ticket

    return render(request, 'tickets/vendedor_ticket_asignar_tecnico.html', {'ticket': ticket, 'tecnicos': tecnicos})

@method_decorator(login_required, name='dispatch')
def marcar_prioridad(request, ticket_id):
    # Obtener el ticket
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Invertir el estado de prioridad
    prioridad_anterior = ticket.prioridad
    ticket.prioridad = not ticket.prioridad  # Cambiar True a False o viceversa
    ticket.save()

    # Registrar en el historial
    descripcion = (
        f"Prioridad del ticket cambiada de {'Alta' if prioridad_anterior else 'Baja'} "
        f"a {'Alta' if ticket.prioridad else 'Baja'}."
    )
    HistorialTicket.objects.create(
        ticket=ticket,
        descripcion=descripcion,
        usuario=request.user  # Usuario que realizó el cambio
    )

    # Redirigir al detalle del ticket o lista
    return redirect('detail', pk=ticket_id)


# Opciones tecnico
@method_decorator(login_required, name='dispatch')
class TicketsAsignadosListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/tecnico_tickets.html'
    context_object_name = 'tickets'
    paginate_by = 10

    def get_queryset(self):
        # Filtrar los tickets asignados al técnico autenticado
        queryset = Ticket.objects.filter(tecnico=self.request.user)
        
        # Filtrar por estado si el parámetro está presente en la URL
        estado = self.request.GET.get('estado', 'diagnostico')  # Estado por defecto: 'diagnostico'
        queryset = queryset.filter(estado=estado)
        
        # Obtener parámetros del filtro
        fecha = self.request.GET.get('fecha')
        prioridad = self.request.GET.get('prioridad')
        
        if fecha:
            aware_date = make_aware(datetime.strptime(fecha, "%Y-%m-%d"))
            queryset = queryset.filter(fecha_creacion__date=aware_date)
        if prioridad == '1':  # Con prioridad
            queryset = queryset.filter(prioridad=True)
        elif prioridad == '0':  # Sin prioridad
            queryset = queryset.filter(prioridad=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pasar el estado actual al contexto para destacar el botón activo
        context['estado_actual'] = self.request.GET.get('estado', 'diagnostico')
        # Pasar la prioridad actual al contexto para mantener el filtro seleccionado
        context['prioridad_actual'] = self.request.GET.get('prioridad', '')
        
        return context
    
@method_decorator(login_required, name='dispatch')
class TecnicoTicketDetailView(DetailView):
    model = Ticket
    template_name = 'tickets/tecnico_ticket_detail.html'
    context_object_name = 'ticket'

def aceptar_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    # Verifica que el ticket está en estado 'diagnostico'
    if ticket.estado != 'diagnostico':
        return HttpResponseForbidden("Este ticket no puede ser aceptado en su estado actual.")

    # Guardar el estado anterior para registrar en el historial
    estado_anterior = ticket.estado

    # Cambia el estado a 'reparacion'
    ticket.estado = 'reparacion'
    ticket.save()

    # Registrar en el historial
    descripcion = f"Estado del ticket cambiado de {estado_anterior} a {ticket.estado}."
    HistorialTicket.objects.create(
        ticket=ticket,
        descripcion=descripcion,
        usuario=request.user  # Usuario que realizó el cambio
    )

    # Redirige a la lista de tickets asignados
    return redirect('tickets_asignados')

def registrar_avance(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Verificar que el ticket está en estado 'reparacion'
    if ticket.estado != 'reparacion':
        return HttpResponseForbidden("Solo se pueden registrar avances en tickets en reparación.")

    if request.method == 'POST':
        form = HistorialForm(request.POST)
        if form.is_valid():
            avance = form.save(commit=False)
            avance.ticket = ticket
            avance.usuario = request.user
            avance.save()
            return redirect('tecnico_detail', pk=ticket_id)  # Cambia según tu vista de detalles
    else:
        form = HistorialForm()

    return render(request, 'tickets/tecnico_registrar_avance.html', {'ticket': ticket, 'form': form})

def marcar_listo(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Verificar que el ticket está en estado 'reparacion'
    if ticket.estado != 'reparacion':
        return HttpResponseForbidden("Solo se pueden marcar como listos los tickets en reparación.")

    if request.method == 'POST':
        form = HistorialForm(request.POST)
        if form.is_valid():
            # Guardar el avance con descripción proporcionada
            avance = form.save(commit=False)
            avance.ticket = ticket
            avance.usuario = request.user
            avance.save()

            # Cambiar el estado del ticket a 'listo'
            ticket.estado = 'listo'
            ticket.save()

            return redirect('tickets_asignados')  # Cambia según tu vista

    else:
        form = HistorialForm()

    return render(request, 'tickets/tecnico_marcar_listo.html', {'ticket': ticket, 'form': form})