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

auth = APIRouter()

@auth.get('/')
def main():
    return {'message': 'Welcome to AutoJobServe'}


# Registration endpoint
@auth.post("/api/v1/register")
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
@auth.post('/api/v1/confirm-email/{user_id}')
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

@auth.post("/api/v1/login")
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
@auth.post('/api/v1/reset')
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

@auth.post("/api/v1/reset_password")
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





# Activate Endpoint
@auth.post("/api/v1/activate", response_model=ActivateProfileResponse)
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
@auth.post("/api/v1/deactivate", response_model=DeactivateProfileResponse)
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


@auth.delete("/api/v1/delete", response_model=DeleteProfileResponse)
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