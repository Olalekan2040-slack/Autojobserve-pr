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

user = APIRouter()

@user.get('/')
def main():
    return {'message': 'Welcome to AutoJobServe'}


# Registration endpoint
@user.post("/api/v1/register")
async def register_user(
    email: EmailStr = Form(...),
    username: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    user_password: str = Form(...),
    job_title: str = Form(""),
    user_location: str = Form(""), 
    cv: UploadFile = File(None), 
    db: Session = Depends(get_db),
    request: Request = None,  
):
    try:
        user_info = capture_user_info(request)

        if user_info:
            # Save user information to CSV
            save_to_csv(['Registration', user_info.get('operating_system'), user_info.get('client_ip')])

        # Check if the email already exists in the database
        existing_user = get_user_by_email(email, db)
        if existing_user:
            raise HTTPException(status_code=409, detail="Email already exists.")

        # Check if the user profile is deleted
        if existing_user:
            user_profile = db.query(UserProfile).filter(UserProfile.user_id == existing_user.id).first()
            if user_profile and user_profile.deleted:
                raise HTTPException(status_code=403, detail="Your account has been deleted. Please contact support for assistance with account reactivation.")

        # Check if the username already exists in the database
        existing_username = get_user_by_username(username, db)
        if existing_username:
            raise HTTPException(status_code=409, detail="Username already exists.")

        # Hash the user's password using bcrypt
        hashed_password = password_context.hash(user_password)

        # Create the user
        user_data = UserSchema(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            user_password=hashed_password,
            job_title=job_title,
            user_location=user_location,
            cv=cv.filename if cv else None
        )
        new_user = create_user(user_data.dict(), db)

        # Create the user profile
        user_profile_data = UserProfileSchema(
            user_id=new_user.id,
            job_title=job_title,
            user_location=user_location,
            cv=cv.filename if cv else None
        )
        create_user_profile(user_profile_data.dict(), db)

        # Save password
        save_password_to_db({"user_id": new_user.id, "user_password": hashed_password}, db)

        if job_title:
            # Save job title
            save_job_title_to_db({"user_id": new_user.id, "job_title": job_title}, db)

        if user_location:
            # Save user location
            save_location_db({"user_id": new_user.id, "user_location": user_location}, db)

        # Handle CV Upload
        file_path = None
        if cv:
            cv_data = await cv.read()
            cv_filename = f"CV/{cv.filename}"

            with open(cv_filename, "wb") as cv_file:
                cv_file.write(cv_data)

            file_path = cv_filename

            # Save CV
            save_cv_to_db({"user_id": new_user.id, "cv": file_path}, db)

        # Create jwt token
        user_info = {
            "user_id": new_user.id,
            "email": email,
        }
        jwt_token = await create_access_token(user_info)

        # Send a confirmation email
        if email and new_user.id:
            logging.debug("Before sending confirmation email")
            await send_confirmation_email(email, first_name, jwt_token, 'utc')
            logging.debug("After sending confirmation email")

        # Return response
        return {
            "message": "Registration successful! Please check your email to confirm your account.",
            "data": user_info,
            "token": jwt_token,
        }

    except Exception as e:
        raise e


# confirm email endpoint 
@user.post('/api/v1/confirm-email/{user_id}')
async def confirm_email(user_id: int, jwt_token: str = Form(...), db: Session = Depends(get_db)):
    try:
        current_user_id = await get_current_user(jwt_token)

        # Verify user_id from the token
        if current_user_id != user_id:
            return {"error": "Invalid user ID."}

        # Update the user's email verification status in the database
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if user_profile:

            # Check if the email has already been verified
            if user_profile.email_verified:
                return JSONResponse(content={"message": "Email already verified."}, status_code=200)

            user_profile.email_verified = True
            user_profile.active = True
            try:
                db.commit()

                # Call add_notification function after successful email verification
                message = "Your email has been successfully verified. Welcome to our platform!"
                add_notification(db, user_id, message)

                return {"message": "VERIFICATION SUCCESSFUL"}
            except IntegrityError:
                db.rollback()
                return {"error": "Email Verification Failed."}

        return {"error": "User not found."}

    except ExpiredSignatureError:
        return {"error": "Token has expired."}
    except Exception as e:
        # Log the exception for debugging purposes
        logging.exception("Error occurred during email verification:")
        return {"error": "Email could not be verified. Please contact support."}


