from django.shortcuts import render
from django.contrib import messages
from datetime import datetime
from branchapp.models import tbl_Payroll
from datetime import datetime, date, timedelta
from calendar import monthrange
from branchapp.models import tbl_ShiftAssignment
from HomeApp.models import tbl_login
# Create your views here.
###########leave management
# views.py
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
from datetime import date
from .models import tbl_LeaveRequest, tbl_LeaveBalance
from branchapp.models import tblEmployee
from AdminApp.models import TblLeaveType, tbl_Manager


def employee_leave_dashboard(request):
    #user=tblEmployee.objects.get(employee_id=request.session['user_id'])
    """Employee leave management view"""
    try:
        # Get employee profile from logged in user
        employee = tblEmployee.objects.get(employee_id=request.session['user_id'])
        print(f"Employee found: {employee.full_name} (ID: {employee.employee_id})")  # Debug print
        # Get or create leave balance for current year
        current_year = timezone.now().year
        leave_balance, created = tbl_LeaveBalance.objects.get_or_create(
            employee=employee,
            year=current_year,
            defaults={
                'casual_leave_total': 12,
                'sick_leave_total': 10,
                'earned_leave_total': 30
            }
        )
        
        # Get all leave types for dropdown
        leave_types = TblLeaveType.objects.all()
        
        # Get leave requests
        leave_requests = tbl_LeaveRequest.objects.filter(
            employee=employee
        ).select_related('leave_type', 'approved_by')[:5]  # Last 5 requests with related fields
        
        # Handle form submission
        if request.method == 'POST':
            try:
                # Get form data
                leave_type_id = request.POST.get('leave_type')
                duration_type = request.POST.get('duration_type')
                from_date = request.POST.get('from_date')
                to_date = request.POST.get('to_date')
                reason = request.POST.get('reason')
                supporting_doc = request.FILES.get('supporting_document')
                
                # Validate dates
                from_date_obj = date.fromisoformat(from_date)
                to_date_obj = date.fromisoformat(to_date)
                
                if from_date_obj > to_date_obj:
                    messages.error(request, 'End date cannot be before start date')
                    return redirect('employee_leave_dashboard')
                
                if from_date_obj < date.today():
                    messages.error(request, 'Cannot apply for leave in the past')
                    return redirect('employee_leave_dashboard')
                
                # Calculate days
                days = (to_date_obj - from_date_obj).days + 1
                
                # Validate duration type
                if duration_type in ['full_day', 'half_day'] and days != 1:
                    messages.error(request, 'For single day leave, start and end date must be same')
                    return redirect('employee_leave_dashboard')
                elif duration_type == 'multiple_days' and days < 2:
                    messages.error(request, 'For multiple days leave, select at least 2 days')
                    return redirect('employee_leave_dashboard')
                
                # Get leave type
                leave_type = TblLeaveType.objects.get(id=leave_type_id)
                
                # Check leave balance
                leave_type_name = leave_type.leave_name.lower()
                if 'casual' in leave_type_name:
                    if days > leave_balance.casual_leave_balance:
                        messages.error(request, f'Insufficient casual leave balance. Available: {leave_balance.casual_leave_balance} days')
                        return redirect('employee_leave_dashboard')
                elif 'sick' in leave_type_name:
                    if days > leave_balance.sick_leave_balance:
                        messages.error(request, f'Insufficient sick leave balance. Available: {leave_balance.sick_leave_balance} days')
                        return redirect('employee_leave_dashboard')
                elif 'earned' in leave_type_name:
                    if days > leave_balance.earned_leave_balance:
                        messages.error(request, f'Insufficient earned leave balance. Available: {leave_balance.earned_leave_balance} days')
                        return redirect('employee_leave_dashboard')
                
                # Create leave request
                leave_request = tbl_LeaveRequest(
                    employee=employee,
                    leave_type=leave_type,
                    duration_type=duration_type,
                    from_date=from_date_obj,
                    to_date=to_date_obj,
                    reason=reason,
                    status='pending',
                    supporting_document=supporting_doc
                )
                leave_request.save()
                
                messages.success(request, 'Leave application submitted successfully!')
                return redirect('employee_leave_dashboard')
                
            except Exception as e:
                messages.error(request, f'Error submitting leave application: {str(e)}')
                return redirect('employee_leave_dashboard')
        
        context = {
            'employee': employee,
            'leave_balance': leave_balance,
            'leave_requests': leave_requests,
            'leave_types': leave_types,
            'today': date.today(),
        }
        
        print(context)
        return render(request, 'employee_leave.html', context)
        
    except tblEmployee.DoesNotExist:
        print("Employee not found for user ID:", request.session['user_id'])  # Debug print
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    except Exception as e:
        print(f"Error in employee_leave_dashboard: {str(e)}")  # Debug print
        messages.error(request, f'Error: {str(e)}')
        return redirect('employee_dashboard')


