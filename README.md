# 🚀 Field Visit Tracker

Field Visit Tracker is a web-based application developed using **Django** to simplify the management of employee attendance and client visits. It allows employees to record their daily attendance, manage client visits, and generate reports, while giving administrators a centralized dashboard to monitor overall activities.

The goal of this project is to replace manual tracking methods with a simple, organized, and efficient digital system.

---

# ✨ Features

### Authentication
- Secure login and logout
- Forgot password using email
- Profile management

### Employee Management
- View employee details
- Search employees by name or email
- Filter employees by role
- Update profile information

### Attendance Management
- Check In
- Check Out
- View attendance history
- Search attendance records
- Filter by date and status
- Pagination
- Email notifications after check-in and check-out

### Client Visit Management
Employees can:

- Add new client visits
- Update visit information
- Delete visits
- Track visit status
- Search and filter visit records
- View paginated visit history

Each visit stores:

- Client Name
- Company Name
- Contact Number
- Location
- Visit Date
- Purpose
- Remarks
- Visit Status

---

# 📊 Dashboard

The dashboard provides an overview of important information including:

- Total Employees
- Today's Attendance
- Total Client Visits
- Pending Visits

It also includes interactive charts built using **Chart.js** to visualize:

- Attendance distribution
- Monthly client visits
- Visit status
- Employee-wise visit statistics

---

# 📑 Reports

The Reports module allows users to generate filtered reports based on:

- Date range
- Employee
- Visit status

Reports can be downloaded in multiple formats:

- PDF
- Excel
- CSV

Each report contains attendance statistics along with detailed visit information.

---

# 📧 Email Notifications

Automatic email notifications are sent when:

- An employee checks in
- An employee checks out
- A client visit is created
- A client visit is marked as completed
- A password reset is requested

---

# 🌐 REST APIs

The project also provides read-only REST APIs using **Django REST Framework**.

Available endpoints:

```
/api/employees/
/api/employees/<id>/

/api/attendance/
/api/attendance/<id>/

/api/visits/
/api/visits/<id>/
```

---

# ⚠ Error Handling

Custom error pages have been created for:

- 400 – Bad Request
- 403 – Forbidden
- 404 – Page Not Found
- 500 – Internal Server Error

The application also handles invalid report filters and empty search results gracefully.

---

# 🛠 Tech Stack

### Backend
- Python
- Django
- Django REST Framework

### Frontend
- HTML
- CSS
- Bootstrap 5
- JavaScript
- Chart.js

### Database
- SQLite

### Libraries Used
- ReportLab
- OpenPyXL

---

# 📂 Project Structure

```
FieldVisitTracker
│
├── attendance
├── dashboard
├── employee
├── reports
├── visits
├── templates
├── static
├── config
├── manage.py
└── requirements.txt
```

---

# ⚙ Getting Started

### Clone the repository

```bash
git clone https://github.com/Akshatha2312/Field-Visit-Tracker.git
cd Field-Visit-Tracker
```

### Create a virtual environment

```bash
python -m venv venv
```

Activate it:

Windows

```bash
venv\Scripts\activate
```

Linux / macOS

```bash
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Apply migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Create a superuser

```bash
python manage.py createsuperuser
```

### Run the project

```bash
python manage.py runserver
```

Open your browser and visit:

```
http://127.0.0.1:8000/
```

---

# 🗄 Database Models

### Employee

- Name
- Email
- Phone Number
- Role

### Attendance

- Employee
- Date
- Check In
- Check Out
- Status

### Client Visit

- Employee
- Client Name
- Company Name
- Contact Number
- Location
- Visit Date
- Purpose
- Remarks
- Status

---

# 📸 Screenshots

### Login Page
*(Add screenshot here)*

### Dashboard
*(Add screenshot here)*

### Attendance Module
*(Add screenshot here)*

### Client Visit Module
*(Add screenshot here)*

### Reports
*(Add screenshot here)*

### Dashboard Analytics
*(Add screenshot here)*

### Employee Management
*(Add screenshot here)*

---

# 📦 Report Export

Reports can be downloaded as:

- PDF
- Excel
- CSV

---

# 🔍 Project Highlights

- Employee Attendance Management
- Client Visit Tracking
- Interactive Dashboard
- Report Generation
- PDF, Excel & CSV Export
- Email Notifications
- REST APIs
- Search & Filters
- Pagination
- Responsive Design
- Custom Error Pages

---

# 🚀 Future Improvements

Some features that can be added in the future include:

- Google Maps integration
- Live location tracking
- QR code attendance
- Face recognition attendance
- Mobile application
- Push notifications
- Advanced analytics

---

# 👩‍💻 Author

**Akshatha**

GitHub: https://github.com/Akshatha2312

---

If you found this project useful, consider giving it a ⭐ on GitHub.