# Dictionary to store login attempts with timestamp
login_attempts = {}
max_login_attempts = 5
ban_duration_minutes = 15

@user.post("/api/v1/login")
async def login_user(
    email: str = Form(...),
    user_password: str = Form(...),
    db: Session = Depends(get_db),
    request: Request = None,  
):
    try:
        user_info = capture_user_info(request)

        # Log user information for debugging
        if user_info:
            logging.info(f"User information: {user_info}")
            # Save user information to CSV
            save_to_csv(['Login', user_info.get('operating_system'), user_info.get('client_ip')])

        # Check if the user has exceeded the maximum login attempts
        if email in login_attempts and login_attempts[email]['attempts'] >= max_login_attempts:
            ban_end_time = login_attempts[email]['timestamp'] + timedelta(minutes=ban_duration_minutes)
            if datetime.utcnow() < ban_end_time:
                remaining_time = int((ban_end_time - datetime.utcnow()).total_seconds() // 60)
                raise HTTPException(status_code=401, detail=f"You are banned for {remaining_time} minute(s). Please try again later.")

            # Reset the login attempts when ban period elapses
            del login_attempts[email]

        # Get the user from the database
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Check if the user's email is verified
        user_profile_verification = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if user_profile_verification and not user_profile_verification.email_verified:
            # Check if a confirmation email was sent within the last hour
            confirmation_email_sent_time = confirmation_email_cache.get(user.email)
            if confirmation_email_sent_time and datetime.utcnow() - confirmation_email_sent_time < timedelta(hours=1):
                # Notify the user to click the existing confirmation link
                raise HTTPException(status_code=401, detail="Email not verified. Please click the existing confirmation link sent to your email.")

            # Create jwt token for confirmation email
            confirmation_user_info = {
                "user_id": user.id,
                "email": user.email,
            }
            confirmation_jwt_token = await create_access_token(confirmation_user_info)

            # Log confirmation email information for debugging
            logging.info(f"Confirmation email sent to {user.email} with token: {confirmation_jwt_token}")

            # Update the confirmation email sent time in the cache
            confirmation_email_cache[user.email] = datetime.utcnow()

            # Call the send_confirmation_email function
            await send_confirmation_email(email=email, first_name=user.first_name, jwt_token=confirmation_jwt_token, user_timezone='utc')
            
            raise HTTPException(status_code=401, detail="Email not verified. Confirmation email resent. Please verify your email before logging in.")         

        # Verify the provided password against the hashed password stored in the database
        if not password_context.verify(user_password, user.user_password):
            # Increment login attempts counter and timestamp for the user
            if email not in login_attempts:
                login_attempts[email] = {'attempts': 1, 'timestamp': datetime.utcnow()}
            else:
                login_attempts[email]['attempts'] += 1

            # When a user reaches maximum login attempts
            if login_attempts[email]['attempts'] >= max_login_attempts:
                login_attempts[email]['timestamp'] = datetime.utcnow()

            remaining_attempts = max_login_attempts - login_attempts[email]['attempts']
            if remaining_attempts > 0:
                raise HTTPException(status_code=401, detail=f"Incorrect email or password. {remaining_attempts} attempt(s) remaining.")
            else:
                raise HTTPException(status_code=401, detail="You have reached the maximum login attempts. Please try again later.")

        # Reset the login attempts counter if the login is successful
        if email in login_attempts:
            del login_attempts[email]

        # Check if the user profile is deleted
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if user_profile and user_profile.deleted:
            raise HTTPException(status_code=403, detail="Profile is deleted. Cannot log in.")

        # Create jwt token
        user_info = {
            "user_id": user.id,
            "email": user.email,
        }
        jwt_token = await create_access_token(user_info)

        # Log successful login information for debugging
        logging.info(f"User {user.email} logged in successfully. Token: {jwt_token}")

        # Return response
        return {
            "message": "Login successful!",
            "user_id": user.id,
            "token": jwt_token,
        }

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired. Please log in again.")
    except HTTPException as e:
        logging.error(f"HTTPException occurred: {e.detail}")
        raise e
    except Exception as e:
        logging.exception(f"Error occurred during login: {e}")
        raise HTTPException(status_code=500, detail="Failed to log in. Please try again later.")



# Password Reset Endpoint
@user.post('/api/v1/reset')
async def reset_password(
    request: ResetPassword,
    db: Session = Depends(get_db),
    http_request: Request = None,
):
    try:
        email = request.email

        user_info = capture_user_info(http_request)

        if user_info:
            # Save user information to CSV
            save_to_csv(['Login', user_info.get('operating_system'), user_info.get('client_ip')])

        # Check if the user exists
        user = get_user_by_email(email, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if the user profile is deleted
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if user_profile and user_profile.deleted:
            raise HTTPException(status_code=403, detail="Unauthorized operation, please contact support.")

        # Generate a password reset token
        user_info = {
            "user_id": user.id,
            "email": user.email,
        }
        reset_token = await create_access_token(user_info)

        # Send password reset email link to user
        await send_reset_password_email(email, user.username, reset_token, 'utc')

        # If email sending is successful, return success message
        return {"message": "Password reset email sent successfully."}

    except HTTPException as http_err:
        raise http_err
    except Exception as err:
        # Log the error and raise an HTTP exception
        logging.error(f"An error occurred: {str(err)}")
        raise HTTPException(status_code=500, detail="Failed to send password reset email")

@user.post("/api/v1/reset_password")
async def reset_password_page(request: ResetPasswordPageRequest, db: Session = Depends(get_db)):
    try:
        # Verify the provided reset token
        token = request.reset_token

        try:
            # Decode the token to get the user information
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = decoded_token.get("user_id")
            email = decoded_token.get("email")

            # Check if the user exists in the database
            user = get_user_by_email(email, db)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Check if the new password matches the confirm password
            if request.new_password != request.confirm_password:
                raise HTTPException(status_code=400, detail="New password and confirm password do not match.")

            # Hash the new password
            user_password = password_context.hash(request.new_password)

            # Update the user's password in the database
            # save_password_to_db({"user_id": user_id, "user_password": user_password}, db) 
            update_password_in_db(email, user_id, user_password, db)           

            # send email notifications to user's email address
            await reset_success_email(email)

            # Add a notification to the database
            notification_message = "Your password was successfully reset."
            add_notification(db, user_id, notification_message)

            return {"message": "Password reset successful."}

        except ExpiredSignatureError:
            raise HTTPException(status_code=400, detail="Reset token has expired.")
        except Exception as err:
            raise HTTPException(status_code=400, detail=f"Invalid reset token. {err}")

    except HTTPException as http_err:
        raise http_err
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


# View profile endpoint
@user.get("/api/v1/view_profile", response_model=CombinedProfileResponse)
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
@user.put("/api/v1/profile/manual_edit")
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
@user.put("/api/v1/profile/cv_extraction")
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



# Activate Endpoint
@user.post("/api/v1/activate", response_model=ActivateProfileResponse)
async def activate_profile(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        data = await request.json()

        token = data.get("token")
        user_id = await get_current_user(token)

        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not user_profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Activate User fields
        user_profile.deactivated_at = None
        user_profile.active = True
        user_profile.hidden = False
        user_profile.deactivation_date = None
        user_profile.restricted = False

        # Add notification for successful activation
        activation_message = "Your account has been successfully activated. Welcome!"
        add_notification(db, user_id, activation_message)

        db.commit()

        response_data = {
            "message": "Profile successfully activated",
            "deactivated_at": user_profile.deactivated_at,
            "active": user_profile.active,
            "hidden": user_profile.hidden,
            "deactivation_date": user_profile.deactivation_date,
            "restricted": user_profile.restricted
        }

        return ActivateProfileResponse(**response_data)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        return JSONResponse(content={"detail": "Internal server error"}, status_code=500)


# Deactivate Endpoint
@user.post("/api/v1/deactivate", response_model=DeactivateProfileResponse)
async def deactivate_profile(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        data = await request.json() 

        logger.info("Received JSON data: %s", data)

        token = data.get("token") 
        user_id = await get_current_user(token) 

        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not user_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Deactivate User fields
        user_profile.deactivated_at = datetime.utcnow()
        user_profile.active = False
        user_profile.hidden = True
        user_profile.deactivation_date = datetime.now() 
        user_profile.restricted = True

        db.commit()

        # Calculate deletion date
        deletion_date = user_profile.deactivation_date + timedelta(days=30)

        # Calculate the reminder date (3 days before deletion)
        reminder_date = deletion_date - timedelta(days=3)        

        # Schedule the deletion reminder email
        #await schedule_deletion_reminder(user.email, user.first_name, reminder_date)

        # Set the user_profile.deleted attribute to True after the 30-day period
        if datetime.utcnow() >= deletion_date:
            user_profile.deleted = True              


        # Convert datetime values to strings
        deactivated_at_str = user_profile.deactivated_at.strftime('%Y-%m-%d %H:%M:%S')
        deactivation_date_str = user_profile.deactivation_date.strftime('%Y-%m-%d %H:%M:%S')

         
        # Send deactivation email 
        await send_deactivation_email(email = user.email, first_name = user.first_name, deactivation_date=deletion_date)

        # Schedule the deletion confirmation email
        await schedule_delete_confirmation_email(user.email, user.first_name, deletion_date)        

        response = DeactivateProfileResponse(
            message="Your account has been successfully deactivated. Your account is now restricted. You will no longer receive any notifications, emails, or communications. To reactivate your account, please log in and click on 'ACTIVATE ACCOUNT' within 30 days.",
            deactivated_at=deactivated_at_str,
            active=user_profile.active,
            hidden=user_profile.hidden,
            deactivation_date=deactivation_date_str,
            restricted=user_profile.restricted
        )


        logger.info("Deactivated profile for user ID %s", user_id)

        return response
    
    except SQLAlchemyError as e:
        logger.error("Database error: %s", e)
        db.rollback()
        return JSONResponse(content={"detail": "Database error"}, status_code=500)
    except Exception as e:
        logger.error("Internal server error: %s", e) 
        return JSONResponse(content={"detail": "Internal server error"}, status_code=500)


@user.delete("/api/v1/delete", response_model=DeleteProfileResponse)
async def delete_profile(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Header(None)
):
    try:
        # Use the 'token' variable directly from the headers
        user_id = await get_current_user(token)

        # Fetch the user record
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch the user profile record
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not user_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Set the deleted flag in user profile
        user_profile.deleted = True

        # Commit changes
        db.commit()

        # Send the email confirmation
        await send_delete_confirmation_email(email=user.email, first_name=user.first_name)

        response = DeleteProfileResponse(message="Profile successfully deleted")

        logger.info("Deleted profile and user record for user ID %s", user_id)

        return response

    except SQLAlchemyError as e:
        logger.error("Database error: %s", e)
        db.rollback()
        return JSONResponse(content={"detail": "Database error"}, status_code=500)
    except Exception as e:
        logger.error("Internal server error: %s", e)
        return JSONResponse(content={"detail": "Internal server error"}, status_code=500)


@user.post("/api/v1/feedback-contact")
async def create_feedback_contact(
    item: FeedbackContactCreate,
    db: Session = Depends(get_db)
):
    try:
        # Create the feedback contact data
        feedback_contact_data = FeedbackContactCreate(
            name=item.name,
            email=item.email,
            subject=item.subject,
            message=item.message,
        )
        
        # Create the feedback contact and return it
        new_feedback_contact = await create_feedback_contact_record(feedback_contact_data, db)

        # Send an email to admin
        await send_feedback_email(item.name, item.email, item.subject, item.message)
        
        return new_feedback_contact
    
    except HTTPException as e:
        # Log the error
        logger.error(f"HTTPException occurred: {e.status_code} - {e.detail}")
        raise e
    
    except Exception as ex:
        # Log other exceptions
        logger.exception("An unexpected error occurred")
        raise HTTPException(status_code=500, detail="Internal Server Error") 


# @user.post('/api/v1/Glassdoorscrapejobs')
# def Glassdoor_scrape_jobs(job_title: str, db:Session=Depends(get_db)):
#     job_count = login_glassdoor(job_title, db)
#     return str(job_count) + " jobs has been scraped for you" 

# @user.post('/api/v1/Glassdoorscrapealljobs')
# def Glassdoor_scrape_all_jobs(jobtitle: str, db:Session=Depends(get_db)):
#     job_count = login_glassdoor(jobtitle, db)
#     return str(job_count) + " jobs has been scraped for you" 



# @user.post('/api/v1/scrape_jobs/{website}/{scrape_folder}')
# def scrape_jobs(website: str, scrape_folder: str, job_title: Optional[str]=None, location: Optional[str]=None, db: Session = Depends(get_db)):
#     job_count = None
#     if website.lower() == "glassdoor":
#         if scrape_folder.lower() == "glassdoor_scrape_all_jobs":
#             job_count = login_glassdoor(db,job_title,location)
#         elif scrape_folder.lower() == "glassdoor_scrape_jobs":
#             job_count = login_glassdoor(db,job_title,location)
#     elif website.lower() == "vanhack":
#         if scrape_folder.lower() == "scrape_all":
#             job_count = scrape_all(db)
#         elif scrape_folder.lower() == "scrape_jobs":
#             job_count = scrape_jobs(job_title, db)
#     elif website.lower() == "linkedin":
#         if scrape_folder.lower() == "scrape_jobs_linkedin":
#             job_count = scrape_jobs_linkedin(job_title, db)
#         elif scrape_folder.lower() == "scrape_all_jobs":
#             job_count = scrape_jobs_linkedin(job_title, db)
#     elif website.lower() == "jobserve":
#         if scrape_folder.lower() == "scrape_job":
#             job_count = scrape_job(db,job_title,location)
#         elif scrape_folder.lower() == "scrape_all":
#             job_count = scrape_all(db)
#     else:
#         raise HTTPException(status_code=400, detail="Unsupported website")
#     if job_count is None:
#         raise HTTPException(status_code=400, detail="Job count not available")
#     return {"jobs": job_count, "message": f"{job_count} jobs have been scraped for you"}


@user.post('/api/v1/scrapejobs')
def scrape_jobs(jobtitle: str, db:Session=Depends(get_db)):
    no_jobs = scrape_job(jobtitle, db)
    return str(no_jobs) + " jobs has been scraped for you" 
 

@user.get("/api/v1/get_jobs")
def get_jobs(
    job_description: str = Query(None, description="Filter jobs by job description"),
    company_name: str = Query(None, description="Filter jobs by company name"),
    job_location: str = Query(None, description="Filter jobs by job location"),
    job_type: str = Query(None, description="Filter jobs by job type"),
    job_salary: str = Query(None, description="Filter jobs by job salary"),
):
    db = SessionLocal()

    # Define a base query for AllJobs
    base_query = db.query(models.AllJobs)

    # Apply filters based on provided criteria using OR condition
    if any([job_description, company_name, job_location, job_type, job_salary]):
        base_query = base_query.filter(
            or_(
                models.AllJobs.job_title.contains(job_description) if job_description else False,
                models.AllJobs.company_name.contains(company_name) if company_name else False,
                models.AllJobs.job_location.contains(job_location) if job_location else False,
                models.AllJobs.job_type.contains(job_type) if job_type else False,
                models.AllJobs.job_salary.contains(job_salary) if job_salary else False,
            )
        )

    # Execute the query
    jobs = base_query.all()

    # Check if jobs were found or raise an exception
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found matching the provided criteria")

    # Create a list of dictionaries without the 'auto_apply' key
    jobs_without_auto_apply = [
        {k: v for k, v in job.__dict__.items() if k != 'auto_apply'} for job in jobs
    ]

    return jobs_without_auto_apply






@user.post("/api/v1/apply_for_job")
async def apply_for_job(
    request_data: ApplyForJobRequest = Body(...),
    db: Session = Depends(get_db)
):
    try:
        user_id = await get_current_user(request_data.token)

        job = db.query(AllJobs).filter(AllJobs.job_id == request_data.job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        applied_job = db.query(AppliedJobs).filter(
            AppliedJobs.user_id == user_id,
            AppliedJobs.job_id == request_data.job_id
        ).first()

        if applied_job:
            return {"message": "You have already applied for this job", "applied_job_id": applied_job.id}
        
        try:
            if request_data.action == 'apply':
                # Create a new record in AppliedJobs
                new_applied_job = AppliedJobs(
                    user_id=user_id,
                    job_id=request_data.job_id,
                    link_to_applied_jobs=request_data.link_to_applied_jobs or ""
                )
                db.add(new_applied_job)
                db.commit()

                # Update the job's auto_apply status
                job.auto_apply = True
                db.commit()

                # Retrieve user information for email notification
                user = db.query(Users).filter(Users.id == user_id).first()
                user_email = user.email if user else None
                if user_email:
                    job_title = job.job_title
                    await send_email_notification(user_email, job_title)
                    notification_message = f"You have successfully applied for the job: {job_title}"
                    add_notification(db, user_id, notification_message)

                return {"message": "Job application successful", "applied_job_id": new_applied_job.id}
                
            elif request_data.action == 'goto_link':
                db.commit()
                return RedirectResponse(url=job.job_permalink, status_code=status.HTTP_302_FOUND)
                
            else:
                raise HTTPException(status_code=400, detail="Invalid action. Use 'apply' or 'goto_link'")

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


    

# History of applied-jobs endpoint
@user.get("/api/v1/applied_jobs")
async def get_applied_jobs(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    try:
        user_id = await get_current_user(token)

        # retrieve the user's applied job history from AppliedJobs table
        applied_jobs = db.query(AppliedJobs).filter(AppliedJobs.user_id == user_id).all()

        if not applied_jobs:
            return {"message": "You haven't applied for any jobs yet."}

        # Create a list to store the applied job details
        applied_job_list = []

        for applied_job in applied_jobs:
            # Query the AllJobs table to get details about the applied job
            job = db.query(AllJobs).filter(AllJobs.job_id == applied_job.job_id).first()

            if job:
                applied_job_details = {
                    "job_title": job.job_title,
                    "job_salary": job.job_salary,
                    "job_location": job.job_location,
                    "job_description": job.job_description,
                    "job_requirements": job.job_requirements,
                    "applied_at": applied_job.created_at
                }
                applied_job_list.append(applied_job_details)

        if not applied_job_list:
            return {"message": "You haven't applied for any jobs yet."}
        else:
            return applied_job_list
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") 
    



#Get matched jobs
@user.get("/api/v1/matched_jobs")
async def get_matched_jobs(
    token=Query(...),
    db: Session = Depends(get_db)
):
    try:
        user_id = await get_current_user(token)

        if user_id is None:
            raise HTTPException(status_code=400, detail="Invalid token or user not found")

        # Fetch data from User and UserProfile tables
        user = db.query(Users).filter(Users.id == user_id).first()
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

        if not user or not user_profile:
            raise HTTPException(status_code=404, detail="User not found")

        matched_jobs = match_jobs_to_user_profile(user_profile, db)

        if not matched_jobs:
            return {"message": "No jobs matched your profile."}
        else:
            # Get saved jobs for the user
            saved_jobs = db.query(SavedJob).filter(
                SavedJob.user_id == user_id,
                SavedJob.job_id.in_([job['job_id'] for job in matched_jobs])
            ).all()

            # Create a set of job_ids for quick lookup
            saved_job_ids = set([saved_job.job_id for saved_job in saved_jobs])

            # Update each matched job to include is_saved_job field
            for job in matched_jobs:
                job['is_saved_job'] = job['job_id'] in saved_job_ids

            # Add a notification that jobs were matched
            add_notification(db, user_id, "Jobs have been matched to your profile.")
            return matched_jobs

    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")



    
@user.get("/api/v1/recent_job_match")
async def get_recent_job_match(
        token=Query(...), 
        db: Session = Depends(get_db)
):
    try:
        user_id = await get_current_user(token)

        if user_id is None:
            raise HTTPException(status_code=400, detail="Invalid token or user not found")

        # Fetch the most recent matched job for the user
        recent_job_match = get_recent_job_matches_for_user(user_id, db)

        if not recent_job_match:
            return {"message": "No recent job match found for the user."}
        else:
            # Add a notification that a recent job match was retrieved
            add_notification(db, user_id, "Recent job match information retrieved.")

            return recent_job_match

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")



@user.post("/api/v1/saved_jobs", response_model=SavedJobResponse)
def save_job(saved_job: SaveJobRequest, db: Session = Depends(get_db)):
    try:
        # Check if the job is already saved by the user
        existing_saved_job = db.query(SavedJob).filter(
            SavedJob.job_id == saved_job.job_id,
            SavedJob.user_id == saved_job.user_id
        ).first()

        if existing_saved_job:
            db.close()
            raise HTTPException(status_code=400, detail="Job is already saved by the user")

        # The job is not saved, proceed to save it
        job = db.query(AllJobs).filter(AllJobs.job_id == saved_job.job_id).first()

        if job is None:
            db.close()
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if the user has already applied for the job
        applied_job = db.query(AppliedJobs).filter(
            AppliedJobs.user_id == saved_job.user_id,
            AppliedJobs.job_id == saved_job.job_id
        ).first()

        # Set auto_apply flag to False if the user has not applied for the job
        auto_apply_flag = False if not applied_job else job.auto_apply

        # Create a new saved job entry in the database
        saved_job_db = SavedJob(
            job_id=job.job_id,
            user_id=saved_job.user_id,
            saved_job_title=job.job_title if job.job_title else "Job Title not available",
            saved_job_salary=job.job_salary if job.job_salary else "Salary not available",
            saved_job_skill=job.job_skill if job.job_skill else "Skills not specified",
            saved_job_location=job.job_location if job.job_location else "Location not specified",
            saved_job_auto_apply=auto_apply_flag,  # Use the determined auto_apply flag
            saved_job_permalink=job.job_permalink if job.job_permalink else "Permalink not available",
            saved_job_description=job.job_description if job.job_description else "Description not available",
            saved_job_requirements=job.job_requirements if job.job_requirements else "Requirements not specified",
            saved_company_name=job.company_name if job.company_name else "Company Name not available"
        )

        # Update the is_saved_job attribute for the job to True only for the current user
        job.is_saved_job = True
        db.add(saved_job_db)
        db.commit()
        db.refresh(saved_job_db)

        # Create a SavedJobResponse
        saved_job_response = SavedJobResponse(
            id=saved_job_db.id,
            job_id=saved_job_db.job_id,
            user_id=saved_job_db.user_id,
            saved_job_title=saved_job_db.saved_job_title,
            saved_job_salary=saved_job_db.saved_job_salary,
            saved_job_skill=saved_job_db.saved_job_skill,
            saved_job_location=saved_job_db.saved_job_location,
            saved_job_auto_apply=saved_job_db.saved_job_auto_apply,
            saved_job_permalink=saved_job_db.saved_job_permalink,
            saved_job_description=saved_job_db.saved_job_description,
            saved_job_requirements=saved_job_db.saved_job_requirements,
            saved_company_name=saved_job_db.saved_company_name
        )

        # notification for the user
        notification_message = f"You have successfully saved the job: {saved_job_db.saved_job_title}"
        add_notification(db, user_id=saved_job.user_id, message=notification_message)

        # Add logging statements
        logging.info(f"Job saved successfully: {saved_job_db.job_id} by user {saved_job_db.user_id}")

        return saved_job_response
    except HTTPException as http_exception:
        # Add logging statements
        logging.error(f"HTTPException: {http_exception}")
        raise http_exception
    except Exception as e:
        # Add logging statements
        logging.error(f"An error occurred while saving the job: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while saving the job.")

@user.get("/api/v1/notifications")
async def get_user_notifications(
        token=Query(...),
        db: Session = Depends(get_db)
):
    try:
        user_id = await get_current_user(token)

        if user_id is None:
            raise HTTPException(status_code=400, detail="Invalid token or user not found")

        # Retrieve user's notifications in descending order by timestamp
        notifications = db.query(Notification).filter(Notification.user_id == user_id).order_by(desc(Notification.created_at)).all()

        return notifications

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") 
    

@user.put("/api/v1/mark_notification_as_read")
async def mark_notification_as_read(
    notification_id: int = Query(..., description="The ID of the notification to mark as read"),
    token: str = Query(..., description="User authentication token"),
    db: Session = Depends(get_db),
):
    try:
        user_id = await get_current_user(token)

        if user_id is None:
            raise HTTPException(status_code=400, detail="Invalid token or user not found")

        # Retrieve the notification 
        notification = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()

        if notification is None:
            raise HTTPException(status_code=404, detail="Notification not found")

        # Mark the notification as read
        notification.is_read = True
        db.commit()

        return {"message": "Notification marked as read"}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")    


# Delete_Notifications_Endpoint        
@user.delete("/api/v1/delete_notification")
async def delete_notification(
    notification_id: int = Query(..., description="The ID of the notification to delete"),
    token: str = Query(..., description="User authentication token"),
    db: Session = Depends(get_db),
):
    try:
        user_id = await get_current_user(token)

        if user_id is None:
            raise HTTPException(status_code=400, detail="Invalid token or user not found")

        # Retrieve the notification 
        notification = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()

        if notification is None:
            raise HTTPException(status_code=404, detail="Notification not found")

        # Delete the notification
        db.delete(notification)
        db.commit()

        return {"message": "Notification deleted"}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") 
    


@user.get("/api/v1/get_job_titles")
def get_job_titles(db: Session = Depends(get_db)):
    job_titles = db.query(distinct(models.AllJobs.job_title)).all()

    # Check if job titles were found or raise an exception
    if not job_titles:
        raise HTTPException(status_code=404, detail="No job titles found")

    # Transform the result into a list of job titles
    job_titles_list = [title[0] for title in job_titles]

    return job_titles_list    