def cancel_leave_request(request):
    """Cancel a pending leave request"""
    try:
        data = json.loads(request.body)
        leave_id = data.get('leave_id')
        
        employee = tblEmployee.objects.get(employee_id=request.session['user_id'])
        leave_request = get_object_or_404(
            tbl_LeaveRequest, 
            leave_id=leave_id, 
            employee=employee
        )
        
        if leave_request.status == 'pending':
            leave_request.status = 'rejected'  # Or use 'cancelled' if you add it to choices
            leave_request.save()
            return JsonResponse({
                'success': True,
                'message': 'Leave request cancelled successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Only pending requests can be cancelled'
            }, status=400)
            
    except tblEmployee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Employee not found'
        }, status=400)
    except tbl_LeaveRequest.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Leave request not found'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


def get_leave_requests_api(request):
    """API endpoint to get leave requests (for AJAX)"""
    try:
        employee = tblEmployee.objects.get(employee_id=request.session['user_id'])
        leave_requests = tbl_LeaveRequest.objects.filter(
            employee=employee
        ).select_related('leave_type').values(
            'leave_id', 
            'leave_type__leave_name', 
            'duration_type', 
            'from_date', 
            'to_date', 
            'status', 
            'applied_date'
        ).order_by('-applied_date')
        
        # Format dates for JSON
        formatted_requests = []
        for req in leave_requests:
            from_date = req['from_date']
            to_date = req['to_date']
            
            # Calculate duration display
            delta = to_date - from_date
            days = delta.days + 1
            if days == 1:
                duration_display = "1 Day"
            else:
                duration_display = f"{days} Days"
            
            formatted_requests.append({
                'leave_id': req['leave_id'],
                'leave_type': req['leave_type__leave_name'],
                'duration_type': req['duration_type'],
                'from_date': from_date.strftime('%Y-%m-%d'),
                'to_date': to_date.strftime('%Y-%m-%d'),
                'status': req['status'],
                'applied_date': req['applied_date'].strftime('%Y-%m-%d %H:%M'),
                'duration_display': duration_display
            })
        
        return JsonResponse({
            'success': True,
            'leave_requests': formatted_requests
        })
        
    except tblEmployee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Employee not found'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

def get_leave_balance_api(request):
    """API endpoint to get leave balance"""
    try:
        employee = tblEmployee.objects.get(employee_id=request.session['user_id'])
        current_year = timezone.now().year
        
        leave_balance, created = tbl_LeaveBalance.objects.get_or_create(
            employee=employee,
            year=current_year,
            defaults={
                'casual_leave_total': 12,
                'sick_leave_total': 10,
                'earned_leave_total': 30
            }
        )
        
        return JsonResponse({
            'success': True,
            'casual': {
                'total': leave_balance.casual_leave_total,
                'used': leave_balance.casual_leave_used,
                'balance': leave_balance.casual_leave_balance,
                'percentage': leave_balance.casual_percentage
            },
            'sick': {
                'total': leave_balance.sick_leave_total,
                'used': leave_balance.sick_leave_used,
                'balance': leave_balance.sick_leave_balance,
                'percentage': leave_balance.sick_percentage
            },
            'earned': {
                'total': leave_balance.earned_leave_total,
                'used': leave_balance.earned_leave_used,
                'balance': leave_balance.earned_leave_balance,
                'percentage': leave_balance.earned_percentage
            }
        })
        
    except tblEmployee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Employee not found'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)





