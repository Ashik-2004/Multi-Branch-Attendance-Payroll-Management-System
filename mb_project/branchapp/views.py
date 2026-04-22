from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse,HttpResponse
from AdminApp.models import tbl_login,tbl_Branch, tbl_Designation,tbl_Manager,tbl_Shift
from .models import *
from .forms import *
from datetime import date
from AdminApp.models import tbl_Manager
from django.db import transaction
from django.db.models import Count, Q,Sum,Avg
from datetime import datetime, timedelta
from employeeapp.models import  tbl_LeaveRequest, TblLeaveType
import json
from django.utils import timezone
import calendar
import traceback


from calendar import monthrange
from decimal import Decimal







def employee_list(request):
    """List all employees in the manager's branch"""
    try:
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        branch = manager.branch
    except:
        messages.error(request, "Access denied. Manager credentials required.")
        return redirect('dashboard')
    
    # Get employees for this branch
    employees = tblEmployee.objects.filter(branch=branch).select_related(
        'login', 'designation'
    ).order_by('-created_at')
    
    # Calculate statistics
    active_count = employees.filter(status='active').count()
    monthly_count = employees.filter(salary_type='monthly').count()
    
    # Get form for adding new employee
    form = EmployeeForm(branch=branch, request_user=manager)
    
    return render(request, 'manage_employees.html', {
        'employees': employees,
        'form': form,
        'branch': branch,
        'active_count': active_count,
        'monthly_count': monthly_count,
        'title': 'Employee Management'
    })


