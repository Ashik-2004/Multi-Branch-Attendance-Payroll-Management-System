from django import forms
from .models import tblEmployee, tbl_login, tbl_Branch, tbl_Designation
from django.core.exceptions import ValidationError
import re

from .models import tbl_ShiftSchedule, tbl_ShiftAssignment
from datetime import date
import calendar

class EmployeeForm(forms.ModelForm):
    # Login fields
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'employee@example.com'
        }),
        required=True
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        required=True
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        required=True
    )
    
    employee_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'style': 'background-color: #f8f9fa; cursor: not-allowed;',
            'placeholder': 'Auto-generated'
        })
    )
    
    class Meta:
        model = tblEmployee
        fields = ['employee_code', 'full_name', 'phone', 'designation', 
                  'joining_date', 'salary_type', 'base_salary', 'status']
        widgets = {
            'employee_code': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'style': 'background-color: #f8f9fa;'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'John Doe'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '9876543210'
            }),
            'designation': forms.Select(attrs={
                'class': 'form-control'
            }),
            'joining_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'salary_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'base_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '25000.00',
                'step': '0.01'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.branch = kwargs.pop('branch', None)
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)
        
        # If creating new employee, set initial value for employee code
        if not self.instance.pk and self.branch:
            # Generate next employee code
            from .utils import get_next_employee_code
            next_code = get_next_employee_code(self.branch)
            self.fields['employee_code'].initial = next_code
            self.fields['employee_code'].help_text = f"Auto-generated code: {next_code}"
        
        # If editing, make passwords optional
        if self.instance and self.instance.pk:
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
            self.fields['password'].widget.attrs['placeholder'] = 'Leave blank to keep current password'
            self.fields['confirm_password'].widget.attrs['placeholder'] = 'Leave blank to keep current password'
        
        # Limit designations to active ones
        self.fields['designation'].queryset = tbl_Designation.objects.all()
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone').strip()
        instance = getattr(self, 'instance', None)
        
        # Validate phone format
        if not re.match(r'^\d{10}$', phone):
            raise ValidationError("Phone number must be exactly 10 digits.")
        
        # Check for duplicate phone
        query = tblEmployee.objects.filter(phone=phone)
        if instance and instance.pk:
            query = query.exclude(pk=instance.pk)
        
        if query.exists():
            raise ValidationError("Phone number already exists.")
        
        return phone
    
    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        instance = getattr(self, 'instance', None)
        
        # Check for duplicate email in login table
        if instance and instance.pk:
            # For editing, check if email changed
            if email != instance.login.email:
                if tbl_login.objects.filter(email=email).exists():
                    raise ValidationError("Email already exists.")
        else:
            # For new employee
            if tbl_login.objects.filter(email=email).exists():
                raise ValidationError("Email already exists.")
        
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        # For new employees, password is required
        if not getattr(self, 'instance', None) and (not password or not confirm_password):
            raise ValidationError("Password is required for new employees.")
        
        # Check if passwords match (only if provided)
        if password and password != confirm_password:
            raise ValidationError("Passwords do not match.")
        
        return cleaned_data
    
############forms for scheduling#####################
# forms.py

class ShiftScheduleForm(forms.ModelForm):
    # Define month field explicitly with choices
    month = forms.ChoiceField(
        choices=[],  # Will be populated in __init__
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = tbl_ShiftSchedule
        fields = ['schedule_name', 'month', 'year', 'period']
        widgets = {
            'schedule_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., March 2024 - First Half'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2024,
                'max': 2030
            }),
            'period': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate month choices
        import calendar
        MONTH_CHOICES = [(i, calendar.month_name[i]) for i in range(1, 13)]
        self.fields['month'].choices = [('', '-- Select Month --')] + MONTH_CHOICES
        
        # Set default year
        if not self.instance.pk:
            from datetime import date
            self.fields['year'].initial = date.today().year
            # Set default month to current month
            self.fields['month'].initial = date.today().month
class AssignShiftForm(forms.Form):
    """Simple form to assign shift to employee"""
    
    employee = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    shift = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Optional notes...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.branch = kwargs.pop('branch', None)
        self.schedule = kwargs.pop('schedule', None)
        self.shifts = kwargs.pop('shifts', [])
        super().__init__(*args, **kwargs)
        
        # Get active employees for this branch
        if self.branch:
            from .models import tblEmployee
            employees = tblEmployee.objects.filter(
                branch=self.branch,
                status='active'
            )
            
            # Exclude already assigned employees
            if self.schedule:
                assigned_ids = tbl_ShiftAssignment.objects.filter(
                    schedule=self.schedule
                ).values_list('employee_id', flat=True)
                employees = employees.exclude(employee_id__in=assigned_ids)
            
            # Create choices
            employee_choices = [(emp.employee_id, f"{emp.full_name} ({emp.employee_code})") 
                              for emp in employees]
            self.fields['employee'].choices = [('', '-- Select Employee --')] + employee_choices
        
        # Create shift choices
        shift_choices = [(s.id, f"{s.shift_name} ({s.start_time_12h} - {s.end_time_12h})") 
                        for s in self.shifts]
        self.fields['shift'].choices = [('', '-- Select Shift --')] + shift_choices

class BulkAssignForm(forms.Form):
    """Bulk assign same shift to multiple employees"""
    
    shift = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    employee_list = forms.MultipleChoiceField(
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'style': 'height: 200px;'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.branch = kwargs.pop('branch', None)
        self.schedule = kwargs.pop('schedule', None)
        self.shifts = kwargs.pop('shifts', [])
        super().__init__(*args, **kwargs)
        
        # Get active employees
        if self.branch:
            from .models import tblEmployee
            employees = tblEmployee.objects.filter(
                branch=self.branch,
                status='active'
            )
            
            # Exclude already assigned
            if self.schedule:
                assigned_ids = tbl_ShiftAssignment.objects.filter(
                    schedule=self.schedule
                ).values_list('employee_id', flat=True)
                employees = employees.exclude(employee_id__in=assigned_ids)
            
            # Create choices
            employee_choices = [(emp.employee_id, f"{emp.full_name} ({emp.employee_code})") 
                              for emp in employees]
            self.fields['employee_list'].choices = employee_choices
        
        # Shift choices
        shift_choices = [(s.id, f"{s.shift_name} ({s.start_time_12h} - {s.end_time_12h})") 
                        for s in self.shifts]
        self.fields['shift'].choices = [('', '-- Select Shift --')] + shift_choices
        