#############employee payslip management

def employee_salary(request):
    """Employee view to see their salary details"""
    
    # Get employee from session
    try:
        if 'user_id' not in request.session:
            messages.error(request, 'Please login first')
            return redirect('login')
            
        employee = tblEmployee.objects.get(employee_id=request.session['user_id'])
    except tblEmployee.DoesNotExist:
        messages.error(request, 'Employee profile not found')
        return redirect('login')
    
    # Get current month and year
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Get current month's payroll
    current_payroll = tbl_Payroll.objects.filter(
        employee=employee,
        month=current_month,
        year=current_year
    ).first()
    
    # Get all payroll history for this employee
    payroll_history = tbl_Payroll.objects.filter(
        employee=employee
    ).order_by('-year', '-month')
    
    context = {
        'employee': employee,
        'current_payroll': current_payroll,
        'payroll_history': payroll_history,
        'current_month': current_month,
        'current_year': current_year,
        'month_name': datetime(current_year, current_month, 1).strftime('%B')
    }
    
    return render(request, 'employee_salary.html', context)

def employee_payslip(request, payroll_id):
    """View single payslip details"""
    
    # Get employee from session
    try:
        if 'user_id' not in request.session:
            messages.error(request, 'Please login first')
            return redirect('login')
            
        employee = tblEmployee.objects.get(employee_id=request.session['user_id'])
    except tblEmployee.DoesNotExist:
        messages.error(request, 'Employee profile not found')
        return redirect('login')
    
    # Get the specific payroll (ensure it belongs to this employee)
    payroll = get_object_or_404(tbl_Payroll, payroll_id=payroll_id, employee=employee)
    
    # Calculate attendance percentage
    attendance_percent = 0
    if payroll.total_days > 0:
        attendance_percent = (payroll.present_days / payroll.total_days) * 100
    
    # Calculate working days
    working_days = payroll.total_days - payroll.holidays
    
    context = {
        'employee': employee,
        'payroll': payroll,
        'attendance_percent': round(attendance_percent, 2),
        'month_name': datetime(payroll.year, payroll.month, 1).strftime('%B'),
        'working_days': working_days
    }
    
    return render(request, 'employee_payslip.html', context)


############attendance management