def add_employee(request):
    """Add new employee to manager's branch"""
    try:
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        branch = manager.branch
    except:
        messages.error(request, "Access denied. Manager credentials required.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, branch=branch, request_user=request.user)
        
        if form.is_valid():
            try:
                # Create login
                login = tbl_login.objects.create(
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    user_role='Employee'
                )
                
                # Create employee
                employee = form.save(commit=False)
                employee.login = login
                employee.branch = branch
                employee.save()
                
                messages.success(request, f'Employee {employee.full_name} added successfully!')
                return redirect('employee_list')
                
            except Exception as e:
                messages.error(request, f'Error saving employee: {str(e)}')
        else:
            # Store form errors in session to display on redirect
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            # Store form data in session to repopulate form
            request.session['form_data'] = request.POST.dict()
            request.session['form_errors'] = True
    
    return redirect('employee_list')

def edit_employee(request, id):
    """Edit existing employee"""
    try:
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        branch = manager.branch
    except:
        messages.error(request, "Access denied. Manager credentials required.")
        return redirect('dashboard')
    
    # Get employee (must belong to manager's branch)
    employee = get_object_or_404(tblEmployee, employee_id=id, branch=branch)
    login = employee.login
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee, branch=branch, request_user=request.user)
        
        if form.is_valid():
            try:
                # Update login email if changed
                new_email = form.cleaned_data['email']
                if new_email != login.email:
                    if tbl_login.objects.filter(email=new_email).exclude(id=login.id).exists():
                        messages.error(request, 'Email already exists.')
                        request.session['edit_form_data'] = request.POST.dict()
                        request.session['edit_form_errors'] = True
                        return redirect('employee_list')
                    else:
                        login.email = new_email
                
                # Update password if provided
                new_password = form.cleaned_data.get('password')
                if new_password:
                    login.password = new_password
                
                login.save()
                
                # Update employee
                updated_employee = form.save(commit=False)
                updated_employee.login = login
                updated_employee.save()
                
                messages.success(request, f'Employee {updated_employee.full_name} updated successfully!')
                return redirect('employee_list')
                
            except Exception as e:
                messages.error(request, f'Error updating employee: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            request.session['edit_form_data'] = request.POST.dict()
            request.session['edit_form_errors'] = True
    
    return redirect('employee_list')
def delete_employee(request, id):
    """Delete employee (soft delete by changing status)"""
    try:
        managerobj = request.session['user_id']
        manager = tbl_Manager.objects.get(manager_id=managerobj)
        branch = manager.branch
    except:
        messages.error(request, "Access denied.")
        return redirect('branch_dashboard')
    
    employee = get_object_or_404(tblEmployee, employee_id=id, branch=branch)
    
    if request.method == 'POST':
        try:
            # Soft delete: change status to inactive
            employee.status = 'inactive'
            employee.save()
            
            # Also deactivate login
            login = employee.login
            login.is_active = False  # If you have this field
            login.save()
            
            messages.success(request, f'Employee {employee.full_name} deactivated successfully!')
        except Exception as e:
            messages.error(request, f'Error deactivating employee: {str(e)}')
    
    return redirect('employee_list')


def restore_employee(request, id):
    """Restore deactivated employee"""
    try:
        managerobj = request.session['user_id']
        manager = tbl_Manager.objects.get(manager_id=managerobj)
        branch = manager.branch
    except:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    employee = get_object_or_404(tblEmployee, employee_id=id, branch=branch)
    
    if request.method == 'POST':
        try:
            # Restore: change status to active
            employee.status = 'active'
            employee.save()
            
            # Reactivate login
            login = employee.login
            login.is_active = True  # If you have this field
            login.save()
            
            messages.success(request, f'Employee {employee.full_name} activated successfully!')
        except Exception as e:
            messages.error(request, f'Error activating employee: {str(e)}')
    
    return redirect('employee_list')


def permanent_delete_employee(request, id):
    """Permanently delete employee and login"""
    try:
        managerobj = request.session['user_id']
        manager = tbl_Manager.objects.get(manager_id=managerobj)
        branch = manager.branch
    except:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    employee = get_object_or_404(tblEmployee, employee_id=id, branch=branch)
    
    if request.method == 'POST':
        try:
            employee_name = employee.full_name
            # Delete login first
            login = employee.login
            login.delete()
            # Employee will be deleted due to CASCADE
            
            messages.success(request, f'Employee {employee_name} permanently deleted!')
        except Exception as e:
            messages.error(request, f'Error deleting employee: {str(e)}')
    
    return redirect('employee_list')


# Dashboard View - NEW
def shift_dashboard(request):
    """Main dashboard for shift schedules"""
    try:
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        branch = manager.branch
    except:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    # Get all schedules for this branch
    schedules = tbl_ShiftSchedule.objects.filter(created_by=manager).order_by('-created_at')
    
    # Calculate counts
    total_schedules = schedules.count()
    published_count = schedules.filter(status='published').count()
    draft_count = schedules.filter(status='draft').count()
    
    # Calculate active schedules (current date between start and end)
    today = date.today()
    
    # Since start_date and end_date are properties, we need to filter in Python
    active_count = 0
    recent_schedules = []
    
    for schedule in schedules:
        # Calculate if schedule is active
        if schedule.start_date <= today <= schedule.end_date:
            active_count += 1
        
        # Prepare data for recent schedules (first 8)
        if len(recent_schedules) < 8:
            recent_schedules.append({
                'schedule_id': schedule.schedule_id,
                'schedule_name': schedule.schedule_name,
                'period': schedule.get_period_display(),
                'month': schedule.month,
                'year': schedule.year,
                'status': schedule.status,
                'created_at': schedule.created_at,
                'duration_days': schedule.duration_days,
                'is_current': schedule.start_date <= today <= schedule.end_date,
                'start_date': schedule.start_date,
                'end_date': schedule.end_date,
            })
    
    return render(request, 'shift_dashboard.html', {
        'recent_schedules': recent_schedules,
        'branch': branch,
        'total_schedules': total_schedules,
        'published_count': published_count,
        'draft_count': draft_count,
        'active_count': active_count,
        'title': 'Shift Schedule Dashboard'
    })
def shift_schedule_list(request):
    """List all shift schedules"""
    try:
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        branch = manager.branch
    except:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    # Get all schedules
    schedules = tbl_ShiftSchedule.objects.filter(created_by=manager).order_by('-year', '-month', 'period')
    
    # Prepare schedule data
    schedule_list = []
    for schedule in schedules:
        schedule_list.append({
            'schedule_id': schedule.schedule_id,
            'schedule_name': schedule.schedule_name,
            'period': schedule.get_period_display(),
            'month': schedule.month,
            'year': schedule.year,
            'status': schedule.status,
            'start_date': schedule.start_date,
            'end_date': schedule.end_date,
            'created_at': schedule.created_at,
            'assignment_count': schedule.assignments.count(),
            'is_current': schedule.is_current,
            'is_future': schedule.is_future,
        })
    
    return render(request, 'shift_schedule_list.html', {
        'schedules': schedule_list,
        'branch': branch,
        'title': 'All Shift Schedules'
    })

def create_schedule(request):
    """Create new shift schedule"""
    try:
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        branch = manager.branch
    except:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ShiftScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = manager
            schedule.save()
            
            messages.success(request, f'Schedule created: {schedule.schedule_name}')
            return redirect('view_schedule', schedule_id=schedule.schedule_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ShiftScheduleForm()
    
    return render(request, 'create_schedule.html', {
        'form': form,
        'branch': branch,
        'title': 'Create Schedule'
    })

def view_schedule(request, schedule_id):
    """View and manage a specific schedule"""
    try:
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        branch = manager.branch
    except:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    schedule = get_object_or_404(tbl_ShiftSchedule, schedule_id=schedule_id, created_by=manager)
    
    # Get assigned employees
    assignments = tbl_ShiftAssignment.objects.filter(
        schedule=schedule,
        employee__branch=branch
    ).select_related('employee', 'shift')
    
    # Get available employees (not assigned to this schedule yet)
    assigned_employee_ids = assignments.values_list('employee_id', flat=True)
    available_employees = tblEmployee.objects.filter(
        branch=branch,
        status='Active'
    ).exclude(employee_id__in=assigned_employee_ids)
    
    # Get available shifts
    available_shifts = tbl_Shift.objects.all()
    
    # Handle form submissions
    if request.method == 'POST':
        # Publish schedule
        if 'publish' in request.POST:
            if schedule.status == 'draft':
                schedule.status = 'published'
                schedule.save()
                messages.success(request, 'Schedule published successfully!')
            return redirect('view_schedule', schedule_id=schedule_id)
        
        # Individual assignment
        elif 'assign_shift' in request.POST:
            employee_id = request.POST.get('employee')
            shift_id = request.POST.get('shift')
            notes = request.POST.get('notes', '')
            
            if employee_id and shift_id:
                try:
                    employee = tblEmployee.objects.get(employee_id=employee_id, branch=branch)
                    shift = tbl_Shift.objects.get(id=shift_id)
                    
                    # Check if already assigned
                    existing = tbl_ShiftAssignment.objects.filter(
                        schedule=schedule,
                        employee=employee
                    ).first()
                    
                    if existing:
                        messages.warning(request, f'{employee.full_name} is already assigned')
                    else:
                        tbl_ShiftAssignment.objects.create(
                            schedule=schedule,
                            employee=employee,
                            shift=shift,
                            notes=notes
                        )
                        messages.success(request, f'Shift assigned to {employee.full_name}')
                
                except Exception as e:
                    messages.error(request, f'Error: {str(e)}')
            
            return redirect('view_schedule', schedule_id=schedule_id)
        
        # Bulk assignment
        elif 'bulk_assign' in request.POST:
            shift_id = request.POST.get('bulk_shift')
            employee_ids = request.POST.getlist('employee_list')
            
            if shift_id and employee_ids:
                try:
                    shift = tbl_Shift.objects.get(id=shift_id)
                    assigned_count = 0
                    
                    for employee_id in employee_ids:
                        employee = tblEmployee.objects.get(employee_id=employee_id, branch=branch)
                        
                        # Check if already assigned
                        existing = tbl_ShiftAssignment.objects.filter(
                            schedule=schedule,
                            employee=employee
                        ).first()
                        
                        if not existing:
                            tbl_ShiftAssignment.objects.create(
                                schedule=schedule,
                                employee=employee,
                                shift=shift
                            )
                            assigned_count += 1
                    
                    messages.success(request, f'Shift assigned to {assigned_count} employees')
                
                except Exception as e:
                    messages.error(request, f'Error: {str(e)}')
            
            return redirect('view_schedule', schedule_id=schedule_id)
        
        # Remove assignment
        elif 'remove_assignment' in request.POST:
            assignment_id = request.POST.get('assignment_id')
            if assignment_id:
                try:
                    assignment = tbl_ShiftAssignment.objects.get(
                        assignment_id=assignment_id,
                        schedule=schedule
                    )
                    employee_name = assignment.employee.full_name
                    assignment.delete()
                    messages.success(request, f'Shift removed for {employee_name}')
                except:
                    messages.error(request, 'Assignment not found.')
            
            return redirect('view_schedule', schedule_id=schedule_id)
    
    # Prepare schedule data for template
    schedule_data = {
        'schedule_id': schedule.schedule_id,
        'schedule_name': schedule.schedule_name,
        'period': schedule.get_period_display(),
        'month': schedule.month,
        'year': schedule.year,
        'status': schedule.status,
        'start_date': schedule.start_date,
        'end_date': schedule.end_date,
        'created_at': schedule.created_at,
        'is_current': schedule.is_current,
        'duration_days': schedule.duration_days,
    }
    
    # Prepare assignments data
    assignments_list = []
    for assignment in assignments:
        assignments_list.append({
            'assignment_id': assignment.assignment_id,
            'employee_id': assignment.employee.employee_id,
            'employee_name': assignment.employee.full_name,
            'employee_department': assignment.employee.designation,
            'shift_id': assignment.shift.id,
            'shift_name': assignment.shift.shift_name,
            'shift_timing': f"{assignment.shift.start_time.strftime('%I:%M %p')} - {assignment.shift.end_time.strftime('%I:%M %p')}",
            'notes': assignment.notes,
            'created_at': assignment.created_at,
        })
    
    # Prepare available employees data
    available_employees_list = []
    for employee in available_employees:
        available_employees_list.append({
            'employee_id': employee.employee_id,
            'full_name': employee.full_name,
            'department': employee.designation,
        })
    
    # Prepare available shifts data
    available_shifts_list = []
    for shift in available_shifts:
        available_shifts_list.append({
            'shift_id': shift.id,
            'shift_name': shift.shift_name,
            'timing': f"{shift.start_time.strftime('%I:%M %p')} - {shift.end_time.strftime('%I:%M %p')}",
        })
    
    return render(request, 'view_schedule.html', {
        'schedule': schedule_data,
        'assignments': assignments_list,
        'available_employees': available_employees_list,
        'available_shifts': available_shifts_list,
        'branch': branch,
        'title': f'Schedule: {schedule.schedule_name}'
    })

def delete_schedule(request, schedule_id):
    """Delete a schedule"""
    try:
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
    except:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    schedule = get_object_or_404(tbl_ShiftSchedule, schedule_id=schedule_id, created_by=manager)
    
    if request.method == 'POST':
        schedule_name = schedule.schedule_name
        schedule.delete()
        messages.success(request, f'Schedule "{schedule_name}" deleted successfully.')
        return redirect('shift_dashboard')
    
    return render(request, 'confirm_delete.html', {
        'schedule': schedule,
        'title': 'Delete Schedule'
    })

# AJAX Views (Simplified)
def get_calendar_events(request):
    """Get events for calendar view"""
    try:
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
    except:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    schedules = tbl_ShiftSchedule.objects.filter(created_by=manager)
    
    events = []
    for schedule in schedules:
        events.append({
            'title': schedule.schedule_name,
            'start': schedule.start_date.isoformat(),
            'end': schedule.end_date.isoformat(),
            'backgroundColor': {
                'draft': '#ffc107',
                'published': '#28a745',
                'active': '#007bff',
                'completed': '#6c757d'
            }.get(schedule.status, '#6c757d'),
            'extendedProps': {
                'schedule_id': schedule.schedule_id,
                'status': schedule.status,
            }
        })
    
    return JsonResponse(events, safe=False)

def get_active_employees(request):
    """Get employees active today"""
    try:
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        branch = manager.branch
    except:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    today = date.today()
    
    # Get active schedule for today
    schedules = tbl_ShiftSchedule.objects.filter(
        start_date__lte=today,
        end_date__gte=today,
        created_by=manager
    ).first()
    
    employees = []
    if schedules:
        assignments = tbl_ShiftAssignment.objects.filter(
            schedule=schedules,
            employee__branch=branch
        ).select_related('employee', 'shift')
        
        for assignment in assignments:
            employees.append({
                'id': assignment.employee.employee_id,
                'name': assignment.employee.full_name,
                'shift': assignment.shift.shift_name,
                'timing': f"{assignment.shift.start_time.strftime('%I:%M %p')} - {assignment.shift.end_time.strftime('%I:%M %p')}"
            })
    
    return JsonResponse({'success': True, 'employees': employees})

def get_all_shifts(request):
    """Get all shifts for dropdown"""
    try:
        shifts = tbl_Shift.objects.all().values('id', 'shift_name', 'start_time', 'end_time')
        data = []
        for shift in shifts:
            data.append({
                'id': shift['id'],
                'name': shift['shift_name'],
                'timing': f"{shift['start_time'].strftime('%I:%M %p')} - {shift['end_time'].strftime('%I:%M %p')}"
            })
        return JsonResponse(data, safe=False)
    except:
        return JsonResponse([], safe=False)

def get_all_employees(request):
    """Get all employees for dropdown"""
    try:
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        branch = manager.branch
        
        employees = tblEmployee.objects.filter(
            branch=branch,
            status='Active'
        ).values('employee_id', 'full_name', 'department')
        
        return JsonResponse(list(employees), safe=False)
    except:
        return JsonResponse([], safe=False)
    

    ###########manager manage leave
    # views.py - Add these manager views




def manager_leave_dashboard(request):
    """Manager dashboard to view and approve leave requests"""
    try:
        # Get manager profile from logged in user
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        
        # Get all employees under this manager's branch
        employees = tblEmployee.objects.filter(
            branch=manager.branch,
            status='active'
        )
        
        # Get leave statistics
        total_employees = employees.count()
        
        # Get pending leave requests
        pending_leaves = tbl_LeaveRequest.objects.filter(
            employee__in=employees,
            status='pending'
        ).select_related('employee', 'leave_type').order_by('-applied_date')
        
        # Get approved leaves today
        today_approved = tbl_LeaveRequest.objects.filter(
            employee__in=employees,
            status='approved',
            reviewed_date__date=date.today()
        ).count()
        
        # Get rejected leaves today
        today_rejected = tbl_LeaveRequest.objects.filter(
            employee__in=employees,
            status='rejected',
            reviewed_date__date=date.today()
        ).count()
        
        # Get employees on leave today
        today = date.today()
        employees_on_leave = tbl_LeaveRequest.objects.filter(
            employee__in=employees,
            status='approved',
            from_date__lte=today,
            to_date__gte=today
        ).select_related('employee').count()
        
        # Get recent activity (last 7 days)
        week_ago = today - timedelta(days=7)
        recent_activity = tbl_LeaveRequest.objects.filter(
            employee__in=employees,
            reviewed_date__gte=week_ago
        ).order_by('-reviewed_date')[:10]
        
        context = {
            'manager': manager,
            'total_employees': total_employees,
            'pending_leaves': pending_leaves,
            'pending_count': pending_leaves.count(),
            'today_approved': today_approved,
            'today_rejected': today_rejected,
            'employees_on_leave': employees_on_leave,
            'recent_activity': recent_activity,
        }
        
        return render(request, 'manage_employee_leave.html', context)
        
    except tbl_Manager.DoesNotExist:
        messages.error(request, 'Manager profile not found.')
        return redirect('login')


def manager_pending_leaves(request):
    """View all pending leave requests"""
    try:
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        
        # Get pending leaves with filters
        status_filter = request.GET.get('status', 'pending')
        leave_type_filter = request.GET.get('leave_type', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        leaves = tbl_LeaveRequest.objects.filter(
            employee__branch=manager.branch
        ).select_related('employee', 'leave_type', 'approved_by')
        
        # Apply filters
        if status_filter and status_filter != 'all':
            leaves = leaves.filter(status=status_filter)
        
        if leave_type_filter:
            leaves = leaves.filter(leave_type_id=leave_type_filter)
        
        if date_from:
            leaves = leaves.filter(from_date__gte=date_from)
        
        if date_to:
            leaves = leaves.filter(to_date__lte=date_to)
        
        # Order by most recent first
        leaves = leaves.order_by('-applied_date')
        
        # Get all leave types for filter dropdown
        leave_types = TblLeaveType.objects.all()
        
        # Statistics
        total_pending = leaves.filter(status='pending').count()
        total_approved = leaves.filter(status='approved').count()
        total_rejected = leaves.filter(status='rejected').count()
        
        context = {
            'manager': manager,
            'leaves': leaves,
            'leave_types': leave_types,
            'total_pending': total_pending,
            'total_approved': total_approved,
            'total_rejected': total_rejected,
            'current_filters': {
                'status': status_filter,
                'leave_type': leave_type_filter,
                'date_from': date_from,
                'date_to': date_to,
            }
        }
        
        return render(request, 'manager_pending_leaves.html', context)
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('manager_leave_dashboard')

import traceback
import sys

def manager_leave_detail(request, leave_id):
    """View and process a single leave request"""
    try:
        print("\n" + "="*50)
        print("MANAGER LEAVE DETAIL VIEW")
        print("="*50)
        
        # Debug session info
        print(f"Session data: {dict(request.session)}")
        print(f"User authenticated: {request.user.is_authenticated}")
        print(f"Request method: {request.method}")
        print(f"Leave ID: {leave_id}")
        
        # Check if user_id exists in session
        if 'user_id' not in request.session:
            print("ERROR: 'user_id' not found in session")
            print(f"Available session keys: {list(request.session.keys())}")
            messages.error(request, 'Session expired. Please login again.')
            return redirect('login')
        
        # Get manager
        try:
            print(f"Looking for manager with manager_id: {request.session['user_id']}")
            manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
            print(f"Manager found: {manager.name}")
            print(f"Manager branch: {manager.branch.name if manager.branch else 'No branch'}")
        except tbl_Manager.DoesNotExist:
            print(f"ERROR: Manager not found with ID: {request.session['user_id']}")
            messages.error(request, 'Manager profile not found.')
            return redirect('login')
        except Exception as e:
            print(f"ERROR getting manager: {str(e)}")
            traceback.print_exc()
            messages.error(request, f'Error finding manager: {str(e)}')
            return redirect('login')
        
        # Get leave request
        try:
            print(f"Looking for leave request with ID: {leave_id}")
            print(f"Branch filter: {manager.branch.name if manager.branch else 'None'}")
            
            leave = get_object_or_404(
                tbl_LeaveRequest.objects.select_related('employee', 'leave_type', 'approved_by'),
                id=leave_id,
                employee__branch=manager.branch
            )
            
            print(f"Leave request found:")
            print(f"  - Employee: {leave.employee.full_name} ({leave.employee.employee_code})")
            print(f"  - Leave Type: {leave.leave_type.leave_name}")
            print(f"  - From: {leave.from_date} To: {leave.to_date}")
            print(f"  - Status: {leave.status}")
            print(f"  - Duration: {leave.leave_days} days")
            
        except Exception as e:
            print(f"ERROR getting leave request: {str(e)}")
            traceback.print_exc()
            messages.error(request, f'Leave request not found or access denied.')
            return redirect('manager_pending_leaves')
        
        # Handle POST request
        if request.method == 'POST':
            print("\n" + "-"*30)
            print("PROCESSING POST REQUEST")
            print("-"*30)
            
            action = request.POST.get('action')
            remarks = request.POST.get('remarks', '')
            
            print(f"Action: {action}")
            print(f"Remarks: {remarks}")
            
            if action == 'approve':
                try:
                    print("Attempting to approve leave...")
                    
                    # Check if approve method exists
                    if not hasattr(leave, 'approve'):
                        print("ERROR: Leave object has no 'approve' method")
                        print(f"Available methods: {dir(leave)}")
                        messages.error(request, 'System error: Approve method not found.')
                        return redirect('manager_leave_detail', leave_id=leave.id)
                    
                    leave.approve(manager, remarks)
                    print("Leave approved successfully")
                    messages.success(request, f'Leave request for {leave.employee.full_name} approved successfully.')
                    
                except Exception as e:
                    print(f"ERROR during approval: {str(e)}")
                    traceback.print_exc()
                    messages.error(request, f'Error approving leave: {str(e)}')
                    
            elif action == 'reject':
                try:
                    print("Attempting to reject leave...")
                    
                    # Check if reject method exists
                    if not hasattr(leave, 'reject'):
                        print("ERROR: Leave object has no 'reject' method")
                        print(f"Available methods: {dir(leave)}")
                        messages.error(request, 'System error: Reject method not found.')
                        return redirect('manager_leave_detail', leave_id=leave.leave_id)
                    
                    leave.reject(manager, remarks)
                    print("Leave rejected successfully")
                    messages.success(request, f'Leave request for {leave.employee.full_name} rejected.')
                    
                except Exception as e:
                    print(f"ERROR during rejection: {str(e)}")
                    traceback.print_exc()
                    messages.error(request, f'Error rejecting leave: {str(e)}')
            
            else:
                print(f"ERROR: Unknown action '{action}'")
                messages.error(request, f'Unknown action: {action}')
            
            return redirect('manager_leave_detail', leave_id=leave.id)
        
        # GET request - render template
        print("\n" + "-"*30)
        print("RENDERING TEMPLATE")
        print("-"*30)
        
        context = {
            'manager': manager,
            'leave': leave,
        }
        
        print(f"Context prepared with {len(context)} items")
        print("="*50 + "\n")
        
        return render(request, 'manager_leave_detail.html', context)
        
    except Exception as e:
        print("\n" + "!"*50)
        print("UNHANDLED EXCEPTION IN MANAGER LEAVE DETAIL")
        print("!"*50)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()
        print("!"*50 + "\n")
        
        messages.error(request, f'Unexpected error: {str(e)}')
        return redirect('manager_pending_leaves')

def manager_bulk_action(request):
    """Bulk approve/reject multiple leave requests"""
    try:
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        data = json.loads(request.body)
        
        leave_ids = data.get('leave_ids', [])
        action = data.get('action')
        remarks = data.get('remarks', '')
        
        if not leave_ids or not action:
            return JsonResponse({
                'success': False,
                'message': 'Please select leaves and action'
            })
        
        leaves = tbl_LeaveRequest.objects.filter(
            leave_id__in=leave_ids,
            employee__branch=manager.branch,
            status='pending'
        )
        
        count = 0
        for leave in leaves:
            if action == 'approve':
                leave.approve(manager, remarks)
            elif action == 'reject':
                leave.reject(manager, remarks)
            count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'{count} leave requests {action}d successfully',
            'count': count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


def manager_leave_calendar(request):
    """Calendar view of all leaves"""
    try:
        # Check session
        if 'user_id' not in request.session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Session expired'}, status=401)
            messages.error(request, 'Session expired. Please login again.')
            return redirect('login')
        
        # Get manager
        try:
            manager = tbl_Manager.objects.select_related('branch').get(
                manager_id=request.session['user_id']
            )
        except tbl_Manager.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Manager not found'}, status=404)
            messages.error(request, 'Manager not found')
            return redirect('login')
        
        # For AJAX requests, return JSON events
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                # Get approved leaves for this branch
                leaves = tbl_LeaveRequest.objects.filter(
                    employee__branch=manager.branch,
                    status='approved'
                ).select_related('employee', 'leave_type')
                
                # Format events for FullCalendar
                events = []
                for leave in leaves:
                    # Get color based on leave type
                    leave_type = leave.leave_type.leave_name.lower()
                    if 'casual' in leave_type:
                        color = '#28a745'
                    elif 'sick' in leave_type:
                        color = '#dc3545'
                    elif 'earned' in leave_type:
                        color = '#ffc107'
                    elif 'maternity' in leave_type:
                        color = '#17a2b8'
                    elif 'paternity' in leave_type:
                        color = '#6f42c1'
                    else:
                        color = '#6c757d'
                    
                    # Calculate end date (FullCalendar needs end date exclusive)
                    end_date = leave.to_date + timedelta(days=1)
                    
                    # Determine text color
                    text_color = '#000000' if color == '#ffc107' else '#ffffff'
                    
                    event = {
                        'id': leave.id,
                        'title': f"{leave.employee.full_name} - {leave.leave_type.leave_name}",
                        'start': leave.from_date.isoformat(),
                        'end': end_date.isoformat(),
                        'backgroundColor': color,
                        'borderColor': color,
                        'textColor': text_color,
                        'url': f"/manager/leave/{leave.id}/",
                    }
                    events.append(event)
                
                # Return JSON response
                return JsonResponse(events, safe=False)
                
            except Exception as e:
                print(f"Error creating events: {e}")
                return JsonResponse({'error': str(e)}, status=500)
        
        # For non-AJAX requests, render template
        context = {
            'manager': manager,
        }
        return render(request, 'manager_leave_calendar.html', context)
        
    except Exception as e:
        print(f"Unhandled error: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        messages.error(request, f'Error: {str(e)}')
        return redirect('manager_leave_dashboard')
def get_leave_color(leave_type):
    """Get color for leave type"""
    try:
        colors = {
            'casual': '#28a745',  # Green
            'sick': '#dc3545',     # Red
            'earned': '#ffc107',    # Yellow
            'maternity': '#17a2b8', # Teal
            'paternity': '#6f42c1', # Purple
        }
        
        leave_type_lower = leave_type.lower() if leave_type else ''
        print(f"  Getting color for leave type: '{leave_type_lower}'")
        
        for key, color in colors.items():
            if key in leave_type_lower:
                print(f"  ✓ Found match: {key} -> {color}")
                return color
        
        print(f"  No match found, using default: #6c757d")
        return '#6c757d'  # Gray default
        
    except Exception as e:
        print(f"  ✗ Error in get_leave_color: {e}")
        return '#6c757d'
def manager_leave_reports(request):
    """Generate leave reports"""
    try:
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        
        # Get filter parameters
        month = request.GET.get('month', datetime.now().month)
        year = request.GET.get('year', datetime.now().year)
        employee_id = request.GET.get('employee', '')
        
        # Base queryset
        leaves = tbl_LeaveRequest.objects.filter(
            employee__branch=manager.branch,
            from_date__year=year,
            from_date__month=month
        ).select_related('employee', 'leave_type')
        
        if employee_id:
            leaves = leaves.filter(employee_id=employee_id)
        
        # Statistics
        total_leaves = leaves.count()
        approved_leaves = leaves.filter(status='approved').count()
        pending_leaves = leaves.filter(status='pending').count()
        rejected_leaves = leaves.filter(status='rejected').count()
        
        # Group by employee
        employee_stats = []
        for employee in tblEmployee.objects.filter(branch=manager.branch, status='active'):
            emp_leaves = leaves.filter(employee=employee)
            if emp_leaves.exists():
                stats = {
                    'employee': employee,
                    'total': emp_leaves.count(),
                    'approved': emp_leaves.filter(status='approved').count(),
                    'pending': emp_leaves.filter(status='pending').count(),
                    'rejected': emp_leaves.filter(status='rejected').count(),
                    'total_days': sum([l.leave_days for l in emp_leaves if l.status == 'approved'])
                }
                employee_stats.append(stats)
        
        context = {
            'manager': manager,
            'leaves': leaves,
            'employee_stats': employee_stats,
            'total_leaves': total_leaves,
            'approved_leaves': approved_leaves,
            'pending_leaves': pending_leaves,
            'rejected_leaves': rejected_leaves,
            'current_month': month,
            'current_year': year,
            'months': range(1, 13),
            'years': range(2020, datetime.now().year + 2),
            'employees': tblEmployee.objects.filter(branch=manager.branch, status='active'),
        }
        
        return render(request, 'manager_leave_reports.html', context)
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('manager_leave_dashboard')
    



    ######debug for calender
def debug_calendar_json(request):
    """Debug endpoint to check the JSON response"""
    try:
        if 'user_id' not in request.session:
            return JsonResponse({'error': 'No session'}, status=401)
            
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        
        leaves = tbl_LeaveRequest.objects.filter(
            employee__branch=manager.branch,
            status='approved'
        ).select_related('employee', 'leave_type')
        
        events = []
        for leave in leaves:
            color = get_leave_color(leave.leave_type.leave_name)
            end_date = leave.to_date + timedelta(days=1)
            
            event = {
                'id': leave.id,
                'title': f"{leave.employee.full_name} - {leave.leave_type.leave_name}",
                'start': leave.from_date.isoformat(),
                'end': end_date.isoformat(),
                'backgroundColor': color,
                'borderColor': color,
            }
            events.append(event)
        
        # Return as JSON with proper formatting
        response = JsonResponse(events, safe=False)
        print(f"Response status: {response.status_code}")
        print(f"Response content type: {response.get('Content-Type')}")
        print(f"Response content preview: {response.content[:200]}")
        
        return response
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
    

#############payroll
def payroll_list(request):
    """Display payroll list for a specific month"""
    
    # Get filter parameters
    month = int(request.GET.get('month', datetime.now().month))
    year = int(request.GET.get('year', datetime.now().year))
    
    # Get branch from logged in user (using session)
    try:
        if 'user_id' not in request.session:
            messages.error(request, 'Please login first')
            return redirect('login')
            
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        branch = manager.branch
    except tbl_Manager.DoesNotExist:
        messages.error(request, 'Manager profile not found')
        return redirect('home')
    
    # Get payroll records
    payrolls = tbl_Payroll.objects.filter(
        employee__branch=branch,
        month=month,
        year=year
    ).select_related('employee')
    
    # Calculate summary
    total_net = 0
    paid_count = 0
    for p in payrolls:
        total_net += p.net_salary
        if p.payment_status == 'paid':
            paid_count += 1
    
    # Generate dynamic years (2020 to current year + 2)
    current_year = datetime.now().year
    years = range(2020, current_year + 3)
    
    context = {
        'payrolls': payrolls,
        'month': month,
        'year': year,
        'month_name': datetime(year, month, 1).strftime('%B'),
        'total_employees': payrolls.count(),
        'total_net_salary': total_net,
        'paid_count': paid_count,
        'months': range(1, 13),
        'years': years,
    }
    
    return render(request, 'payroll_list.html', context)

def process_payroll(request):
    """Process payroll for a specific month"""
    
    if request.method == 'POST':
        # Get form data
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))
        
        # Get branch using session
        try:
            if 'user_id' not in request.session:
                messages.error(request, 'Please login first')
                return redirect('login')
                
            manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
            branch = manager.branch
        except tbl_Manager.DoesNotExist:
            messages.error(request, 'Manager profile not found')
            return redirect('payroll_list')
        
        # Get all active employees in branch
        employees = tblEmployee.objects.filter(branch=branch, status='active')
        
        if not employees.exists():
            messages.warning(request, 'No active employees found in this branch')
            return redirect('payroll_list')
        
        # Get month details
        total_days_in_month = monthrange(year, month)[1]
        month_start = date(year, month, 1)
        month_end = date(year, month, total_days_in_month)
        
        # Get holidays for this month
        holidays = TblHoliday.objects.filter(
            holiday_date__range=[month_start, month_end]
        ).count()
        
        # Calculate total working days (excluding holidays)
        total_working_days = total_days_in_month - holidays
        
        payrolls_created = 0
        payrolls_updated = 0
        
        # Process each employee
        for employee in employees:
            # Check if payroll already exists
            existing_payroll = tbl_Payroll.objects.filter(
                employee=employee,
                month=month,
                year=year
            ).first()
            
            if existing_payroll and existing_payroll.payment_status == 'paid':
                continue  # Skip if already paid
            
            # Get approved leaves for this month
            leaves = tbl_LeaveRequest.objects.filter(
                employee=employee,
                status='approved',
                from_date__lte=month_end,
                to_date__gte=month_start
            )
            
            # Calculate leave days (unpaid)
            leave_days = 0
            for leave in leaves:
                # Calculate overlapping days
                start = max(leave.from_date, month_start)
                end = min(leave.to_date, month_end)
                
                if start <= end:
                    delta = end - start
                    days = delta.days + 1
                    
                    # Adjust for half day
                    if leave.duration_type == 'half_day':
                        days = 0.5
                    
                    leave_days += days
            
            # Calculate present days (all working days except leave days)
            present_days = total_working_days - leave_days
            if present_days < 0:
                present_days = 0
            
            # Absent days (none since all non-leave days are considered present)
            absent_days = 0
            
            # Calculate salary based on type
            if employee.salary_type == 'monthly':
                # Monthly salary calculation
                if total_working_days > 0:
                    daily_rate = employee.base_salary / Decimal(str(total_working_days))
                else:
                    daily_rate = Decimal('0')
                
                # For monthly employees, deduct for unpaid leave days
                unpaid_days = leave_days  # Leaves are unpaid
                absent_deduction = daily_rate * Decimal(str(unpaid_days))
                net_salary = employee.base_salary - absent_deduction
                
            else:  # daily wage
                # Daily salary calculation
                daily_rate = employee.base_salary
                # Daily workers get paid only for days they work (present days)
                # Leaves are unpaid, so exclude them
                paid_days = present_days
                
                net_salary = daily_rate * Decimal(str(paid_days))
                absent_deduction = Decimal('0')  # No separate deduction, just not paid
                unpaid_days = total_working_days - paid_days
            
            # Create or update payroll
            if existing_payroll:
                existing_payroll.basic_salary = employee.base_salary
                existing_payroll.salary_type = employee.salary_type
                existing_payroll.total_days = total_days_in_month
                existing_payroll.present_days = present_days
                existing_payroll.absent_days = absent_days
                existing_payroll.leave_days = leave_days
                existing_payroll.holidays = holidays
                existing_payroll.absent_deduction = absent_deduction
                existing_payroll.net_salary = net_salary
                existing_payroll.payment_status = 'pending'
                existing_payroll.save()
                payrolls_updated += 1
            else:
                tbl_Payroll.objects.create(
                    employee=employee,
                    month=month,
                    year=year,
                    basic_salary=employee.base_salary,
                    salary_type=employee.salary_type,
                    total_days=total_days_in_month,
                    present_days=present_days,
                    absent_days=absent_days,
                    leave_days=leave_days,
                    holidays=holidays,
                    absent_deduction=absent_deduction,
                    net_salary=net_salary,
                    payment_status='pending'
                )
                payrolls_created += 1
        
        total_processed = payrolls_created + payrolls_updated
        messages.success(request, f'Payroll processed: {payrolls_created} new, {payrolls_updated} updated for {month}/{year}')
        return redirect(f'/branch/payroll/?month={month}&year={year}')
    
    # GET request - show form
    current_year = datetime.now().year
    years = range(2020, current_year + 3)
    
    context = {
        'months': range(1, 13),
        'years': years,
        'current_month': datetime.now().month,
        'current_year': datetime.now().year
    }
    return render(request, 'process_payroll.html', context)

def payroll_detail(request, payroll_id):
    """View single payroll details"""
    
    payroll = get_object_or_404(tbl_Payroll, payroll_id=payroll_id)
    
    # Calculate attendance percentage
    if payroll.total_days > 0:
        attendance_percent = (payroll.present_days / payroll.total_days) * 100
    else:
        attendance_percent = 0
    
    # Calculate working days
    working_days = payroll.total_days - payroll.holidays
    
    context = {
        'payroll': payroll,
        'attendance_percent': round(attendance_percent, 2),
        'month_name': datetime(payroll.year, payroll.month, 1).strftime('%B'),
        'working_days': working_days
    }
    
    return render(request, 'payroll_detail.html', context)

def update_payment_status(request, payroll_id):
    """Mark payroll as paid"""
    
    if request.method == 'POST':
        payroll = get_object_or_404(tbl_Payroll, payroll_id=payroll_id)
        
        payroll.payment_status = 'paid'
        payroll.payment_date = date.today()
        payroll.save()
        
        messages.success(request, f'Payment marked as paid for {payroll.employee.full_name}')
        
    return redirect('payroll_detail', payroll_id=payroll_id)

def employee_payroll_history(request, employee_id):
    """View payroll history for a specific employee"""
    
    employee = get_object_or_404(tblEmployee, employee_id=employee_id)
    payrolls = tbl_Payroll.objects.filter(employee=employee).order_by('-year', '-month')
    
    # Generate years for filter
    current_year = datetime.now().year
    years = range(2020, current_year + 3)
    
    context = {
        'employee': employee,
        'payrolls': payrolls,
        'years': years
    }
    
    return render(request, 'employee_payroll.html', context)

###########analytics and reports

def branch_analytics(request):
    """Branch analytics dashboard with minimal reports"""
    
    # Get branch from logged in user
    try:
        if 'user_id' not in request.session:
            messages.error(request, 'Please login first')
            return redirect('login')
            
        manager = tbl_Manager.objects.get(manager_id=request.session['user_id'])
        branch = manager.branch
    except tbl_Manager.DoesNotExist:
        messages.error(request, 'Manager profile not found')
        return redirect('home')
    
    # Get current date info
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # Get filter parameters (default to current month/year)
    selected_year = int(request.GET.get('year', current_year))
    selected_month = int(request.GET.get('month', current_month))
    
    # REPORT 1: Employee Statistics
    total_employees = tblEmployee.objects.filter(branch=branch, status='active').count()
    
    # Employee count by designation
    employees_by_designation = tblEmployee.objects.filter(
        branch=branch, 
        status='active'
    ).values('designation__role').annotate(
        count=Count('employee_id')
    ).order_by('-count')
    
    # Salary type distribution
    monthly_count = tblEmployee.objects.filter(
        branch=branch, 
        status='active', 
        salary_type='monthly'
    ).count()
    
    daily_count = tblEmployee.objects.filter(
        branch=branch, 
        status='active', 
        salary_type='daily'
    ).count()
    
    # REPORT 2: Monthly Payroll Summary
    payroll_data = tbl_Payroll.objects.filter(
        employee__branch=branch,
        year=selected_year,
        month=selected_month
    ).aggregate(
        total_net=Sum('net_salary'),
        total_basic=Sum('basic_salary'),
        total_deduction=Sum('absent_deduction'),
        avg_salary=Avg('net_salary'),
        employee_count=Count('payroll_id')
    )
    
    # Get recent payrolls
    recent_payrolls = tbl_Payroll.objects.filter(
        employee__branch=branch
    ).select_related('employee').order_by('-year', '-month')[:5]
    
    # REPORT 3: Leave Summary for the month
    month_start = date(selected_year, selected_month, 1)
    month_end = date(selected_year, selected_month, monthrange(selected_year, selected_month)[1])
    
    leave_summary = tbl_LeaveRequest.objects.filter(
        employee__branch=branch,
        from_date__lte=month_end,
        to_date__gte=month_start,
        status='approved'
    ).aggregate(
        total_leaves=Count('id'),
        total_employees=Count('employee', distinct=True)
    )
    
    # Leave by type
    leaves_by_type = tbl_LeaveRequest.objects.filter(
        employee__branch=branch,
        from_date__lte=month_end,
        to_date__gte=month_start,
        status='approved'
    ).values('leave_type__leave_name').annotate(
        count=Count('id')
    )
    
    # Calculate total leave days
    total_leave_days = 0
    for leave in tbl_LeaveRequest.objects.filter(
        employee__branch=branch,
        from_date__lte=month_end,
        to_date__gte=month_start,
        status='approved'
    ):
        start = max(leave.from_date, month_start)
        end = min(leave.to_date, month_end)
        if start <= end:
            days = (end - start).days + 1
            if leave.duration_type == 'half_day':
                days = 0.5
            total_leave_days += days
    
    # Generate years for filter
    current_year = datetime.now().year
    years = range(2020, current_year + 3)
    
    context = {
        # Filter info
        'selected_year': selected_year,
        'selected_month': selected_month,
        'month_name': datetime(selected_year, selected_month, 1).strftime('%B'),
        'years': years,
        'months': range(1, 13),
        
        # Report 1: Employee Stats
        'total_employees': total_employees,
        'employees_by_designation': employees_by_designation,
        'monthly_count': monthly_count,
        'daily_count': daily_count,
        
        # Report 2: Payroll Stats
        'total_payroll': payroll_data['total_net'] or 0,
        'total_basic': payroll_data['total_basic'] or 0,
        'total_deductions': payroll_data['total_deduction'] or 0,
        'avg_salary': payroll_data['avg_salary'] or 0,
        'payroll_employee_count': payroll_data['employee_count'] or 0,
        'recent_payrolls': recent_payrolls,
        
        # Report 3: Leave Stats
        'total_leave_requests': leave_summary['total_leaves'] or 0,
        'employees_on_leave': leave_summary['total_employees'] or 0,
        'total_leave_days': total_leave_days,
        'leaves_by_type': leaves_by_type,
    }
    
    return render(request, 'branch_analytics.html', context)
