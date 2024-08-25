import logging, asyncio, traceback, re
from jose import JWTError, jwt
from jwt import ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, Query, File, Request, Header, Response, status, Body
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc, or_, distinct
from cachetools import TTLCache
from PyPDF2 import PdfReader
import os
from datetime import datetime, timedelta
from pydantic import EmailStr
from typing import Dict
from autojobserve.db import *
from autojobserve.schemas import *
from autojobserve.utils import create_access_token, get_current_user, SECRET_KEY, ALGORITHM
from autojobserve.emails import send_confirmation_email, send_reset_password_email, reset_success_email, send_delete_confirmation_email, send_deactivation_email, send_feedback_email, schedule_deletion_reminder, schedule_delete_confirmation_email, send_email_notification
from autojobserve.models import *
from selenium_scripts.apply_to_link import apply_through_link 
from selenium_scripts.scrape_all import scrape_all
from selenium_scripts.scrape_job import scrape_job 
from selenium_scripts.job_available import check_job 
from autojobserve.usable_functions import *
from . import logger
from selenium_scripts.Glassdoor_Jobs import Glassdoor_scrape_all_jobs
from selenium_scripts.Glassdoor_Jobs import Glassdoor_scrape_jobs
from selenium_scripts.Glassdoor_Jobs import Glassdoor_save_jobs
from selenium_scripts.Glassdoor_Jobs.Glassdoor_scrape_all_jobs import login_glassdoor

# Define a cache with a TTL (time-to-live) of 1 hour
confirmation_email_cache = TTLCache(maxsize=1000, ttl=3600)
from . import models

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

profile = APIRouter()



