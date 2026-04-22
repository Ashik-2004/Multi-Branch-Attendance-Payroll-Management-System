from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.contrib import messages
from django.db.models import Q
from datetime import datetime, timedelta
from .forms import *
from branchapp.models import tblEmployee, tbl_Branch,tbl_ShiftSchedule,tbl_Payroll
from employeeapp.models import tbl_LeaveRequest
from django.db.models import Sum, Count, Avg
from datetime import datetime, date
from calendar import monthrange
# ADD BRANCH
def add_branch(request):
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            branch = form.save(commit=False)
            branch.status = 'Active'  # Ensure consistent status
            branch.save()
            return redirect('branch_list')
    else:
        form = BranchForm()
    
    # Get all branches for the list
    branches = tbl_Branch.objects.all()
    
    return render(request, 'manage_branch.html', {
        'form': form, 
        'title': 'Add Branch',
        'branches': branches
    })

def edit_branch(request, id):
    branch = get_object_or_404(tbl_Branch, id=id)
    branches = tbl_Branch.objects.all()

    if request.method == 'POST':
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()
            return redirect('branch_list')
    else:
        form = BranchForm(instance=branch)

    return render(request, 'manage_branch.html', {
        'form': form,
        'branches': branches,
        'title': 'Edit Branch'
    })


# DELETE BRANCH (PERMANENT)
def delete_branch(request, id):
    branch = get_object_or_404(tbl_Branch, id=id)
    branch.delete()
    return redirect('branch_list')


# REVOKE BRANCH (SOFT DELETE)
def revoke_branch(request, id):
    branch = get_object_or_404(tbl_Branch, id=id)
    branch.status = 'revoked'
    branch.save()
    return redirect('branch_list')


# RESTORE BRANCH
def restore_branch(request, id):
    branch = get_object_or_404(tbl_Branch, id=id)
    branch.status = 'Active'  # Use consistent capitalization
    branch.save()
    return redirect('branch_list')


# BRANCH LIST (Main view)
def branch_list(request):
    branches = tbl_Branch.objects.all()
    form = BranchForm()  # Empty form for adding
    
    return render(request, 'manage_branch.html', {
        'branches': branches,
        'form': form,
        'title': 'Add Branch'
    })

###########Manager management views##############
def manager_list(request):
    # Get all managers with related data
    managers = tbl_Manager.objects.all().select_related('branch', 'login')
    
    # Create form instance
    form = ManagerForm()
    
    # Get all branches
    branch_list = tbl_Branch.objects.all()
    
    # Debug: Check what branches are available in form
    print("DEBUG: Total branches in system:", branch_list.count())
    print("DEBUG: Branches available in form:", form.fields['branch'].queryset.count())
    
    context = {
        'managers': managers,
        'form': form,
        'branch_list': branch_list,
        'title': 'Manage Managers'
    }
    
    return render(request, 'addmanager.html', context)

def add_manager(request):
    if request.method == 'POST':
        print("=== DEBUG: Starting add_manager POST ===")
        
        form = ManagerForm(request.POST)
        print(f"DEBUG: Form created")
        
        if form.is_valid():
            print("DEBUG: Form is valid")
            
            # Check if branch already has an active manager
            branch = form.cleaned_data['branch']
            print(f"DEBUG: Selected branch: {branch.name} (ID: {branch.id})")
            
            # Double-check branch availability
            existing_manager = tbl_Manager.objects.filter(
                branch=branch,
                status='Active'
            ).exists()
            
            if existing_manager:
                print(f"DEBUG: Branch {branch.name} already has an active manager")
                form.add_error('branch', 'This branch already has an active manager.')
                branches = tbl_Branch.objects.all()
                return render(request, 'addmanager.html', {
                    'form': form,
                    'title': 'Add Manager',
                    'branches': branches
                })
            
            try:
                # Create login
                print(f"DEBUG: Creating login for email: {form.cleaned_data['email']}")
                login = tbl_login.objects.create(
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    user_role='Manager'
                )
                print(f"DEBUG: Login created with ID: {login.id}")

                # Save manager
                print("DEBUG: Saving manager...")
                manager = form.save(commit=False)
                manager.login = login
                manager.status = 'Active'
                manager.save()
                print(f"DEBUG: Manager saved successfully! ID: {manager.manager_id}")

                return redirect('manager_list')
                
            except Exception as e:
                print(f"DEBUG: Exception occurred: {str(e)}")
                # Rollback login if created
                if 'login' in locals():
                    login.delete()
                raise
        else:
            print(f"DEBUG: Form is NOT valid")
            print(f"Form errors: {form.errors}")
            print(f"Non-field errors: {form.non_field_errors()}")
            print(f"POST data: {dict(request.POST)}")
    else:
        print("=== DEBUG: GET request for add_manager ===")
        form = ManagerForm()

    # Get all branches for the template
    branches = tbl_Branch.objects.all()
    print(f"DEBUG: Total branches in database: {branches.count()}")
    
    return render(request, 'addmanager.html', {
        'form': form,
        'title': 'Add Manager',
        'branches': branches
    })

