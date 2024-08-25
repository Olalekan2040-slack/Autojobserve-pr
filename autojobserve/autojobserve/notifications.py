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


notifications = APIRouter()
models.Base.metadata.create_all(bind=engine)

@notifications.get("/api/v1/notifications")
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
    

@notifications.put("/api/v1/mark_notification_as_read")
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
@notifications.delete("/api/v1/delete_notification")
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