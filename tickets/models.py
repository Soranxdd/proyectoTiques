import uuid
from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Equipo(models.Model):
    tipo_equipo = (
        ('notebook', 'Notebook'),
        ('PC', 'PC de escritorio'),
        ('impresora', 'Impresora'),
        # Se podra agregar mas tipos si es necesario
    )
    folio = models.CharField(max_length=20, unique=True, blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=tipo_equipo)
    marca = models.CharField(max_length=50)
    observaciones = models.TextField(null=True, blank=True)
    incluye_cargador = models.BooleanField(default=False)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='equipos_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.marca}"
    
    def save(self, *args, **kwargs):
        if not self.folio:  # Si el folio está vacío
            self.folio = f"EQP-{Equipo.objects.count() + 1}"  # Generar un folio único
        super().save(*args, **kwargs)  # Guarda el objeto con el folio asignado
            
class Ticket(models.Model):
    status_ticket = (
        ('pendiente', 'Pendiente'),
        ('diagnostico', 'En diagnostico'),
        ('reparacion', 'En reparacion'),
        ('listo', 'Listo para Retiro')
    )
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='ticket')
    vendedor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_vendidos')
    tecnico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_asignados')
    estado = models.CharField(max_length=20, choices=status_ticket, default='pendiente')
    descripcion_reparacion = models.TextField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    prioridad = models.BooleanField(default=False)

    def __str__(self):
        return f"Ticket para {self.equipo}"
    
class Report(models.Model):
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reportes'
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reporte del {self.fecha_inicio} al {self.fecha_fin}"
    
    def calcular_rendimiento_tecnico(self):
        # Verifica si el usuario pertenece al grupo 'Técnicos'
        if self.usuario.groups.filter(name='Técnicos').exists():
            # Filtra los tickets asignados al técnico dentro del rango de fechas
            tickets = Ticket.objects.filter(
                tecnico=self.usuario,
                fecha_creacion__range=(self.fecha_inicio, self.fecha_fin)
            )
            
            print(tickets)
            tickets_resueltos = tickets.filter(estado='listo').count()
            tickets_urgentes = tickets.filter(prioridad=True).count()
            tiempo_promedio_respuesta = (
                tickets.filter(estado='listo')
                .aggregate(promedio=models.Avg(models.F('fecha_actualizacion') - models.F('fecha_creacion')))['promedio']
            )
            return {
                'tickets_resueltos': tickets_resueltos,
                'tickets_urgentes': tickets_urgentes,
                'tiempo_promedio_respuesta': tiempo_promedio_respuesta,
            }
        return None
    
    def calcular_rendimiento_vendedor(self):
        # Verifica si el usuario pertenece al grupo 'Vendedores'
        if self.usuario.groups.filter(name='Vendedores').exists():
            # Filtra los tickets creados por el vendedor dentro del rango de fechas
            tickets = Ticket.objects.filter(
                vendedor=self.usuario,
                fecha_creacion__range=(self.fecha_inicio, self.fecha_fin)
            )
            tickets_creados = tickets.count()
            equipos_registrados = Equipo.objects.filter(
                creado_por=self.usuario,
                fecha_creacion__range=(self.fecha_inicio, self.fecha_fin)
            ).count()
            tickets_completados = tickets.filter(estado='listo').count()
            relacion_tickets = (tickets_creados and (tickets_completados / tickets_creados * 100)) or 0
            return {
                'tickets_creados': tickets_creados,
                'equipos_registrados': equipos_registrados,
                'relacion_tickets': relacion_tickets,
            }
        return None
    
class HistorialTicket(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='historial', on_delete=models.CASCADE)
    descripcion = models.TextField(default='Descripcion')  # Descripción del cambio realizado
    fecha = models.DateTimeField(auto_now_add=True)  # Fecha del cambio
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # Usuario que realizó el cambio (opcional)

    def __str__(self):
        return f"Historial de Ticket {self.ticket.id} - {self.fecha}"
    
