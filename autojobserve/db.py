from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from autojobserve.schemas import * 
from fastapi import HTTPException
from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv()

# Retrieve the variables
database_url = os.getenv("DATABASE_URL")




# DATABASE_URL = "mysql+pymysql://root:admin@mysql:3306/autojob"

                
Base = declarative_base()

if not database_url:
    raise ValueError("DATABASE_URL is not set. Please check your .env file or environment variables.")


try:
    # Create a database engine
    engine = create_engine(database_url)


    # Create a session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

except SQLAlchemyError as e:
    # Handle exceptions, log the error, and potentially raise an HTTPException
    error_message = f"Error connecting to the database: {str(e)}"
    print(error_message)
    raise HTTPException(status_code=500, detail=error_message)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
