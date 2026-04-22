from django import forms
from .models import *
import re
from datetime import datetime
from django.core.exceptions import ValidationError
class BranchForm(forms.ModelForm):

    class Meta:
        model = tbl_Branch
        fields = ['name', 'address', 'city', 'contact_no']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Branch Name'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Branch Address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'contact_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10-digit Contact Number'
            }),
        }

    def clean_contact_no(self):
        contact_no = self.cleaned_data.get('contact_no')

        # Allow only 10 digits
        if not re.fullmatch(r'\d{10}', contact_no):
            raise forms.ValidationError(
                "Contact number must be exactly 10 digits."
            )
        return contact_no 
    




class ManagerForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=True
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = tbl_Manager
        fields = ['branch', 'name', 'phone']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        instance = kwargs.get('instance')
        
        if instance:
            # For editing: show all branches, we'll handle validation in clean()
            self.fields['branch'].queryset = tbl_Branch.objects.all()
            # For editing, passwords are optional
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
        else:
            # For adding: only show branches without active managers
            # Get IDs of branches that have active managers
            active_manager_branch_ids = tbl_Manager.objects.filter(
                status='Active'
            ).values_list('branch_id', flat=True)
            
            # Show all branches except those with active managers
            self.fields['branch'].queryset = tbl_Branch.objects.exclude(
                id__in=active_manager_branch_ids
            )
            
            # Debug: print available branches
            print(f"DEBUG: Available branches for new manager: {list(self.fields['branch'].queryset.values_list('name', flat=True))}")

    # ---------------- VALIDATIONS ----------------
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise ValidationError("Name is required.")
        
        # Allow only letters and spaces
        if not re.fullmatch(r'[A-Za-z ]+', name):
            raise ValidationError("Name can contain only letters and spaces.")
        
        return name.strip()

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise ValidationError("Phone number is required.")
        
        # Allow only 10 digits
        if not re.fullmatch(r'\d{10}', phone):
            raise ValidationError("Phone number must be exactly 10 digits.")
        
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required.")
        
        # Check if instance exists (editing)
        instance = getattr(self, 'instance', None)
        
        if instance and instance.pk:
            # For editing: check if email changed and already exists
            if email != instance.login.email:
                if tbl_login.objects.filter(email=email).exists():
                    raise ValidationError("Email already exists.")
        else:
            # For adding: check if email exists
            if tbl_login.objects.filter(email=email).exists():
                raise ValidationError("Email already exists.")
        
        return email

    def clean(self):
        cleaned_data = super().clean()
        
        # Get instance to check if we're editing
        instance = getattr(self, 'instance', None)
        
        # Get password fields
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        # If creating new manager, password is required
        if not instance and (not password or not confirm_password):
            raise ValidationError("Password is required for new managers.")
        
        # If editing and passwords are provided, validate them
        if instance and password:
            if password != confirm_password:
                raise ValidationError("Passwords do not match.")
        
        # If creating new manager, validate passwords match
        if not instance and password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match.")
        
        # Branch validation (only for new managers or when branch is changed)
        branch = cleaned_data.get('branch')
        if branch:
            # Check if branch already has an active manager
            # Exclude current instance if editing
            query = tbl_Manager.objects.filter(branch=branch, status='Active')
            
            if instance and instance.pk:
                query = query.exclude(pk=instance.pk)
            
            if query.exists():
                raise ValidationError("This branch already has an active manager.")
        
        return cleaned_data
class DesignationForm(forms.ModelForm):

    class Meta:
        model = tbl_Designation
        fields = ['role']
        widgets = {
            'role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Designation (e.g., Manager)'
            }),
        }

    def clean_role(self):
        role = self.cleaned_data.get('role')

        # Trim spaces
        role = role.strip()

        # Allow letters and spaces only
        if not re.fullmatch(r'[A-Za-z ]+', role):
            raise forms.ValidationError(
                "Designation must contain only letters and spaces."
            )

        # Prevent duplicate (case-insensitive)
        if tbl_Designation.objects.filter(role__iexact=role).exists():
            raise forms.ValidationError(
                "This designation already exists."
            )
        return role
