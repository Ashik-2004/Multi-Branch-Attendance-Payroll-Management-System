from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 
from .import views

urlpatterns = [
   
    path('',views.index, name='index'), 
    path('login',views.login_view, name='login'), 
    path('logout',views.logout_view, name='logout'), 

    path('admin_dashboard',views.admin_dashboard, name='admin_dashboard'), 
     path('branch_dashboard',views.branch_dashboard, name='branch_dashboard'),
    path('employee_dashboard',views.employee_dashboard, name='employee_dashboard'), 


]
if settings.DEBUG: 
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
