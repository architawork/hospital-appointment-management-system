from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL="sqlite:///./hospital.db"

#we set it as false so that multiple threads can access with supervision
engine=create_engine(DATABASE_URL,connect_args={"check_same_thread": False})

SessionLocal=sessionmaker(autocommit=False, autoflush=False,bind=engine)

Base=declarative_base()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close() 