# View profile endpoint
@profile.get("/api/v1/view_profile", response_model=CombinedProfileResponse)
async def view_profile(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    try:
        logging.debug("Starting view_profile endpoint")

        # Perform token validation
        user_id = await get_current_user(token)
        
        if user_id is None:
            raise HTTPException(status_code=400, detail="Invalid token or user not found")

        logging.debug(f"Extracted user_id: {user_id}")

        # Fetch data from User and UserProfile tables
        user = db.query(Users).filter(Users.id == user_id).first()
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

        if not user or not user_profile:
            raise HTTPException(status_code=404, detail="User not found")

        logging.debug("Data retrieved from database")

        # Map fields to the CombinedProfileResponse model
        combined_profile = CombinedProfileResponse(
            user_id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name, 
            last_name=user.last_name,
            user_location=user.user_location,
            job_title=user.job_title,
            cv=user.cv, 
            bio=user_profile.bio,
            website=user_profile.website,
            phone_number=user_profile.phone_number,
            address=user_profile.address,
            date_of_birth=user_profile.date_of_birth,
            gender=user_profile.gender,
            nationality=user_profile.nationality,
            language=user_profile.language,
            education=user_profile.education,
            work_experience=user_profile.work_experience,
            job_description=user_profile.job_description,
            skills=user_profile.skills,
            position=user_profile.position,
            job_preference=user_profile.job_preference,
            social_media=user_profile.social_media,
            experience_from_year=user_profile.experience_from_year, 
            experience_to_year=user_profile.experience_to_year,
            active=user_profile.active,
            email_notifications=user_profile.email_notifications,
            mobile_messaging=user_profile.mobile_messaging,
        )

        logging.debug("Profile data mapped to response model")
        return combined_profile

    except HTTPException as http_exception:
        logging.error(f"HTTPException occurred: {http_exception}")
        raise http_exception 

    except Exception as e:
        logging.error(f"Exception occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")




# Manual Edit Profile Endpoint with CV
@profile.put("/api/v1/profile/manual_edit")
async def edit_profile(
    token: str,
    cv: Optional[UploadFile] = File(None),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    user_location: Optional[str] = Form(None),
    job_title: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    nationality: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    education: Optional[str] = Form(None),
    job_description: Optional[str] = Form(None),
    skills: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    job_preference: Optional[str] = Form(None),
    social_media: Optional[str] = Form(None),
    experience_from_year: Optional[int] = Form(None),
    experience_to_year: Optional[int] = Form(None),
    email_notifications: Optional[bool] = Form(True),
    mobile_messaging: Optional[bool] = Form(True),
    db: Session = Depends(get_db),
):
    try:
        logging.debug("Starting manual_edit_profile endpoint")

        user_id = await get_current_user(token)

        # Check if 'CV' directory exists, create it if not
        cv_directory = f'CV/{user_id}'
        if not os.path.exists(cv_directory):
            os.makedirs(cv_directory)

        # Fetch the User and UserProfile records to edit
        user = db.query(Users).filter(Users.id == user_id).first()
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

        if not user or not user_profile:
            raise HTTPException(status_code=404, detail="User not found")

        # Save CV file to 'CV' directory
        if cv:
            cv_content = cv.file.read()
            cv_filename = f"CV/{cv.filename}"
            with open(cv_filename, "wb") as cv_file:
                cv_file.write(cv_content)

            # Save CV path to the user
            user.cv = cv_filename
            save_cv_to_db(cv_data={"user_id": user.id, "cv": cv_filename}, db=db)

        # Update User fields with provided or existing values
        user.first_name = first_name if first_name is not None else user.first_name
        user.last_name = last_name if last_name is not None else user.last_name
        user.user_location = user_location if user_location is not None else user.user_location
        user.job_title = job_title if job_title is not None else user.job_title

        # Update UserProfile fields with provided or existing values
        user_profile.bio = bio if bio is not None else user_profile.bio
        user_profile.website = website if website is not None else user_profile.website
        user_profile.phone_number = phone_number if phone_number is not None else user_profile.phone_number
        user_profile.address = address if address is not None else user_profile.address
        user_profile.date_of_birth = date_of_birth if date_of_birth is not None else user_profile.date_of_birth
        user_profile.gender = gender if gender is not None else user_profile.gender
        user_profile.nationality = nationality if nationality is not None else user_profile.nationality
        user_profile.language = language if language is not None else user_profile.language
        user_profile.education = education if education is not None else user_profile.education
        user_profile.job_description = job_description if job_description is not None else user_profile.job_description
        user_profile.skills = skills if skills is not None else user_profile.skills
        user_profile.position = position if position is not None else user_profile.position
        user_profile.job_preference = job_preference if job_preference is not None else user_profile.job_preference
        user_profile.social_media = social_media if social_media is not None else user_profile.social_media
        user_profile.experience_from_year = experience_from_year if experience_from_year is not None else user_profile.experience_from_year
        user_profile.experience_to_year = experience_to_year if experience_to_year is not None else user_profile.experience_to_year
        user_profile.email_notifications = email_notifications
        user_profile.mobile_messaging = mobile_messaging

        # Update records in separate user_location and job_title tables.
        if user_location:
            save_location_db(user_location_data={"user_id": user.id, "user_location": user_location}, db=db)

        if job_title:
            save_job_title_to_db(job_title_data={"user_id": user.id, "job_title": job_title}, db=db)

        db.commit()

        # Update the user notifications table
        add_notification(db, user_id, "Profile successfully updated manually")

        # Return updated combined profile
        updated_combined_profile = CombinedProfileResponse(
            user_id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            user_location=user.user_location,
            job_title=user.job_title,
            cv=user.cv,
            bio=user_profile.bio,
            website=user_profile.website,
            phone_number=user_profile.phone_number,
            address=user_profile.address,
            date_of_birth=user_profile.date_of_birth,
            gender=user_profile.gender,
            nationality=user_profile.nationality,
            language=user_profile.language,
            education=user_profile.education,
            job_description=user_profile.job_description,
            skills=user_profile.skills,
            position=user_profile.position,
            job_preference=user_profile.job_preference,
            social_media=user_profile.social_media,
            experience_from_year=user_profile.experience_from_year,
            experience_to_year=user_profile.experience_to_year,
            email_notifications=user_profile.email_notifications,
            mobile_messaging=user_profile.mobile_messaging,
        )

        logging.debug("Profile updated successfully manually")

        logging.debug("Returning response: %s", updated_combined_profile)

        return EditProfileResponse(
            message="Profile successfully updated manually",
            profile=updated_combined_profile
        )

    except SQLAlchemyError as e:
        logging.error("Database error: %s", str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    except Exception as e:
        logging.error("Internal server error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



#extract info from cv for profile edit
@profile.put("/api/v1/profile/cv_extraction")
async def cv_extraction(
    token: str,
    cv: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    try:
        logging.debug("Starting auto_edit_profile_with_cv endpoint")

        user_id = await get_current_user(token)

        # Check if 'CV' directory exists, create it if not
        cv_directory = f'CV/{user_id}'
        if not os.path.exists(cv_directory):
            os.makedirs(cv_directory)

        # Fetch the User and UserProfile records to edit
        user = db.query(Users).filter(Users.id == user_id).first()
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

        if not user or not user_profile:
            raise HTTPException(status_code=404, detail="User not found")

        if cv:
            # Check if the uploaded file is a PDF
            if cv.content_type != 'application/pdf':
                raise HTTPException(status_code=400, detail="Only PDF files are allowed for CV")

            cv_content = cv.file.read()

            # Extract text from the PDF CV using PyPDF2
            pdf_text = ""
            with io.BytesIO(cv_content) as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                for page_num in range(len(pdf_reader.pages)):
                    pdf_text += pdf_reader.pages[page_num].extract_text()

                    

            # Extract relevant information from the PDF text
            extracted_info = extract_info_from_cv(pdf_text)

            # Update specific key words in user_profile
            user_profile.education = extracted_info.get("education", user_profile.education)
            user_profile.skills = extracted_info.get("skills", user_profile.skills)
            user_profile.address = extracted_info.get("address", user_profile.address)
            user_profile.work_experience = extracted_info.get("work experience", user_profile.work_experience)
           

            # Return the extracted information as a response
            return extracted_info

        else:
            raise HTTPException(status_code=400, detail="CV file is required for automatic edit")

    except SQLAlchemyError as e:
        logging.error("Database error: %s", str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    except Exception as e:
        logging.error("Internal server error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")