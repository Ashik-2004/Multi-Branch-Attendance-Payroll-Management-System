# branchapp/utils/__init__.py
from .employee_code import get_next_employee_code

__all__ = [
    'get_next_employee_code',
    'parse_attendance_excel',
    'export_salary_to_excel',
    'generate_attendance_template',
]