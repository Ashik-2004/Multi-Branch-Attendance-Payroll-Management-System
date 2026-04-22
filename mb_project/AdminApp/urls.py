from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 
from .import views

urlpatterns = [
        ######## BRANCH URLS ###########
   path('branches/', views.branch_list, name='branch_list'),
    path('branch/add/', views.add_branch, name='add_branch'),
    path('branch/edit/<int:id>/', views.edit_branch, name='edit_branch'),
    path('branch/delete/<int:id>/', views.delete_branch, name='delete_branch'),
    path('branch/revoke/<int:id>/', views.revoke_branch, name='revoke_branch'),
    path('branch/restore/<int:id>/', views.restore_branch, name='restore_branch'),
   
   ########### MANAGER URLS ###########
    path('managers/', views.manager_list, name='manager_list'),
    path('manager/add/', views.add_manager, name='add_manager'),
    path('manager/edit/<int:id>/', views.edit_manager, name='edit_manager'),
    path('manager/delete/<int:id>/', views.delete_manager, name='delete_manager'),
    path('manager/revoke/<int:id>/', views.revoke_manager, name='revoke_manager'),
    path('manager/restore/<int:id>/', views.restore_manager, name='restore_manager'),

    path('designation', views.add_designation, name='designation'),
    path('designation/delete/<int:id>', views.delete_designation, name='delete_designation'),
    path('shift/', views.shift_list, name='shift_list'),
    path('shift/edit/<int:id>/', views.edit_shift, name='edit_shift'),
    path('shift/delete/<int:id>/', views.delete_shift, name='delete_shift'),

    ########## LEAVE TYPE URLS ##########
     path('leave-type/', views.leave_type_crud, name='leave_type_crud'),
    path('leave-type/edit/<int:id>/', views.leave_type_crud, name='edit_leave_type'),
    path('leave-type/delete/<int:id>/', views.delete_leave_type, name='delete_leave_type'),

    #############holiday URLS ##############
    path('holidays/', views.holiday_calendar, name='holiday_calendar'),
    path('holidays/edit/<int:id>/', views.holiday_calendar, name='edit_holiday'),
    path('holidays/delete/<int:id>/', views.delete_holiday, name='delete_holiday'),
    path('admin_analytics/', views.admin_analytics, name='admin_analytics'),
]
if settings.DEBUG: 
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
