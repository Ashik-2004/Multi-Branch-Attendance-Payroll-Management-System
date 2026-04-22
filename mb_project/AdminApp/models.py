from django.db import models
from HomeApp.models import tbl_login
class tbl_Branch(models.Model):
    name = models.CharField(max_length=150, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    contact_no = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    status=models.CharField(max_length=25,default="Active")
    def __str__(self):
        return f"{self.name} - {self.city}"

   
class tbl_Manager(models.Model):
     manager_id = models.AutoField(primary_key=True)
     login = models.ForeignKey(tbl_login,
       
        on_delete=models.CASCADE,
       
    )
     branch=models.ForeignKey(tbl_Branch,on_delete=models.CASCADE)

     name = models.CharField(max_length=150)
     phone = models.CharField(max_length=10)

     status = models.CharField(
        max_length=10,
        choices=(
            ('Active', 'Active'),
            ('Inactive', 'Inactive'),
        ),
        default='Active'
    )

     created_at = models.DateTimeField(auto_now_add=True)
                                      
     def __str__(self):
         return self.name
     



class tbl_Designation(models.Model):
   

    role = models.CharField(
        max_length=100,
        unique=True
    )

    

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.role
class tbl_Shift(models.Model):
    shift_name = models.CharField(max_length=100, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    allowed_late_minutes = models.PositiveIntegerField(
        help_text="Grace time in minutes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.shift_name

    @property
    def duration_hours(self):
        """Calculate shift duration in hours"""
        start = self.start_time
        end = self.end_time
        
        # Calculate difference
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        
        if end_minutes < start_minutes:
            # Overnight shift
            end_minutes += 24 * 60
        
        duration_minutes = end_minutes - start_minutes
        return round(duration_minutes / 60, 2)
    
    @property
    def duration_display(self):
        """Get duration in HH:MM format"""
        hours = int(self.duration_hours)
        minutes = int((self.duration_hours - hours) * 60)
        return f"{hours}:{minutes:02d}"
    
    @property
    def duration_percentage(self):
        """Get duration as percentage of 8 hours"""
        return min((self.duration_hours / 8) * 100, 100)
    
    @property
    def start_time_12h(self):
        """Get start time in 12-hour format"""
        return self.start_time.strftime("%I:%M %p").lstrip('0')
    
    @property
    def end_time_12h(self):
        """Get end time in 12-hour format"""
        return self.end_time.strftime("%I:%M %p").lstrip('0')
    
    @property
    def start_time_24h(self):
        """Get start time in 24-hour format"""
        return self.start_time.strftime("%H:%M")
    
    @property
    def end_time_24h(self):
        """Get end time in 24-hour format"""
        return self.end_time.strftime("%H:%M")
    
####model for leave type
class TblLeaveType(models.Model):
    
    leave_name = models.CharField(max_length=100)
    max_days = models.PositiveIntegerField()

    def __str__(self):
        return self.leave_name
class TblHoliday(models.Model):
    HOLIDAY_TYPE_CHOICES = [
        ('National', 'National'),
        ('Festival', 'Festival'),
        ('Company', 'Company'),
    ]

    holiday_name = models.CharField(max_length=150)
    holiday_date = models.DateField()
    holiday_type = models.CharField(
        max_length=20,
        choices=HOLIDAY_TYPE_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.holiday_name} - {self.holiday_date}"