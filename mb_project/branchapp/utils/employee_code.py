from django.db.models import Max
from branchapp.models import tblEmployee 

from django.db.models import Max

def get_next_employee_code(branch):
    """
    Get the next available employee code for a branch
    Format: EMP{branch_id}{sequential_number}
    """
    # Get the highest employee number for this branch
    highest_emp = tblEmployee.objects.filter(
        branch=branch
    ).aggregate(Max('employee_code'))
    
    # Extract the numeric part from existing codes
    highest_number = 0
    if highest_emp['employee_code__max']:
        try:
            code = highest_emp['employee_code__max']
            # Remove EMP prefix and get number
            if code.startswith('EMP'):
                number_part = code[3:]  # Remove 'EMP'
                highest_number = int(number_part)
        except:
            highest_number = 0
    
    next_number = highest_number + 1
    return f'EMP{next_number:05d}'  # 5-digit zero-padded number