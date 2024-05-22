from sqlalchemy.orm import Session
from fastapi import Request
from user_agents import parse
from autojobserve.models import * 
from autojobserve.schemas import * 
from autojobserve.db import *
from typing import List
from PyPDF2 import PdfReader
import re 
import io
import csv

def get_user_by_email(email: str, db: Session):
    return db.query(Users).filter(Users.email == email).first()

def get_user_by_username(username: str, db: Session):
    return db.query(Users).filter(Users.username == username).first()

def create_user(user_data: dict, db: Session):
    new_user = Users(**user_data)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def capture_user_info(request: Request):
    user_info = {}
    
    # Capture user-agent, operating system, and IP
    user_agent = request.headers.get('User-Agent')
    if user_agent:
        user_agent_info = parse(user_agent)
        user_info['operating_system'] = user_agent_info.os.family
    else:
        user_info['operating_system'] = None

    user_info['client_ip'] = request.client.host if request.client else None
    
    return user_info 


# Function to save data to CSV
def save_to_csv(data):
    with open('user_data.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)


def save_password_to_db(password_data: PasswordSchema, db: Session):
    user_password = Password(**password_data)
    db.add(user_password)
    db.commit()
    db.refresh(user_password)

def save_job_title_to_db(job_title_data: JobTitleSchema, db: Session):
    job_title = JobTitle(**job_title_data)
    db.add(job_title)
    db.commit()
    db.refresh(job_title)

def save_location_db(user_location_data: LocationSchema, db: Session):
    user_location = Location(**user_location_data)
    db.add(user_location)
    db.commit()
    db.refresh(user_location)

def save_cv_to_db(cv_data: CVsSchema, db: Session):
    cv = CVs(**cv_data)
    db.add(cv)
    db.commit()
    db.refresh(cv)



def update_password_in_db(email: str, user_id: int, new_password: str, db: Session):
    try:
        user = get_user_by_email(email, db)
        if user and user.id == user_id:
            # Update the user's password in the Password table
            password_entry = db.query(Password).filter(Password.user_id == user_id).first()
            if password_entry:
                password_entry.password = new_password
            else:
                password_data = PasswordSchema(user_id=user_id, user_password=new_password)
                db_password_entry = Password(**password_data)
                db.add(db_password_entry)

            # Update the user's password in the Users table
            user.user_password = new_password

            # Commit the changes to the database
            db.commit()
            return True
        else:
            return False
    except SQLAlchemyError as e:
        db.rollback()  
        print(f"An error occurred during password update: {e}")
        return False


def create_user_profile(user_profile_data: dict, db: Session):
    new_user_profile = UserProfile(**user_profile_data)
    db.add(new_user_profile)
    db.commit()
    db.refresh(new_user_profile)
    return new_user_profile


async def create_feedback_contact_record(
    feedback_contact_data: FeedbackContactCreate,
    db: Session
):
    try:
        feedback_contact = FeedbackContact(
            name=feedback_contact_data.name,
            email=feedback_contact_data.email,
            subject=feedback_contact_data.subject,
            message=feedback_contact_data.message,
        )
        
        db.add(feedback_contact)
        db.commit()
        db.refresh(feedback_contact)
        
        return feedback_contact
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database Error")


def check_if_user_applied(user_id: int, joblink: str, db: Session):
    """Check if a user has applied for a job based on their user ID and the job link."""
    applied_job = db.query(AppliedJobs).filter(
        AppliedJobs.user_id == user_id,
        AppliedJobs.link_to_applied_jobs == joblink
    ).first()
    return applied_job is not None


def get_user_cv(user_id: int, db: Session):
    """Get a user's CV based on their user ID."""
    cv = db.query(CVs).filter(CVs.user_id == user_id).first()
    return cv
   

def create_job(job_title, salary, skills, location, url, company_name, job_type, db: Session):
    # Check if the job already exists in the database
    existing_job = db.query(AllJobs).filter(
        AllJobs.job_title == job_title,
        AllJobs.job_salary == salary,
        AllJobs.job_skill == skills,
        AllJobs.job_location == location,
        AllJobs.job_permalink == url,
        AllJobs.company_name == company_name,
        AllJobs.job_type == job_type
    ).first()

    if existing_job is not None:
        return

    # If the job doesn't exist, create and save it to the database
    new_job = AllJobs(
        job_title=job_title,
        job_salary=salary,
        job_skill=skills,
        job_location=location,
        job_permalink=url,
        company_name=company_name,
        job_type=job_type
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    

def match_jobs_to_user_profile(user_profile: UserProfile, db: Session) -> List[dict]:
    user_skills = user_profile.skills.split(', ') if user_profile.skills else []
    user_location = user_profile.user.user_location
    user_job_titles = user_profile.user.job_title.split(', ') if user_profile.user.job_title else []
    user_experience_from = user_profile.experience_from_year
    user_experience_to = user_profile.experience_to_year

    # Query the jobs from the AllJobs table.
    all_jobs = db.query(AllJobs).all()

    matched_jobs = []

    for job in all_jobs:
        job_skills = job.job_skill.split(', ')

        # Calculate the intersection of user skills and job skills.
        matching_skills = list(set(user_skills) & set(job_skills))

        # Calculate a matching score based on matched criteria.
        matching_score = len(matching_skills)

        # Additional criteria for matching: Location and Job Title
        if user_location and job.job_location and user_location.lower() in job.job_location.lower():
            matching_score += 1

        # Check if any user job title matches any job title of the current job.
        if user_job_titles and any(user_title.lower() in job_title.lower() for job_title in job.job_title.split(', ') for user_title in user_job_titles if job_title):
            matching_score += 1

        # Check if user's experience falls within the job's relevant information.
        if user_experience_from is not None and user_experience_to is not None:
            # Check if job_requirements is not None before attempting to iterate over it.
            if job.job_requirements is not None:
                # Check if user's experience is mentioned in job_requirements.
                if (
                    str(user_experience_from) in job.job_requirements
                    or str(user_experience_to) in job.job_requirements
                ):
                    matching_score += 1

            # Check if user's experience is mentioned in job_description or job_skill.
            if (
                str(user_experience_from) in job.job_description
                or str(user_experience_to) in job.job_description
                or str(user_experience_from) in job.job_skill
                or str(user_experience_to) in job.job_skill
            ):
                matching_score += 1

        # Match a job to a user if a match is found.
        if matching_score >= 1:
            matched_job_details = {
                "job_id": job.job_id,
                "job_title": job.job_title,
                "job_salary": job.job_salary,
                "job_location": job.job_location,
                "job_description": job.job_description,
                "job_skills": job.job_skill,
                "job_requirements": job.job_requirements,
                "company_name": job.company_name,
                "job_type": job.job_type,
                "auto_apply": job.auto_apply,
                "is_saved_job": job.is_saved_job,
                "matching_score": matching_score,
            }

            matched_jobs.append(matched_job_details)

    # Sort the matched jobs in descending order.
    matched_jobs.sort(key=lambda x: x['matching_score'], reverse=True)
    return matched_jobs


def add_notification(db, user_id, message,):
    notification = Notification(user_id=user_id, message=message)
    db.add(notification)
    db.commit()
    db.refresh(notification) 


def get_recent_job_matches_for_user(user_id: int, db: Session) -> list:
    try:
        # Fetch the user profile
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

        if not user_profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Use the existing function to match jobs to the user profile
        matched_jobs = match_jobs_to_user_profile(user_profile, db)

        # Return the most recent job matches
        if matched_jobs:
            return matched_jobs[:5]
        else:
            return None

    except Exception as e:
        print(f"Error in get_recent_job_matches_for_user: {str(e)}")
        return [] 
    

def extract_info_from_cv(pdf_text):
    extracted_info = {}

def extract_info_from_cv(pdf_text):
    extracted_info = {}

    # Extract education information
    education_match = re.search(r'(?i)\bEDUCATION\b(.*?)(?=\bSUMMARY\b|\bSKILLS\b|\bEXPERIENCE\b|$)', pdf_text, re.DOTALL)
    if education_match:
        extracted_info['education'] = education_match.group(1).strip()

    # Extract summary/bio information
    bio_match = re.search(r'(?i)\b(SUMMARY|BIO)\b(.*?)(?=\bEDUCATION\b|\bSKILLS\b|\bEXPERIENCE\b|$)', pdf_text, re.DOTALL)
    if bio_match:
        extracted_info['bio'] = bio_match.group(2).strip() if bio_match.group(2) else None

    # Extract skills information
    skills_match = re.search(r'(?i)\bSKILLS\b(.*?)(?=\bEDUCATION\b|\bEXPERIENCE\b|\b(SUMMARY|BIO)\b|$)', pdf_text, re.DOTALL)
    if skills_match:
        extracted_info['skills'] = skills_match.group(1).strip()

    # Extract experience information
    experience_match = re.search(r'(?i)\bExperience\b(.*?)(?=\b\w+\b:|\Z)', pdf_text, re.DOTALL)
    if experience_match:
        extracted_info['experience'] = experience_match.group(1).strip()

    # print("Education Match:", education_match)
    # print("Extracted Education:", extracted_info.get('education'))
    print("Bio Match:", bio_match)
    print("Extracted Bio:", extracted_info.get('bio'))
    print("Skills Match:", skills_match)
    print("Extracted Skills:", extracted_info.get('skills'))

    return extracted_info