def edit_manager(request, id):
    manager = get_object_or_404(tbl_Manager, manager_id=id)
    login = manager.login
    
    if request.method == 'POST':
        print(f"=== DEBUG: Editing manager {id} ===")
        
        # Pass instance to form
        form = ManagerForm(request.POST, instance=manager)
        print(f"DEBUG: Form created with instance")
        
        if form.is_valid():
            print("DEBUG: Form is valid for editing")
            
            # Check if branch is being changed and already has an active manager
            new_branch = form.cleaned_data['branch']
            if new_branch != manager.branch:
                print(f"DEBUG: Branch changed from {manager.branch.name} to {new_branch.name}")
                existing_manager = tbl_Manager.objects.filter(
                    branch=new_branch,
                    status='Active'
                ).exclude(manager_id=manager.manager_id).exists()
                
                if existing_manager:
                    print(f"DEBUG: Branch {new_branch.name} already has an active manager")
                    form.add_error('branch', 'This branch already has an active manager.')
                    branches = tbl_Branch.objects.all()
                    return render(request, 'addmanager.html', {
                        'form': form,
                        'title': 'Edit Manager',
                        'branches': branches,
                        'manager': manager
                    })
            
            # Update login email if changed
            new_email = form.cleaned_data['email']
            if new_email != login.email:
                print(f"DEBUG: Email changed from {login.email} to {new_email}")
                if tbl_login.objects.filter(email=new_email).exclude(id=login.id).exists():
                    print(f"DEBUG: Email {new_email} already exists")
                    form.add_error('email', 'Email already exists.')
                    branches = tbl_Branch.objects.all()
                    return render(request, 'addmanager.html', {
                        'form': form,
                        'title': 'Edit Manager',
                        'branches': branches,
                        'manager': manager
                    })
                login.email = new_email
            
            # Update password if provided
            new_password = form.cleaned_data.get('password')
            if new_password:
                print("DEBUG: Password updated")
                login.password = new_password
            
            login.save()
            print(f"DEBUG: Login updated")
            
            # Save manager
            updated_manager = form.save(commit=False)
            updated_manager.login = login
            updated_manager.save()
            print(f"DEBUG: Manager {manager.manager_id} updated successfully")
            
            return redirect('manager_list')
        else:
            print(f"DEBUG: Form validation failed for editing")
            print(f"Form errors: {form.errors}")
    else:
        print(f"=== DEBUG: GET request for editing manager {id} ===")
        # Initialize form with manager data
        initial_data = {
            'email': login.email,
            'branch': manager.branch,
            'name': manager.name,
            'phone': manager.phone,
        }
        form = ManagerForm(instance=manager, initial=initial_data)
        # For editing, passwords are optional
        form.fields['password'].required = False
        form.fields['confirm_password'].required = False

    branches = tbl_Branch.objects.all()
    return render(request, 'addmanager.html', {
        'form': form,
        'title': 'Edit Manager',
        'branches': branches,
        'manager': manager,  # Pass manager instance
        'managers': tbl_Manager.objects.all().select_related('branch', 'login')  # Pass all managers for list
    })

def delete_manager(request, id):
    manager = get_object_or_404(tbl_Manager, manager_id=id)
    login = manager.login
    
    # Delete associated login
    login.delete()
    # Manager will be automatically deleted due to CASCADE
    
    return redirect('manager_list')

