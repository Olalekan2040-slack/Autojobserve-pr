from pydantic import BaseModel, EmailStr, constr
from typing import List, Optional

# Create Pydantic models for each table
class UserSchema(BaseModel):
    email: EmailStr
    username: constr(max_length=50)
    first_name: str
    last_name: str
    user_password: str
    job_title: Optional[str]
    user_location: Optional[str]
    cv: Optional[str]
    user_profile: Optional["UserProfileSchema"] 

class AllJobsSchema(BaseModel):
    job_title: str
    # job_salary: str
    job_salary: Optional[float]
    job_skill: str
    job_location: str
    job_link: str
    job_permalink: str 
    job_description: str 
    job_requirements: str 
    company_name: str 
    job_type: str  
    auto_apply: bool = False 

class AppliedJobsSchema(BaseModel):
    user_id: int
    job_id: int
    link_to_applied_jobs: str

class SavedJobSchema(BaseModel):
    job_id: int
    user_id: int
    saved_job_title: str
    saved_job_salary: str
    saved_job_skill: str
    saved_job_location: str
    saved_job_auto_apply: bool = False
    saved_job_permalink: str
    saved_job_description: str
    saved_job_requirements: str
    saved_company_name: str
    saved_job_type: str

class PasswordSchema(BaseModel):
    user_id: int
    user_password: str

class LocationSchema(BaseModel):
    user_id: int
    user_location: Optional[str]
    user_profile_id: Optional[int]

class CVsSchema(BaseModel):
    user_id: int
    cv: Optional[str]
    user_profile_id: Optional[int]

class JobTitleSchema(BaseModel):
    user_id: int
    job_title: Optional[str]
    user_profile_id: Optional[int]

class UserProfileSchema(BaseModel):
    user_id: int
    bio: Optional[str]
    website: Optional[str]
    phone_number: Optional[str]
    address: Optional[str]
    date_of_birth: Optional[str]
    gender: Optional[str]
    nationality: Optional[str]
    language: Optional[str]
    education: Optional[str]
    work_experience: Optional[str]
    job_description: Optional[str]
    skills: Optional[str]
    position: Optional[str]
    job_preference: Optional[str]
    social_media: Optional[str]
    experience_from_year: Optional[int]
    experience_to_year: Optional[int]
    email_verified: bool = False
    active: Optional[bool] 
    restricted: Optional[bool]
    deactivated_at: Optional[str]
    hidden: Optional[bool]
    deactivation_date: Optional[str]
    email_notifications: Optional[bool] = True
    mobile_messaging: Optional[bool] = True
    deleted: bool = False

class UserWithJobsSchema(BaseModel):
    id: int
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    jobs: List[AllJobsSchema] = []

class UserWithAppliedJobsSchema(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    applied_jobs: List[AppliedJobsSchema] = []

class UserWithPasswordSchema(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    password: PasswordSchema

class UserWithLocationSchema(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    location: List[LocationSchema] = []

class UserWithCVsSchema(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    cvs: List[CVsSchema] = []

class UserWithJobTitleSchema(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    jobtitle: List[JobTitleSchema] = []

class UserWithUserProfileSchema(BaseModel):
    id: int
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    user_profile: UserProfileSchema

    class Config:
        orm_mode = True 


class ResetPassword(BaseModel): 
    email: EmailStr

class ResetPasswordPageRequest(BaseModel):
    reset_token: str
    new_password: str
    confirm_password: str


class CombinedProfileResponse(BaseModel):
    user_id: int
    email: EmailStr
    username: constr(max_length=50)
    first_name: str
    last_name: str
    job_title: Optional[str]
    user_location: Optional[str]
    cv: Optional[str]
    bio: Optional[str]
    website: Optional[str]
    phone_number: Optional[str]
    address: Optional[str]
    date_of_birth: Optional[str]
    gender: Optional[str]
    nationality: Optional[str]
    language: Optional[str]
    education: Optional[str]
    work_experience: Optional[str]
    job_description: Optional[str]
    skills: Optional[str]
    position: Optional[str]
    job_preference: Optional[str]
    social_media: Optional[str]
    experience_from_year: Optional[int]
    experience_to_year: Optional[int]
    active: Optional[bool]
    email_notifications: Optional[bool] = True
    mobile_messaging: Optional[bool] = True


class EditProfileResponse(BaseModel):
    message: str
    profile: CombinedProfileResponse


class ActivateProfileResponse(BaseModel):
    message: str
    deactivated_at: Optional[str]
    active: Optional[bool]
    hidden: Optional[bool]
    restricted: Optional[bool]
    deactivation_date: Optional[str]


class DeactivateProfileResponse(BaseModel): 
    message: str
    deactivated_at: Optional[str]
    active: Optional[bool]
    hidden: Optional[bool]
    deactivation_date: Optional[str]
    restricted: Optional[bool]

class DeleteProfileResponse(BaseModel):
    message: str    


class FeedbackContactCreate(BaseModel):
    # user_id: Optional[int] = None
    name: str
    email: EmailStr
    subject: str
    message: str 

class JobApplicationRequest(BaseModel):
    email: str
    joblink: str   

class ApplyForJobRequest(BaseModel):
    token: str
    job_id: int
    action: str = 'apply'    
    link_to_applied_jobs: Optional[str] = None


class SaveJobRequest(BaseModel):
    job_id: int
    user_id: int


class SavedJobResponse(BaseModel):
    id: int
    job_id: int
    user_id: int
    saved_job_title: str
    saved_job_salary: str
    saved_job_skill: str
    saved_job_location: str
    saved_job_auto_apply = bool = False
    saved_job_permalink: str
    saved_job_description: str
    saved_job_requirements: str
    saved_company_name: str

class NotificationsSchema(BaseModel):
    id: int
    user_id: int
    message: str
    is_read: bool = False