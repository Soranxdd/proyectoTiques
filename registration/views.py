from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.utils.timezone import make_aware
from datetime import datetime
from django.http import HttpResponse
from registration.forms import ReportForm
from tickets.models import Report, Ticket
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
            return redirect('login')
    else:
        return render(request, 'registration/login.html')

def logout_user(request):
    logout(request)
    messages.success(request, 'Sesion terminada')
    return redirect('login')

@method_decorator(login_required, name='dispatch')
class UserListView(ListView):
    model = User
    template_name = 'registration/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        # Para obtener el grupo 'Dueños' **cambio**
        dueño_group = Group.objects.get(name='Dueños')
        # Para excluir usuarios que pertenecen al grupo 'Dueño' y superusuarios
        return User.objects.exclude(groups=dueño_group).exclude(is_superuser=True)

@method_decorator(login_required, name='dispatch')
class ReportListView(ListView):
    model = Report
    template_name = 'registration/report_list.html'
    context_object_name = 'reports'

def create_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role']
        
        # Validaciones
        if User.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
            return render(request, 'registration/create_user.html', {'roles': ['Técnicos', 'Vendedores']})
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "El correo electrónico ya está en uso.")
            return render(request, 'registration/create_user.html', {'roles': ['Técnicos', 'Vendedores']})
        
        if len(password) < 8:
            messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
            return render(request, 'registration/create_user.html', {'roles': ['Técnicos', 'Vendedores']})
        
        if role not in ['Técnicos', 'Vendedores']:
            messages.error(request, "Seleccione un rol válido.")
            return render(request, 'registration/create_user.html', {'roles': ['Técnicos', 'Vendedores']})
        
        # Crear usuario
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Asignar al grupo
        group = Group.objects.get(name=role)
        user.groups.add(group)
        
        messages.success(request, "Usuario creado exitosamente.")
        return redirect('user_list')
    
    return render(request, 'registration/create_user.html', {'roles': ['Técnicos', 'Vendedores']})

def edit_user(request, user_id):
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        user.username = request.POST['username']
        user.email = request.POST['email']
        role = request.POST['role']
        
        # Actualizar grupo
        user.groups.clear()  # Para eliminar grupos anteriores
        group = Group.objects.get(name=role)
        user.groups.add(group)
        
        user.save()
        messages.success(request, f'Usuario {user.username} actualizado con éxito.')
        return redirect('user_list')
    
    return render(request, 'registration/edit_user.html', {'user': user, 'roles': ['Técnicos', 'Vendedores']})

def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, f'Usuario {user.username} eliminado con éxito.')
    return redirect('user_list')

@method_decorator(login_required, name='dispatch')
class DueñoTicketListView(ListView):
    model = Ticket
    template_name = 'registration/dueño_ticket_list.html'
    context_object_name = 'tickets'
    
    def get_queryset(self):
        # Base query
        queryset = Ticket.objects.all()

        # Obtener parámetros del filtro
        tecnico_id = self.request.GET.get('tecnico')
        vendedor_id = self.request.GET.get('vendedor')
        estado = self.request.GET.get('estado')
        fecha = self.request.GET.get('fecha')

        # El filtrado si se envio un parametro
        if tecnico_id:
            queryset = queryset.filter(tecnico_id=tecnico_id)
        if vendedor_id:
            queryset = queryset.filter(vendedor_id=vendedor_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if fecha:
            aware_date = make_aware(datetime.strptime(fecha, "%Y-%m-%d"))
            queryset = queryset.filter(fecha_creacion__date=aware_date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Añadir datos necesarios para los filtros
        context['tecnicos'] = User.objects.filter(groups__name='Técnicos')
        context['vendedores'] = User.objects.filter(groups__name='Vendedores')
        context['estados'] = Ticket.status_ticket  # Enum de estados en el modelo Ticket
        return context

@method_decorator(login_required, name='dispatch')    
class ReportListView(ListView):
    model = Report
    template_name = 'registration/dueño_report_list.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        # Base query
        queryset = Report.objects.all()

        # Obtener parámetros del filtro
        fecha_inicio = self.request.GET.get('fecha_inicio')
        fecha_fin = self.request.GET.get('fecha_fin')
        tipo_reporte = self.request.GET.get('tipo_reporte')

        # El filtrado si se envio un parametro
        if fecha_inicio and fecha_fin:
            queryset = queryset.filter(
                fecha_inicio__gte=fecha_inicio,
                fecha_fin__lte=fecha_fin
            )
            
        if tipo_reporte:
            if tipo_reporte == 'tecnico':
                queryset = queryset.filter(tecnico__isnull=False)
            elif tipo_reporte == 'vendedor':
                queryset = queryset.filter(vendedor__isnull=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Pasar valores actuales de los filtros al contexto para mantenerlos en el formulario
        context['fecha_inicio'] = self.request.GET.get('fecha_inicio', '')
        context['fecha_fin'] = self.request.GET.get('fecha_fin', '')
        context['tipo_reporte'] = self.request.GET.get('tipo_reporte', '')
        return context

@method_decorator(login_required, name='dispatch')    
class ReportCreateView(CreateView):
    model = Report
    form_class = ReportForm
    template_name = 'registration/dueño_report_create.html'
    success_url = reverse_lazy('reports_list')

    def form_valid(self, form):
        # Obtener datos del formulario
        fecha_inicio = form.cleaned_data['fecha_inicio']
        fecha_fin = form.cleaned_data['fecha_fin']
        usuario = form.cleaned_data['usuario']

        # Guardar el reporte sin necesidad de asociar tickets
        reporte = form.save(commit=False)
        reporte.usuario = usuario  # Asegura que el reporte esté asociado al usuario
        reporte.save()

        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')    
class ReportDetailView(DetailView):
    model = Report
    template_name = 'registration/dueño_report_detail.html'
    context_object_name = 'report'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.get_object()
        if report.usuario.groups.filter(name='Técnicos').exists():
            context['rendimiento'] = report.calcular_rendimiento_tecnico()
        elif report.usuario.groups.filter(name='Vendedores').exists():
            context['rendimiento'] = report.calcular_rendimiento_vendedor()
        return context