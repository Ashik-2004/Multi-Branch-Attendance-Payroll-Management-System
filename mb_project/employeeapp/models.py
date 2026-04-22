from django.db import models
from AdminApp.models import TblLeaveType,tbl_Manager
from branchapp.models import tblEmployee
from django.utils import timezone
# Create your models here.
# Add to your existing models.py file

class tbl_LeaveRequest(models.Model):
    """Leave request model matching your tbl_leave_request structure"""
    
   
    DURATION_TYPES = [
        ('full_day', 'Full Day'),
        ('half_day', 'Half Day'),
        ('multiple_days', 'Multiple Days'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    
    employee = models.ForeignKey(
        'branchapp.tblEmployee',
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    leave_type = models.ForeignKey(
        'AdminApp.TblLeaveType',
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    duration_type = models.CharField(max_length=20, choices=DURATION_TYPES)
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        'AdminApp.tbl_Manager',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'
    )
    applied_date = models.DateTimeField(auto_now_add=True)
    reviewed_date = models.DateTimeField(null=True, blank=True)
    manager_remarks = models.TextField(blank=True)
    supporting_document = models.FileField(
        upload_to='leave_documents/',
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'tbl_leave_request'
        ordering = ['-applied_date']
    
    def __str__(self):
        return f"{self.employee.employee_code} - {self.leave_type.leave_name} ({self.from_date} to {self.to_date})"
    
    def approve(self, manager, remarks=''):
        """Approve leave request"""
        self.status = 'approved'
        self.approved_by = manager
        self.reviewed_date = timezone.now()
        if remarks:
            self.manager_remarks = remarks
        self.save()
        
        # Deduct from leave balance
        try:
            balance = tbl_LeaveBalance.objects.get(
                employee=self.employee,
                year=self.from_date.year
            )
            
            days = self.leave_days
            leave_type_name = self.leave_type.leave_name.lower()
            
            if 'casual' in leave_type_name:
                balance.casual_leave_used += days
            elif 'sick' in leave_type_name:
                balance.sick_leave_used += days
            elif 'earned' in leave_type_name:
                balance.earned_leave_used += days
            
            balance.save()
        except tbl_LeaveBalance.DoesNotExist:
            # Create balance if it doesn't exist
            balance = tbl_LeaveBalance.objects.create(
                employee=self.employee,
                year=self.from_date.year
            )
            # Then deduct
            leave_type_name = self.leave_type.leave_name.lower()
            if 'casual' in leave_type_name:
                balance.casual_leave_used = days
            elif 'sick' in leave_type_name:
                balance.sick_leave_used = days
            elif 'earned' in leave_type_name:
                balance.earned_leave_used = days
            balance.save()
    
    def reject(self, manager, remarks=''):
        """Reject leave request"""
        self.status = 'rejected'
        self.approved_by = manager
        self.reviewed_date = timezone.now()
        if remarks:
            self.manager_remarks = remarks
        self.save()
    
    @property
    def duration_display(self):
        """Get human-readable duration type"""
        if self.duration_type == 'full_day':
            return 'Full Day'
        elif self.duration_type == 'half_day':
            return 'Half Day'
        elif self.duration_type == 'multiple_days':
            return 'Multiple Days'
        return self.duration_type.replace('_', ' ').title()
    @property
    def leave_days(self):
        """Calculate number of leave days"""
        delta = self.to_date - self.from_date
        return delta.days + 1
    
    @property
    def duration_display(self):
        """Get duration in readable format"""
        days = self.leave_days
        if days == 1:
            return "1 Day"
        return f"{days} Days"

class tbl_LeaveBalance(models.Model):
    """Employee leave balance tracking"""
    
    employee = models.OneToOneField(
        'branchapp.tblEmployee',
        on_delete=models.CASCADE,
        related_name='leave_balance'
    )
    casual_leave_total = models.PositiveIntegerField(default=12)
    casual_leave_used = models.PositiveIntegerField(default=0)
    sick_leave_total = models.PositiveIntegerField(default=10)
    sick_leave_used = models.PositiveIntegerField(default=0)
    earned_leave_total = models.PositiveIntegerField(default=30)
    earned_leave_used = models.PositiveIntegerField(default=0)
    year = models.PositiveIntegerField(default=2024)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tbl_leave_balance'
        unique_together = ['employee', 'year']
    
    def __str__(self):
        return f"{self.employee.employee_code} - Leave Balance {self.year}"
    
    @property
    def casual_leave_balance(self):
        return self.casual_leave_total - self.casual_leave_used
    
    @property
    def sick_leave_balance(self):
        return self.sick_leave_total - self.sick_leave_used
    
    @property
    def earned_leave_balance(self):
        return self.earned_leave_total - self.earned_leave_used
    
    @property
    def casual_percentage(self):
        if self.casual_leave_total > 0:
            return (self.casual_leave_used / self.casual_leave_total) * 100
        return 0
    
    @property
    def sick_percentage(self):
        if self.sick_leave_total > 0:
            return (self.sick_leave_used / self.sick_leave_total) * 100
        return 0
    
    @property
    def earned_percentage(self):
        if self.earned_leave_total > 0:
            return (self.earned_leave_used / self.earned_leave_total) * 100
        return 0
    
    def can_apply_leave(self, leave_type, days):
        """Check if employee can apply for leave"""
        if leave_type == 'casual':
            return days <= self.casual_leave_balance
        elif leave_type == 'sick':
            return days <= self.sick_leave_balance
        elif leave_type == 'earned':
            return days <= self.earned_leave_balance
        return False
    
    def deduct_leave(self, leave_type, days):
        """Deduct leave days after approval"""
        if leave_type == 'casual':
            self.casual_leave_used += days
        elif leave_type == 'sick':
            self.sick_leave_used += days
        elif leave_type == 'earned':
            self.earned_leave_used += days
        self.save()