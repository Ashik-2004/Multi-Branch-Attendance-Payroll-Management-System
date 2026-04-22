# Multi-Branch Attendance & Payroll Management System

A comprehensive web-based application built with Django designed to effectively manage employee attendance, shift schedules, leave requests, and payroll processes distributed across multiple company branches.

## Features

- **Multi-Branch Capability:** Manage distinct branches, assigning specific managers and staff to each location.
- **Role-Based Portals:** Dedicated dashboards tailored for Administrators, Branch Managers, and Employees.
- **Attendance Tracking:** Easily track and upload daily employee attendance and work hours.
- **Shift & Schedule Management:** Assign varying shifts and schedules directly to employees.
- **Leave Management:** Employees can request time-off while managers review, approve, or reject leaves seamlessly.
- **Payroll Processing:** Streamline employee payroll creation utilizing logged attendance and assigned salary metrics.
- **Analytics & Reporting:** Visual overviews of branch performance, leave counts, and attendance stats.

## Technologies Used

- **Backend:** Python, Django
- **Frontend:** HTML, CSS, JavaScript
- **Database:** MySQL

## Setup & Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Ashik-2004/Multi-Branch-Attendance-Payroll-Management-System.git
   cd Multi-Branch-Attendance-Payroll-Management-System
   ```

2. **Create and Activate a Virtual Environment**
   ```bash
   python -m venv mb_env
   # On Windows:
   mb_env\Scripts\activate
   # On macOS/Linux:
   source mb_env/bin/activate
   ```

3. **Install Dependencies**
   (Ensure you have `requirements.txt` exported, or use standard Django installs)
   ```bash
   pip install django
   ```

4. **Apply Migrations**
   ```bash
   cd mb_project
   python manage.py migrate
   ```

5. **Create a Superuser (Admin)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the Development Server**
   ```bash
   python manage.py runserver
   ```
   Navigate to `http://localhost:8000` in your web browser.

## Author

Developed by [Ashik](https://github.com/Ashik-2004)
