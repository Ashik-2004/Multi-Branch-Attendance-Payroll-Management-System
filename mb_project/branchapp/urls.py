from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 
from .import views

urlpatterns = [
   ####################emplyee management
    path('employees/', views.employee_list, name='employee_list'),
    path('employee/add/', views.add_employee, name='add_employee'),
    path('employee/edit/<int:id>/', views.edit_employee, name='edit_employee'),
    path('employee/delete/<int:id>/', views.delete_employee, name='delete_employee'),
    path('employee/restore/<int:id>/', views.restore_employee, name='restore_employee'),
    path('employee/permanent-delete/<int:id>/', views.permanent_delete_employee, name='permanent_delete_employee'),

    ####################shift schedule management#####################
     # Dashboard
    path('shift-dashboard/', views.shift_dashboard, name='shift_dashboard'),
    
    # Schedule CRUD
    path('shift-schedules/', views.shift_schedule_list, name='shift_schedule_list'),
    path('shift-schedule/create/', views.create_schedule, name='create_schedule'),
    path('shift-schedule/<int:schedule_id>/', views.view_schedule, name='view_schedule'),
    path('shift-schedule/<int:schedule_id>/delete/', views.delete_schedule, name='delete_schedule'),
    
    # AJAX endpoints
    path('api/calendar-events/', views.get_calendar_events, name='get_calendar_events'),
    path('api/active-employees/', views.get_active_employees, name='get_active_employees'),
    path('api/all-shifts/', views.get_all_shifts, name='get_all_shifts'),
    path('api/all-employees/', views.get_all_employees, name='get_all_employees'),
#leav
    # Manager URLs
    path('manager/leave/', views.manager_leave_dashboard, name='manager_leave_dashboard'),
    path('manager/leave/pending/', views.manager_pending_leaves, name='manager_pending_leaves'),
    path('manager/leave/<int:leave_id>/', views.manager_leave_detail, name='manager_leave_detail'),
    path('manager/leave/bulk-action/', views.manager_bulk_action, name='manager_bulk_action'),
    path('manager/leave/calendar/', views.manager_leave_calendar, name='manager_leave_calendar'),
    path('manager/leave/reports/', views.manager_leave_reports, name='manager_leave_reports'),
    path('debug-calendar-json/', views.debug_calendar_json, name='debug_calendar_json'),

   #     # Manager Payroll URLs
     path('branch/payroll/', views.payroll_list, name='payroll_list'),
    path('payroll/process/', views.process_payroll, name='process_payroll'),
    path('payroll/<int:payroll_id>/', views.payroll_detail, name='payroll_detail'),
    path('payroll/<int:payroll_id>/update-status/', views.update_payment_status, name='update_payment_status'),
    path('employee/<int:employee_id>/payroll/', views.employee_payroll_history, name='employee_payroll'),
    path('debug-calendar-json/', views.debug_calendar_json, name='debug_calendar_json'),
  #  path('test-json/', views.test_json, name='test_json'),
  path('analytics/', views.branch_analytics, name='branch_analytics'),

]
if settings.DEBUG: 
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
