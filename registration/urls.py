from django.urls import path
from . import views
from .views import DueñoTicketListView, UserListView, ReportDetailView, ReportListView, ReportCreateView, ReportDetailView

urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('gerente/users/', views.UserListView.as_view(), name='user_list'),
    path('gerente/users/create/', views.create_user, name='create_user'),
    path('gerente/users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('gerente/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('dueño/tickets_list', DueñoTicketListView.as_view(), name='dueño_ticket_list'),
    path('dueño/report_list', ReportListView.as_view(), name='reports_list'),
    path('dueño/report_create', ReportCreateView.as_view(), name='reports_create'),
    path('dueño/report_detail/<int:pk>', ReportDetailView.as_view(), name='reports_detail')
]