def revoke_manager(request, id):
    manager = get_object_or_404(tbl_Manager, manager_id=id)
    manager.status = 'Inactive'
    manager.save()
    return redirect('manager_list')

def restore_manager(request, id):
    manager = get_object_or_404(tbl_Manager, managerid=id)
    
    # Check if branch already has an active manager
    existing_manager = tbl_Manager.objects.filter(
        branch=manager.branch,
        status='Active'
    ).exclude(id=manager.id).exists()
    
    if existing_manager:
        # You might want to show an error message here
        return redirect('manager_list')
    
    manager.status = 'Active'
    manager.save()
    return redirect('manager_list')


def add_designation(request):
    designations = tbl_Designation.objects.all().order_by('role')

    if request.method == 'POST':
        form = DesignationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('designation')
    else:
        form = DesignationForm()

    return render(request, 'designation.html', {
        'form': form,
        'designations': designations,
        'title': 'Add Designation'
    })


def delete_designation(request, id):
    designation = get_object_or_404(tbl_Designation, id=id)
    designation.delete()
    return redirect('designation')

##########shift management views##############
def shift_list(request):
    shifts = tbl_Shift.objects.all().order_by('start_time')
    
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shift added successfully!')
            return redirect('shift_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ShiftForm()
    
    return render(request, 'manage_shift.html', {
        'form': form,
        'shifts': shifts,
        'title': 'Manage Shifts'
    })

def edit_shift(request, id):
    shift = get_object_or_404(tbl_Shift, id=id)
    shifts = tbl_Shift.objects.all().order_by('start_time')
    
    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shift updated successfully!')
            return redirect('shift_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ShiftForm(instance=shift)
    
    return render(request, 'manage_shift.html', {
        'form': form,
        'shifts': shifts,
        'title': 'Edit Shift'
    })

def delete_shift(request, id):
    shift = get_object_or_404(tbl_Shift, id=id)
    shift.delete()
    messages.success(request, 'Shift deleted successfully!')
    return redirect('shift_list')

########leave type management views##########

def leave_type_crud(request, id=None):
    if id:
        leave_type = get_object_or_404(TblLeaveType, id=id)
    else:
        leave_type = None

    if request.method == 'POST':
        form = LeaveTypeForm(request.POST, instance=leave_type)
        if form.is_valid():
            form.save()
            return redirect('leave_type_crud')
    else:
        form = LeaveTypeForm(instance=leave_type)

    leave_types = TblLeaveType.objects.all()

    return render(request, 'manage_leave_type.html', {
        'form': form,
        'leave_types': leave_types,
        'edit_id': id
    })


def delete_leave_type(request, id):
    leave_type = get_object_or_404(TblLeaveType, id=id)
    leave_type.delete()
    return redirect('leave_type_crud')

##########manage holiday views##############

def holiday_calendar(request, id=None):
    if id:
        holiday = get_object_or_404(TblHoliday, id=id)
    else:
        holiday = None

    if request.method == 'POST':
        form = HolidayForm(request.POST, instance=holiday)
        if form.is_valid():
            form.save()
            return redirect('holiday_calendar')
    else:
        form = HolidayForm(instance=holiday)

    holidays = TblHoliday.objects.all().order_by('holiday_date')

    return render(request, 'holiday_calendar.html', {
        'form': form,
        'holidays': holidays,
        'edit_id': id
    })


def delete_holiday(request, id):
    holiday = get_object_or_404(TblHoliday, id=id)
    holiday.delete()
    return redirect('holiday_calendar')


##########analytics views##############

def admin_analytics(request):
    """Admin analytics dashboard with minimal reports"""
    
    # Check if user is admin (you may need to adjust this based on your auth)
    
    # Get current date info
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # Get filter parameters
    selected_year = int(request.GET.get('year', current_year))
    selected_month = int(request.GET.get('month', current_month))
    
    # REPORT 1: Branch Overview
    total_branches = tbl_Branch.objects.filter(status='Active').count()
    total_managers = tbl_Manager.objects.filter(status='Active').count()
    total_employees_all = tblEmployee.objects.filter(status='active').count()
    
    # Employees per branch
    employees_per_branch = tbl_Branch.objects.filter(
        status='Active'
    ).annotate(
        employee_count=Count('employees', filter=models.Q(employees__status='active'))
    ).values('name', 'employee_count').order_by('-employee_count')
    
    # REPORT 2: Company-wide Payroll Summary
    month_start = date(selected_year, selected_month, 1)
    month_end = date(selected_year, selected_month, monthrange(selected_year, selected_month)[1])
    
    payroll_summary = tbl_Payroll.objects.filter(
        year=selected_year,
        month=selected_month
    ).aggregate(
        total_net=Sum('net_salary'),
        total_basic=Sum('basic_salary'),
        total_deductions=Sum('absent_deduction'),
        avg_salary=Avg('net_salary'),
        employee_count=Count('payroll_id', distinct=True),
        paid_count=Count('payroll_id', filter=models.Q(payment_status='paid'))
    )
    
    # Payroll by branch
    payroll_by_branch = tbl_Branch.objects.filter(
        status='Active'
    ).annotate(
        branch_payroll=Sum(
            'employees__payrolls__net_salary',
            filter=models.Q(employees__payrolls__year=selected_year, 
                           employees__payrolls__month=selected_month)
        ),
        branch_employees=Count(
            'employees__payrolls',
            filter=models.Q(employees__payrolls__year=selected_year,
                           employees__payrolls__month=selected_month),
            distinct=True
        )
    ).values('name', 'branch_payroll', 'branch_employees')
    
    # REPORT 3: Leave Overview
    leave_summary = tbl_LeaveRequest.objects.filter(
        from_date__lte=month_end,
        to_date__gte=month_start,
        status='approved'
    ).aggregate(
        total_requests=Count('id'),
        total_employees=Count('employee', distinct=True)
    )
    
    # Calculate total leave days company-wide
    total_leave_days = 0
    leaves = tbl_LeaveRequest.objects.filter(
        from_date__lte=month_end,
        to_date__gte=month_start,
        status='approved'
    ).select_related('employee', 'employee__branch')
    
    leave_by_branch = {}
    for leave in leaves:
        start = max(leave.from_date, month_start)
        end = min(leave.to_date, month_end)
        if start <= end:
            days = (end - start).days + 1
            if leave.duration_type == 'half_day':
                days = 0.5
            total_leave_days += days
            
            # Group by branch
            branch_name = leave.employee.branch.name
            if branch_name not in leave_by_branch:
                leave_by_branch[branch_name] = 0
            leave_by_branch[branch_name] += days
    
    # Leave by type
    leave_by_type = tbl_LeaveRequest.objects.filter(
        from_date__lte=month_end,
        to_date__gte=month_start,
        status='approved'
    ).values('leave_type__leave_name').annotate(
        count=Count('id')
    )
    
    # Generate years for filter
    years = range(2020, current_year + 3)
    
    context = {
        # Filter info
        'selected_year': selected_year,
        'selected_month': selected_month,
        'month_name': datetime(selected_year, selected_month, 1).strftime('%B'),
        'years': years,
        'months': range(1, 13),
        
        # Report 1: Branch Overview
        'total_branches': total_branches,
        'total_managers': total_managers,
        'total_employees_all': total_employees_all,
        'employees_per_branch': employees_per_branch,
        
        # Report 2: Payroll Summary
        'total_payroll': payroll_summary['total_net'] or 0,
        'total_basic': payroll_summary['total_basic'] or 0,
        'total_deductions': payroll_summary['total_deductions'] or 0,
        'avg_salary': payroll_summary['avg_salary'] or 0,
        'payroll_employee_count': payroll_summary['employee_count'] or 0,
        'paid_count': payroll_summary['paid_count'] or 0,
        'payroll_by_branch': payroll_by_branch,
        
        # Report 3: Leave Summary
        'total_leave_requests': leave_summary['total_requests'] or 0,
        'total_employees_on_leave': leave_summary['total_employees'] or 0,
        'total_leave_days': total_leave_days,
        'leave_by_branch': leave_by_branch,
        'leave_by_type': leave_by_type,
    }
    
    return render(request, 'admin_analytics.html', context)