from django.shortcuts import render,redirect
from .models import *
from AdminApp.models import tbl_Manager
from branchapp.models import tblEmployee
# Create your views here.
def index(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            user = tbl_login.objects.get(email=username, password=password)

           

            # 🔐 Create session
            request.session['login_id'] = user.id
            request.session['username'] = user.email
            request.session['role'] = user.user_role

            # 🔀 Redirect based on role
            if user.user_role == "admin":
                return redirect("admin_dashboard")
            elif user.user_role == "Manager":
                manager=tbl_Manager.objects.get(login_id=user.id)
                request.session['user_id'] = manager.manager_id
                return redirect("branch_dashboard")
            elif user.user_role == "Employee":
                emp=tblEmployee.objects.get(login_id=user.id)
                request.session['user_id'] = emp.employee_id
                request.session['name'] = emp.full_name
                return redirect("employee_dashboard")

        except tbl_login.DoesNotExist:
            return render(request, "login.html", {
                "error": "Invalid username or password"
            })

    return render(request, "login.html")
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')
def branch_dashboard(request):
    return render(request,'branch_dashboard.html' )
def employee_dashboard(request):

    return render(request,'employee_home.html' )
def logout_view(request):
    request.session.flush()  # Clear all session data
    return redirect('index')  # Redirect to home page after logout