def employee_attendance(request):
    """Employee view to see their attendance history"""
    
    # Get employee from session
    try:
        if 'user_id' not in request.session:
            messages.error(request, 'Please login first')
            return redirect('login')
            
        employee = tblEmployee.objects.get(employee_id=request.session['user_id'])
    except tblEmployee.DoesNotExist:
        messages.error(request, 'Employee profile not found')
        return redirect('login')
    
    # Get filter parameters
    selected_month = int(request.GET.get('month', datetime.now().month))
    selected_year = int(request.GET.get('year', datetime.now().year))
    
    # Get month details
    month_start = date(selected_year, selected_month, 1)
    month_end = date(selected_year, selected_month, monthrange(selected_year, selected_month)[1])
    
    # Get holidays for this month
    from AdminApp.models import TblHoliday
    holidays = TblHoliday.objects.filter(
        holiday_date__range=[month_start, month_end]
    ).values_list('holiday_date', flat=True)
    
    # Get approved leaves for this month
    leaves = tbl_LeaveRequest.objects.filter(
        employee=employee,
        status='approved',
        from_date__lte=month_end,
        to_date__gte=month_start
    )
    
    # Create a dictionary of leave dates
    leave_dates = {}
    for leave in leaves:
        start = max(leave.from_date, month_start)
        end = min(leave.to_date, month_end)
        current = start
        while current <= end:
            if leave.duration_type == 'half_day':
                leave_dates[current] = 'half_day'
            else:
                leave_dates[current] = 'full_day'
            current += timedelta(days=1)
    
    # Get shift assignments for this month
    assignments = tbl_ShiftAssignment.objects.filter(
        employee=employee,
        schedule__month=selected_month,
        schedule__year=selected_year
    ).select_related('shift', 'schedule')
    
    # Generate daily attendance for the month
    attendance_data = []
    total_present = 0
    total_absent = 0
    total_leave = 0
    total_holiday = 0
    
    current_date = month_start
    while current_date <= month_end:
        day_data = {
            'date': current_date,
            'day_name': current_date.strftime('%A'),
            'is_holiday': current_date in holidays,
            'leave_type': leave_dates.get(current_date, None),
            'shift': None,
            'status': 'present'  # Default status
        }
        
        # Check if holiday
        if day_data['is_holiday']:
            day_data['status'] = 'holiday'
            day_data['remarks'] = 'Holiday'
            total_holiday += 1
        # Check if leave
        elif day_data['leave_type']:
            if day_data['leave_type'] == 'half_day':
                day_data['status'] = 'half_day_leave'
                day_data['remarks'] = 'Half Day Leave'
                total_leave += 0.5
            else:
                day_data['status'] = 'leave'
                day_data['remarks'] = 'Full Day Leave'
                total_leave += 1
        else:
            # Find shift for this date
            for assignment in assignments:
                if assignment.schedule.start_date <= current_date <= assignment.schedule.end_date:
                    day_data['shift'] = assignment.shift
                    break
            
            if day_data['shift']:
                day_data['status'] = 'present'
                day_data['remarks'] = f"Present - {day_data['shift'].shift_name}"
                total_present += 1
            else:
                # No shift assigned, considered absent
                day_data['status'] = 'absent'
                day_data['remarks'] = 'No shift assigned'
                total_absent += 1
        
        attendance_data.append(day_data)
        current_date += timedelta(days=1)
    
    # Calculate summary
    total_days = len(attendance_data)
    working_days = total_days - total_holiday
    attendance_percent = 0
    if working_days > 0:
        attendance_percent = (total_present / working_days) * 100
    
    # Generate years for filter
    current_year = datetime.now().year
    years = range(2020, current_year + 3)
    
    context = {
        'employee': employee,
        'attendance_data': attendance_data,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'month_name': datetime(selected_year, selected_month, 1).strftime('%B'),
        'months': range(1, 13),
        'years': years,
        'summary': {
            'total_days': total_days,
            'present': total_present,
            'absent': total_absent,
            'leave': total_leave,
            'holiday': total_holiday,
            'working_days': working_days,
            'attendance_percent': round(attendance_percent, 2)
        }
    }
    
    return render(request, 'employee_attendance.html', context)


#######change password

def change_password(request):
    """Allow employee to change their password"""
    
    # Check if user is logged in
    if 'user_id' not in request.session:
        messages.error(request, 'Please login first')
        return redirect('login')
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Get user login details
        try:
            user = tbl_login.objects.get(id=request.session['login_id'])
        except tbl_login.DoesNotExist:
            messages.error(request, 'User not found')
            return redirect('login')
        
        # Validate current password
        if user.password != current_password:
            messages.error(request, 'Current password is incorrect')
            return redirect('change_password')
        
        # Check if new password and confirm password match
        if new_password != confirm_password:
            messages.error(request, 'New password and confirm password do not match')
            return redirect('change_password')
        
        # Check if new password is empty
        if not new_password:
            messages.error(request, 'New password cannot be empty')
            return redirect('change_password')
        
        # Update password (no hashing)
        user.password = new_password
        user.save()
        
        messages.success(request, 'Password changed successfully!')
        return redirect('login')  # Redirect to home or dashboard
    
    return render(request, 'change_password.html')