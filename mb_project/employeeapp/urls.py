from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 
from .import views

urlpatterns = [
   
    path('employee/leave/', views.employee_leave_dashboard, name='employee_leave_dashboard'),
    path('employee/leave/cancel/', views.cancel_leave_request, name='cancel_leave_request'),
    path('api/employee/leave-requests/', views.get_leave_requests_api, name='get_leave_requests_api'),
    path('api/employee/leave-balance/', views.get_leave_balance_api, name='get_leave_balance_api'),

 path('my-salary/', views.employee_salary, name='employee_salary'),
    path('my-payslip/<int:payroll_id>/', views.employee_payslip, name='employee_payslip'),
    path('my-attendance/', views.employee_attendance, name='employee_attendance'),
     path('change-password/', views.change_password, name='change_password'),
]
if settings.DEBUG: 
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
