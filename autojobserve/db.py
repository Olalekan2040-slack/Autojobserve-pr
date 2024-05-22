from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from autojobserve.schemas import * 
from fastapi import HTTPException
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Construct the database URL
DATABASE_URL = f"mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


# DATABASE_URL = "mysql+pymysql://root:admin@mysql:3306/autojob"
# DATABASE_URL = "mysql://avnadmin:AVNS_K2mgJXx4KdSbaISmPd9@autojobserve-sharafdeenolaleken-f53d.a.aivencloud.com:12273/defaultdb"

Base = declarative_base()


try:
    # Create a database engine
    engine = create_engine(DATABASE_URL)


    # Create a session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

except SQLAlchemyError as e:
    # Handle exceptions, log the error, and potentially raise an HTTPException
    error_message = f"Error connecting to the database: {str(e)}"
    print(error_message)
    raise HTTPException(status_code=500, detail=error_message)
