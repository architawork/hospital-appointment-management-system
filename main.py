from fastapi import FastAPI,Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime,timedelta
from typing import List,Optional
import schemas
import auth
import models
from database import engine,get_db

models.Base.metadata.create_all(bind=engine)
app=FastAPI(title="Hospital Appointment Management System")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#Authentication
@app.post("/register/patient",response_model=schemas.UserResponse)
def register_patient(user:schemas.UserCreate,db:Session=Depends(get_db)):
    db_user=db.query(models.User).filter(models.User.email==user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password=auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role="patient"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/register/doctor", response_model=schemas.UserResponse)
def register_doctor(user: schemas.DoctorCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role="doctor",
        specialization=user.specialization
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

#login
@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@app.get("/doctors", response_model=List[schemas.UserResponse])
def get_all_doctors(db: Session = Depends(get_db)):
    doctors = db.query(models.User).filter(models.User.role == "doctor").all()
    return doctors


@app.get("/doctors/{doctor_id}", response_model=schemas.UserResponse)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(models.User).filter(
        models.User.id == doctor_id, 
        models.User.role == "doctor"
    ).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@app.post("/availability", response_model=schemas.AvailabilityResponse)
def create_availability(availability: schemas.AvailabilityCreate,current_user: models.User = Depends(auth.get_doctor),db: Session = Depends(get_db)
):
    overlap = db.query(models.Availability).filter(
        models.Availability.doctor_id == current_user.id,
        models.Availability.date == availability.date,
        models.Availability.start_time < availability.end_time,
        models.Availability.end_time > availability.start_time
    ).first()
    
    if overlap:
        raise HTTPException(status_code=400, detail="slots overlap")
    
    db_availability = models.Availability(
        doctor_id=current_user.id,
        date=availability.date,
        start_time=availability.start_time,
        end_time=availability.end_time
    )
    db.add(db_availability)
    db.commit()
    db.refresh(db_availability)
    return db_availability

@app.get("/availability/doctor/{doctor_id}", response_model=List[schemas.AvailabilityResponse])
def get_doctor_availability(doctor_id: int,date: Optional[str] = None,db: Session = Depends(get_db)):
    query = db.query(models.Availability).filter(models.Availability.doctor_id == doctor_id)
    if date:
        query = query.filter(models.Availability.date == date)
    
    availabilities = query.all()
    return availabilities

@app.delete("/availability/{availability_id}")
def delete_availability(availability_id: int,current_user: models.User = Depends(auth.get_doctor),db: Session = Depends(get_db)):
    availability = db.query(models.Availability).filter(
        models.Availability.id == availability_id,
        models.Availability.doctor_id == current_user.id
    ).first()
    
    if not availability:
        raise HTTPException(status_code=404, detail="Availability not found")
    
    db.delete(availability)
    db.commit()
    return {"message": "Availability deleted successfully"}


@app.post("/appointments", response_model=schemas.AppointmentResponse)
def create_appointment(appointment: schemas.AppointmentCreate,current_user: models.User = Depends(auth.get_patient),db: Session = Depends(get_db)): 
    # Verify doctor exists
    doctor = db.query(models.User).filter(
        models.User.id == appointment.doctor_id,
        models.User.role == "doctor"
    ).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Checking for availability of the doctor
    availability = db.query(models.Availability).filter(
        models.Availability.doctor_id == appointment.doctor_id,
        models.Availability.date == appointment.date,
        models.Availability.start_time <= appointment.start_time,
        models.Availability.end_time >= appointment.end_time
    ).first()
    
    if not availability:
        raise HTTPException(status_code=400, detail="Doctor not available")
    
    overlap = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == appointment.doctor_id,
        models.Appointment.date == appointment.date,
        models.Appointment.status != "cancelled",
        models.Appointment.start_time < appointment.end_time,
        models.Appointment.end_time > appointment.start_time
    ).first()
    
    if overlap:
        raise HTTPException(status_code=400, detail="Time slot already booked")
    
    db_appointment = models.Appointment(
        patient_id=current_user.id,
        doctor_id=appointment.doctor_id,
        date=appointment.date,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        status="booked"
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


@app.get("/appointments", response_model=List[schemas.AppointmentResponse])
def get_appointments(current_user: models.User = Depends(auth.get_current_user),db: Session = Depends(get_db),date: Optional[str] = None,status: Optional[str] = None):
    if current_user.role == "patient":
        query = db.query(models.Appointment).filter(models.Appointment.patient_id == current_user.id)
    else:  # doctor
        query = db.query(models.Appointment).filter(models.Appointment.doctor_id == current_user.id)
    
    if date:
        query = query.filter(models.Appointment.date == date)
    if status:
        query = query.filter(models.Appointment.status == status)
    
    appointments = query.all()
    return appointments

@app.get("/appointments/{appointment_id}", response_model=schemas.AppointmentResponse)
def get_appointment(appointment_id: int,current_user: models.User = Depends(auth.get_current_user),db: Session = Depends(get_db)):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first() 
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if current_user.role == "patient" and appointment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "doctor" and appointment.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return appointment


@app.put("/appointments/{appointment_id}/cancel")
def cancel_appointment(appointment_id: int,current_user: models.User = Depends(auth.get_current_user),db: Session = Depends(get_db)):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if current_user.role == "patient" and appointment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "doctor" and appointment.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if appointment.status == "cancelled":
        raise HTTPException(status_code=400, detail="Appointment was already cancelled")
    appointment.status = "cancelled"
    db.commit()
    return {"message": "Appointment cancelled successfully"}

@app.put("/appointments/{appointment_id}/complete")
def complete_appointment(appointment_id: int,current_user: models.User = Depends(auth.get_doctor),db: Session = Depends(get_db)):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id,models.Appointment.doctor_id == current_user.id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot complete cancelled appointment")
    appointment.status = "completed"
    db.commit()
    return {"message": "Appointment completed successfully"}


@app.get("/search/appointments", response_model=List[schemas.AppointmentResponse])
def search_appointments(
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    date: Optional[str] = None,
    status: Optional[str] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Appointment)
    
    if current_user.role == "patient":
        query = query.filter(models.Appointment.patient_id == current_user.id)
    elif current_user.role == "doctor":
        query = query.filter(models.Appointment.doctor_id == current_user.id)
    
    if doctor_id:
        query = query.filter(models.Appointment.doctor_id == doctor_id)
    if patient_id and current_user.role == "doctor": 
        query = query.filter(models.Appointment.patient_id == patient_id)
    if date:
        query = query.filter(models.Appointment.date == date)
    if status:
        query = query.filter(models.Appointment.status == status)
    
    appointments = query.all()
    return appointments


@app.get("/history/patient/{patient_id}", response_model=List[schemas.AppointmentResponse])
def get_patient_history(patient_id: int,current_user: models.User = Depends(auth.get_current_user),db: Session = Depends(get_db)):
    if current_user.role == "patient" and current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    appointments = db.query(models.Appointment).filter(models.Appointment.patient_id == patient_id,models.Appointment.status == "completed").order_by(models.Appointment.date.desc()).all()
    return appointments



