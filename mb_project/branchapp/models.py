from django.db import models
from HomeApp.models import tbl_login
from AdminApp.models import tbl_Branch, tbl_Designation,TblHoliday
from AdminApp.models import tbl_Shift,tbl_Branch,tbl_Manager
from django.core.exceptions import ValidationError
from datetime import timedelta, date, datetime
from django.utils import timezone


from django.db.models import Max

class tblEmployee(models.Model):
    SALARY_TYPE_CHOICES = (
        ('monthly', 'Monthly'),
        ('daily', 'Daily'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    employee_id = models.AutoField(primary_key=True)
    employee_code = models.CharField(max_length=20,blank=True)
    
    login = models.ForeignKey(
        tbl_login,
        on_delete=models.CASCADE,
        related_name='employees'
    )

    branch = models.ForeignKey(
        tbl_Branch,
        on_delete=models.CASCADE,
        related_name='employees'
    )

    designation = models.ForeignKey(
        tbl_Designation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )

    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, unique=True)
    joining_date = models.DateField()
    
    salary_type = models.CharField(
        max_length=10,
        choices=SALARY_TYPE_CHOICES
    )

    base_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generate employee code only if not already set
        if not self.employee_code:
            from .utils import get_next_employee_code
            self.employee_code = get_next_employee_code(self.branch)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.employee_code})"
    


#############models for employee scheduling#####################
# In your models.py

class tbl_ShiftSchedule(models.Model):
    """Master schedule for 15-day shift patterns"""
    
    PERIOD_CHOICES = (
        ('first_half', '1st - 15th'),
        ('second_half', '16th - 30th/31st'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    )
    
    schedule_id = models.AutoField(primary_key=True)
    schedule_name = models.CharField(max_length=200)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    month = models.PositiveIntegerField()  # 1-12
    year = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(
        'AdminApp.tbl_Manager',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_schedules'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    def __str__(self):
        return f"{self.schedule_name} - {self.get_period_display()} {self.month}/{self.year}"
    
    @property
    def start_date(self):
        """Get start date of this schedule period"""
        if self.period == 'first_half':
            return date(self.year, self.month, 1)
        else:  # second_half
            return date(self.year, self.month, 16)
    
    @property
    def end_date(self):
        """Get end date of this schedule period"""
        if self.period == 'first_half':
            return date(self.year, self.month, 15)
        else:  # second_half
            # Handle month-end correctly
            import calendar
            last_day = calendar.monthrange(self.year, self.month)[1]
            return date(self.year, self.month, last_day)
    
    @property
    def date_range(self):
        """Get all dates in this schedule"""
        start = self.start_date
        end = self.end_date
        delta = timedelta(days=1)
        
        dates = []
        current_date = start
        while current_date <= end:
            dates.append(current_date)
            current_date += delta
        
        return dates
    
    @property
    def is_current(self):
        """Check if this schedule is for current period"""
        today = date.today()
        return self.start_date <= today <= self.end_date
    
    @property
    def is_future(self):
        """Check if this schedule is for future period"""
        today = date.today()
        return self.start_date > today
    
    @property
    def duration_days(self):
        """Get duration in days"""
        return (self.end_date - self.start_date).days + 1

class tbl_ShiftAssignment(models.Model):
    """Shift assignment for an employee for a 15-day period"""
    
    assignment_id = models.AutoField(primary_key=True)
    schedule = models.ForeignKey(
        tbl_ShiftSchedule,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    employee = models.ForeignKey(
        'tblEmployee',
        on_delete=models.CASCADE,
        related_name='shift_assignments'
    )
    shift = models.ForeignKey(
        'AdminApp.tbl_Shift',
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['schedule', 'employee']
        ordering = ['schedule', 'employee']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.shift.shift_name} ({self.schedule})"
    
    @property
    def daily_attendance(self):
        """Get attendance records for each day"""
        return self.attendance_records.all()
    
    @property
    def present_days(self):
        """Count present days"""
        return self.attendance_records.filter(status='present').count()
    
    @property
    def absent_days(self):
        """Count absent days"""
        return self.attendance_records.filter(status='absent').count()
    
    @property
    def leave_days(self):
        """Count leave days"""
        return self.attendance_records.filter(status='on_leave').count()
    
    @property
    def attendance_summary(self):
        """Get attendance summary"""
        return {
            'total_days': self.schedule.duration_days,
            'present': self.present_days,
            'absent': self.absent_days,
            'leave': self.leave_days,
            'attendance_rate': round((self.present_days / self.schedule.duration_days) * 100, 2)
        }


# branchapp/models.py (add this)

class tbl_Payroll(models.Model):
    """Payroll model for monthly salary calculation"""
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    )
    
    payroll_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        'tblEmployee',
        on_delete=models.CASCADE,
        related_name='payrolls'
    )
    month = models.PositiveIntegerField()  # 1-12
    year = models.PositiveIntegerField()
    
    # Basic Info
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    salary_type = models.CharField(max_length=10)  # monthly or daily
    
    # Attendance
    total_days = models.PositiveIntegerField(default=0)
    present_days = models.PositiveIntegerField(default=0)
    absent_days = models.PositiveIntegerField(default=0)
    leave_days = models.PositiveIntegerField(default=0)
    holidays = models.PositiveIntegerField(default=0)
    
    # Calculations
    absent_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS, 
        default='pending'
    )
    payment_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['employee', 'month', 'year']
    
    def __str__(self):
        return f"{self.employee.employee_code} - {self.month}/{self.year}"