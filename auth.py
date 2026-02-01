from fastapi import FastAPI,HTTPException,status,Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db
from typing import Optional
from datetime import datetime,timedelta

SECRET_KEY="79a2e24a62ec4a340e9897012eb4d004c3d55128769111c2be8709fb2f0339eb" 
ALGORITHM="HS256" 
ACCESS_TOKEN_EXPIRE_MINUTES=30

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
OAuth2_scheme=OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password:str,hashed_password:str)->bool:
    return pwd_context.verify(plain_password,hashed_password)

def get_password_hash(password:str)->str:
    return pwd_context.hash(password)

def authenticate_user(db:Session,email:str,password:str):
    user=db.query(models.User).filter(models.User.email==email).first()
    if not user:
        return False
    if not verify_password(password,user.hashed_password):
        return False
    else:
        return user
    
def create_access_token(data:dict,expires_delta:Optional[timedelta]=None):
    to_encode=data.copy()
    if expires_delta:
        expire=datetime.utcnow()+expires_delta
    else:
        expire=datetime.utcnow()+timedelta(minutes=15)
    to_encode.update({"exp":expire})
    encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(OAuth2_scheme), db: Session = Depends(get_db)):
    credentials_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="could not validate",
        headers={"WWW-Authenticate":"Bearer"}
    )
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        email:str=payload.get("sub")
        if email is None:
           raise credentials_exception
        token_data=schemas.TokenData(email=email,role=payload.get("role"))
    except JWTError:
        raise credentials_exception
    
    user=db.query(models.User).filter(models.User.email==token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_patient(current_user:models.User=Depends(get_current_user)):
    if current_user.role!="patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="only patients allowed"
        )
    return current_user

async def get_doctor(current_user:models.User=Depends(get_current_user)):
    if current_user.role!="doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="only doctors allowed"
        )
    return current_user

