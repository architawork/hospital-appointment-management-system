from pydantic import EmailStr,BaseModel,Field
from typing import Optional
from datetime import date,time,datetime

class UserBase(BaseModel):
    full_name:str
    email:EmailStr

class UserCreate(UserBase):
    password:str

class DoctorCreate(UserCreate):
    specialization:str

#to not expose the databse to the users like hashed passwords or something
class UserResponse(UserBase):
    id:int
    role:str
    specialization:Optional[str]=None
    created_at:datetime

#basically returns orm objects not a dict
#we can keep track of the changes made in the database
    class Config:
       from_attributes=True



class Token(BaseModel):
    access_token:str
    token_type:str


class TokenData(BaseModel):
    email:Optional[str]=None
    role:Optional[str]=None

class AvailabilityBase(BaseModel):
    date:date
    start_time:time
    end_time:time

class AvailabilityCreate(AvailabilityBase):
    pass

class AvailabilityResponse(AvailabilityBase):
    id:int
    doctor_id:int
    created_at:datetime

    class Config:
        from_attributes=True



class AppointmentBase(BaseModel):
    doctor_id: int
    date: date
    start_time: time
    end_time: time


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentComplete(BaseModel):
    notes: str


class AppointmentResponse(AppointmentBase):
    id: int
    patient_id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True