class ShiftForm(forms.ModelForm):
    # Use text input with pattern for better time entry
    start_time = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control time-input',
            'placeholder': 'HH:MM (24-hour format)',
            'pattern': '^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
        }),
        help_text="Enter time in 24-hour format (e.g., 09:00, 14:30)"
    )
    
    end_time = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control time-input',
            'placeholder': 'HH:MM (24-hour format)',
            'pattern': '^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
        }),
        help_text="Enter time in 24-hour format (e.g., 17:00, 22:30)"
    )

    class Meta:
        model = tbl_Shift
        fields = ['shift_name', 'start_time', 'end_time', 'allowed_late_minutes']
        widgets = {
            'shift_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Shift Name (e.g. Morning Shift, Night Shift)'
            }),
            'allowed_late_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Grace time in minutes (0-120)',
                'min': '0',
                'max': '120',
                'step': '5'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing, convert TimeField to string for display
        if self.instance and self.instance.pk:
            self.initial['start_time'] = self.instance.start_time.strftime('%H:%M')
            self.initial['end_time'] = self.instance.end_time.strftime('%H:%M')
    
    # VALIDATION: Time format conversion
    def clean_start_time(self):
        time_str = self.cleaned_data.get('start_time')
        try:
            # Parse 24-hour format
            return datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            # Also accept 12-hour format with AM/PM
            try:
                return datetime.strptime(time_str, '%I:%M %p').time()
            except ValueError:
                raise ValidationError("Enter time in HH:MM format (24-hour) or HH:MM AM/PM")

    def clean_end_time(self):
        time_str = self.cleaned_data.get('end_time')
        try:
            # Parse 24-hour format
            return datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            # Also accept 12-hour format with AM/PM
            try:
                return datetime.strptime(time_str, '%I:%M %p').time()
            except ValueError:
                raise ValidationError("Enter time in HH:MM format (24-hour) or HH:MM AM/PM")

    # VALIDATION: Shift Name
    def clean_shift_name(self):
        name = self.cleaned_data.get('shift_name').strip()
        
        if not name:
            raise ValidationError("Shift name is required.")

        # Check for duplicate (case-insensitive, excluding current instance)
        query = tbl_Shift.objects.filter(shift_name__iexact=name)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise ValidationError("Shift name already exists.")

        return name

    # VALIDATION: Grace Time
    def clean_allowed_late_minutes(self):
        minutes = self.cleaned_data.get('allowed_late_minutes')
        
        if minutes is None:
            raise ValidationError("Grace time is required.")

        if minutes < 0:
            raise ValidationError("Grace time cannot be negative.")

        if minutes > 120:
            raise ValidationError("Grace time cannot exceed 120 minutes.")

        return minutes

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        
        if start and end:
            # Convert to minutes for calculation
            start_minutes = start.hour * 60 + start.minute
            end_minutes = end.hour * 60 + end.minute
            
            # Handle overnight shifts
            if end_minutes < start_minutes:
                end_minutes += 24 * 60
            
            # Calculate duration
            duration_minutes = end_minutes - start_minutes
            
            # Check if shift exceeds 8 hours
            if duration_minutes > (8 * 60):  # 8 hours in minutes
                raise ValidationError(
                    f"Shift duration cannot exceed 8 hours. Current duration: {duration_minutes/60:.1f} hours."
                )
            
            # Check if start and end times are the same
            if start == end:
                raise ValidationError("Start time and end time cannot be the same.")
        
        return cleaned_data
    
class LeaveTypeForm(forms.ModelForm):
    class Meta:
        model = TblLeaveType
        fields = ['leave_name', 'max_days']
        widgets = {
            'leave_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter leave name'
            }),
            'max_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter max days'
            }),
        }


class HolidayForm(forms.ModelForm):
    class Meta:
        model = TblHoliday
        fields = ['holiday_name', 'holiday_date', 'holiday_type']
        widgets = {
            'holiday_name': forms.TextInput(attrs={'class': 'form-control'}),
            'holiday_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'holiday_type': forms.Select(attrs={'class': 'form-control'}),
        }