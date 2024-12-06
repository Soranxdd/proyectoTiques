from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from tickets.forms import EquipoForm
from tickets.models import Equipo, Ticket
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Create your views here.
@method_decorator(login_required, name='dispatch')
class RegistrarEquipoCreateView(CreateView):
    model = Equipo
    template_name = 'equipo/vendedor_registrar_equipo.html'
    form_class = EquipoForm
    success_url = reverse_lazy('consulta_tickets')
    
    def form_valid(self, form):
        # Aquí puedes agregar lógica adicional si es necesario
        form.instance.creado_por = self.request.user  # Por ejemplo, asignar el usuario actual al equipo
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class ObservacionesUpdateView(UpdateView):
    model = Equipo
    fields = ['observaciones']
    template_name = 'equipo/vendedor_equipo_modificar_observaciones.html'
    
    def get_success_url(self):
        # Redirigir al detalle del ticket una vez editadas las observaciones
        ticket_id = self.kwargs['pk']
        return reverse_lazy('detail', kwargs={'pk': ticket_id})

    def get_object(self, queryset=None):
        # Obtener el objeto equipo asociado al id del ticket
        ticket_id = self.kwargs['pk']
        ticket = Ticket.objects.get(id=ticket_id)
        return ticket.equipo