from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, UniqueConstraint, Boolean, DateTime, func, Text, DECIMAL
from sqlalchemy.ext.declarative import declarative_base 
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    username = Column(String(50), nullable=False, unique=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    user_password = Column(String(100), nullable=False)
    job_title = Column(String(100), nullable=True)
    user_location = Column(String(255), nullable=True)
    cv = Column(String(200), nullable=True)

    __table_args__ = (
        UniqueConstraint('email', name='uq_email'),
        UniqueConstraint('username', name='uq_username'),
    )

    user_profile = relationship("UserProfile", uselist=False, back_populates="user")
    notification = relationship("Notification", back_populates="user")

class AllJobs(Base):
    __tablename__ = 'all_jobs'

    job_id = Column(Integer, primary_key=True, autoincrement=True)
    job_title = Column(String(255), nullable=False)
    job_salary = Column(String(255), nullable=False)
    job_skill = Column(Text, nullable=False)
    job_location = Column(String(255), nullable=False)
    job_permalink = Column(String(255), unique=True) 
    job_requirements = Column(String(2000), nullable=True)
    job_description = Column(String(2000), nullable=True)
    company_name = Column(String(255), nullable=True)
    job_type = Column(String(255), nullable=True)
    auto_apply = Column(Boolean, default=False, nullable=False) 
    is_saved_job = Column(Boolean, default=False, nullable=False)
    created_by = Column(String(255), default='admin')
    modified_by = Column(String(255), default='admin')
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    modified_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)
#     modified_at = Column(
#     TIMESTAMP,
#     server_default=text('CURRENT_TIMESTAMP'),
#     server_onupdate=text('CURRENT_TIMESTAMP'),
#     nullable=False
# )

    __table_args__ = (
        UniqueConstraint('job_permalink', name='uq_job_permalink'),
    )

class AppliedJobs(Base):
    __tablename__ = 'applied_jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    job_id = Column(Integer, ForeignKey('all_jobs.job_id'), nullable=False)
    link_to_applied_jobs = Column(String(255), nullable=False)
    created_by = Column(String(255), default='admin')
    modified_by = Column(String(255), default='admin')
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    modified_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)
    # modified_at = Column(
    #     TIMESTAMP,
    #     server_default=text('CURRENT_TIMESTAMP'),
    #     server_onupdate=text('CURRENT_TIMESTAMP'),
    #     nullable=False
    # )

class SavedJob(Base):
    __tablename__ = "saved_jobs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey('all_jobs.job_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    saved_job_title = Column(String(255), nullable=False)
    saved_job_salary = Column(String(255), nullable=False)
    saved_job_skill = Column(Text, nullable=False)
    saved_job_location = Column(String(255), nullable=False)
    saved_job_auto_apply = Column(Boolean, default=False, nullable=False) 
    # saved_job_is_saved_job = Column(Boolean, default=False, nullable=False)
    saved_job_permalink = Column(String(255))
    saved_job_description = Column(String(2000), nullable=True)
    saved_job_requirements = Column(String(2000), nullable=True)
    saved_company_name = Column(String(255), nullable=True)
    saved_job_type = Column(String(255), nullable=True)
    created_by = Column(String(255), default='admin')
    modified_by = Column(String(255), default='admin')
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    modified_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)    
    # modified_at = Column(
    #     TIMESTAMP,
    #     server_default=text('CURRENT_TIMESTAMP'),
    #     server_onupdate=text('CURRENT_TIMESTAMP'),
    #     nullable=False
    # )

class Password(Base):
    __tablename__ = 'password'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user_password = Column(String(255), nullable=False)
    created_by = Column(String(255), default='admin')
    modified_by = Column(String(255), default='admin')
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    modified_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)
    # modified_at = Column(
    #     TIMESTAMP,
    #     server_default=text('CURRENT_TIMESTAMP'),
    #     server_onupdate=text('CURRENT_TIMESTAMP'),
    #     nullable=False
    # )


