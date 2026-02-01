from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

#Doctors and patients
class User(Base):
    __tablename__="users"

    id=Column(Integer,primary_key=True,index=True)
    full_name=Column(String,nullable=False)
    email=Column(String,unique=True,nullable=False,index=True)
    hashed_password=Column(String,nullable=False)
    role=Column(String,nullable=False)
    specialization=Column(String,nullable=True)
    created_at=Column(DateTime,default=datetime.utcnow)

    patient_appointment=relationship("Appointment",back_populates="patient",foreign_keys="Appointment.patient_id")
    doctor_appointment=relationship("Appointment",back_populates="doctor",foreign_keys="Appointment.doctor_id")
    available=relationship("Availability",back_populates="doctor",cascade="all,delete-orphan")
    #all operations on the parent entity are automatically applied to its related child entities, and that child records are deleted if they lose their parent, maintaining data integrity

class Availability(Base):
    __tablename__="availabilities"

    id=Column(Integer,primary_key=True,index=True)
    doctor_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    date=Column(Date,nullable=False)
    start_time=Column(Time,nullable=False)
    end_time=Column(Time,nullable=False)
    created_at=Column(DateTime,default=datetime.utcnow)

    doctor=relationship("User",back_populates="available")



class Appointment(Base):
    __tablename__="appointments"

    id=Column(Integer,primary_key=True,index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status=Column(String,default="booked")#booked, cancelled, completed
    date=Column(Date,nullable=False)
    start_time=Column(Time,nullable=False)
    end_time=Column(Time,nullable=False)
    created_at=Column(DateTime,default=datetime.utcnow)

    patient=relationship("User",back_populates="patient_appointment",foreign_keys=[patient_id])
    doctor=relationship("User",back_populates="doctor_appointment",foreign_keys=[doctor_id])
    

    




