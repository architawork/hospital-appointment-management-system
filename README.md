# Hospital Appointment Management System

## Description
A system to manage doctor schedules, patient appointments, and visit history in a hospital.

## Task Definition
Develop a REST API that allows:

- Patient and doctor registration
- Appointment booking and cancellation
- Doctor availability management
- Medical visit history tracking
- Authentication for patients and doctors

## Technical Requirements
- Python 3.8+
- FastAPI
- SQLAlchemy
- Pydantic
- JWT Authentication
- SQLite / PostgreSQL

## Functional Requirements
- CRUD operations for patients, doctors, and appointments
- Role-based access control (doctor vs patient)
- Prevention of overlapping appointments
- Search appointments by date and doctor
- Appointment status tracking:
  - Booked
  - Cancelled
  - Completed