class Location(Base):
    __tablename__ = 'location'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user_location = Column(String(255), nullable=True)
    created_by = Column(String(255), default='admin')
    modified_by = Column(String(255), default='admin')
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    modified_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)
    # modified_at = Column(
    #     TIMESTAMP,
    #     server_default=text('CURRENT_TIMESTAMP'),
    #     server_onupdate=text('CURRENT_TIMESTAMP'),
    #     nullable=False
    # )
    user_profile_id = Column(Integer, ForeignKey('user_profile.id'))
    user_profile = relationship("UserProfile", back_populates="location")


class CVs(Base):
    __tablename__ = 'cvs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    cv = Column(String(200), nullable=True)
    created_by = Column(String(255), default='admin')
    modified_by = Column(String(255), default='admin')
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    modified_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)
    # user_profile = relationship("UserProfile", back_populates="cvs")
    # modified_at = Column(
    #     TIMESTAMP,
    #     server_default=text('CURRENT_TIMESTAMP'),
    #     server_onupdate=text('CURRENT_TIMESTAMP'),
    #     nullable=False
    # )
    user_profile_id = Column(Integer, ForeignKey('user_profile.id'))
    user_profile = relationship("UserProfile", back_populates="cvs")

class JobTitle(Base):
    __tablename__ = 'jobtitle'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    job_title = Column(String(255), nullable=True)
    created_by = Column(String(255), default='admin')
    modified_by = Column(String(255), default='admin')
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    modified_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)
    # modified_at = Column(
    #     TIMESTAMP,
    #     server_default=text('CURRENT_TIMESTAMP'),
    #     server_onupdate=text('CURRENT_TIMESTAMP'),
    #     nullable=False
    # )
    user_profile_id = Column(Integer, ForeignKey('user_profile.id'))
    user_profile = relationship("UserProfile", back_populates="jobtitle")


class FeedbackContact(Base):
    __tablename__ = 'feedback_contacts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=False)
    created_by = Column(String(255), default='admin')
    created_at = Column(DateTime, default=func.now(), nullable=False)



class UserProfile(Base):
    __tablename__ = 'user_profile'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    bio = Column(String(1000), nullable=True)
    website = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    address = Column(String(500), nullable=True)
    date_of_birth = Column(String(10), nullable=True)
    gender = Column(String(10), nullable=True)
    nationality = Column(String(100), nullable=True)
    language = Column(String(255), nullable=True)
    education = Column(String(1000), nullable=True)
    work_experience = Column(String(2000), nullable=True)
    job_description = Column(String(1000), nullable=True)
    skills = Column(String(2000), nullable=True)
    position = Column(String(255), nullable=True)
    job_preference = Column(String(255), nullable=True)
    social_media = Column(String(255), nullable=True)
    experience_from_year = Column(Integer, nullable=True)
    experience_to_year = Column(Integer, nullable=True)    
    email_verified = Column(Boolean, default=False)
    active = Column(Boolean)
    restricted = Column(Boolean)
    deactivated_at = Column(DateTime, default=func.now())
    hidden = Column(Boolean)
    deactivation_date = Column(DateTime, default=None)
    email_notifications = Column(Boolean, default=True)
    mobile_messaging = Column(Boolean, default=True)
    deleted = Column(Boolean, default=False)
    
    created_by = Column(String(255), default='admin')
    modified_by = Column(String(255), default='admin')
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    modified_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)
    # modified_at = Column(
    #     TIMESTAMP,
    #     server_default=text('CURRENT_TIMESTAMP'),
    #     server_onupdate=text('CURRENT_TIMESTAMP'),
    #     nullable=False
    # )
    user = relationship("Users", uselist=False, back_populates="user_profile")
    location = relationship("Location", uselist=False, back_populates="user_profile")
    jobtitle = relationship("JobTitle", uselist=False, back_populates="user_profile")
    cvs = relationship("CVs", uselist=False, back_populates="user_profile")
    # cvs = relationship("CVs", back_populates="user_profile") 

    def update_job_title(self, job_title):
        if self.jobtitle:
            self.jobtitle.job_title = job_title

    def update_cv(self, cv):
        if self.cvs:
            self.cvs.cv = cv

    def update_user_location(self, user_location):
        if self.location:
            self.location.user_location = user_location 


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)

    user = relationship("Users", back_populates="notification")            
