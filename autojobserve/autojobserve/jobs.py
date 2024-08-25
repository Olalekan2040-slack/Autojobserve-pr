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


logger = logging.getLogger(__name__)
models.Base.metadata.create_all(bind=engine)
jobs = APIRouter()

@jobs.post('/api/v1/scrapejobs')
def scrape_jobs(jobtitle: str, db:Session=Depends(get_db)):
    no_jobs = scrape_job(jobtitle, db)
    return str(no_jobs) + " jobs has been scraped for you" 
 

@jobs.get("/api/v1/get_jobs")
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






@jobs.post("/api/v1/apply_for_job")
async def apply_for_job(
    request_data: ApplyForJobRequest = Body(...),
    db: Session = Depends(get_db)
):
    try:
        user_id = await get_current_user(request_data.token)
        logger.info(f"User ID retrieved: {user_id}")

        job = db.query(AllJobs).filter(AllJobs.job_id == request_data.job_id).first()

        if not job:
            logger.warning(f"Job with ID {request_data.job_id} not found")
            raise HTTPException(status_code=404, detail="Job not found")

        applied_job = db.query(AppliedJobs).filter(
            AppliedJobs.user_id == user_id,
            AppliedJobs.job_id == request_data.job_id
        ).first()

        if applied_job:
            logger.info(f"User {user_id} has already applied for job ID {request_data.job_id}")
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
                logger.info(f"User {user_id} applied for job ID {request_data.job_id}")

                # Update the job's auto_apply status
                job.auto_apply = True
                db.commit()

                # Retrieve user information for email notification
                user = db.query(Users).filter(Users.id == user_id).first()
                user_email = user.email if user else None
                if user_email:
                    job_title = job.job_title
                    await send_email_notification(user_email, job_title)
                    logger.info(f"Email notification sent to {user_email} for job {job_title}")
                    
                    notification_message = f"You have successfully applied for the job: {job_title}"
                    add_notification(db, user_id, notification_message)
                    logger.info(f"Notification added for user {user_id}")

                return {"message": "Job application successful", "applied_job_id": new_applied_job.id}
                
            elif request_data.action == 'goto_link':
                logger.info(f"Redirecting user {user_id} to job link for job ID {request_data.job_id}")
                db.commit()
                return RedirectResponse(url=job.job_permalink, status_code=status.HTTP_302_FOUND)
                
            else:
                logger.error(f"Invalid action provided by user {user_id}: {request_data.action}")
                raise HTTPException(status_code=400, detail="Invalid action. Use 'apply' or 'goto_link'")

        except Exception as e:
            db.rollback()
            logger.error(f"Error during job application process for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")



    

# History of applied-jobs endpoint
@jobs.get("/api/v1/applied_jobs")
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
@jobs.get("/api/v1/matched_jobs")
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



    
@jobs.get("/api/v1/recent_job_match")
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



@jobs.post("/api/v1/saved_jobs", response_model=SavedJobResponse)
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

@jobs.get("/api/v1/get_job_titles")
def get_job_titles(db: Session = Depends(get_db)):
    job_titles = db.query(distinct(models.AllJobs.job_title)).all()

    # Check if job titles were found or raise an exception
    if not job_titles:
        raise HTTPException(status_code=404, detail="No job titles found")

    # Transform the result into a list of job titles
    job_titles_list = [title[0] for title in job_titles]

    return job_titles_list    