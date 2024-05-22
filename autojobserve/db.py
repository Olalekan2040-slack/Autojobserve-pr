from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from autojobserve.schemas import * 
from fastapi import HTTPException
# import psycopg2



# DATABASE_URL = "mysql+pymysql://root:admin@mysql:3306/autojob"
DATABASE_URL = "mysql://avnadmin:AVNS_K2mgJXx4KdSbaISmPd9@autojobserve-sharafdeenolaleken-f53d.a.aivencloud.com:12273/defaultdb"

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
