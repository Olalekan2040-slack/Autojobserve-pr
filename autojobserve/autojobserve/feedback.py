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
from . import models
# Create a logger for this module
logger = logging.getLogger(__name__)
feedback = APIRouter()

# Define a cache with a TTL (time-to-live) of 1 hour
confirmation_email_cache = TTLCache(maxsize=1000, ttl=3600)

models.Base.metadata.create_all(bind=engine)


@feedback.post("/api/v1/feedback-contact")
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