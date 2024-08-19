import pytz, logging, asyncio
from fastapi import HTTPException
from datetime import datetime, timedelta
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from dotenv import load_dotenv


load_dotenv()
password = os.getenv("MAIL_PASSWORD")



# Connection Configuration for sending a confirmation message.
conf = ConnectionConfig(
    MAIL_USERNAME = "olalekanquadri58@gmail.com",
    MAIL_PASSWORD= password,
    MAIL_FROM = "test@email.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_FROM_NAME="Olalekan Quadri",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send_confirmation_email(email: str, first_name: str, jwt_token: str, user_timezone: str):
    # Determine the user's time zone using the provided 'user_timezone' parameter
    user_tz = pytz.timezone(user_timezone)
    
    # Calculate the expiration time in the user's time zone
    expiration_time_utc = datetime.now() + timedelta(hours=1)
    expiration_time_user_tz = expiration_time_utc.astimezone(user_tz)
    
    # Format the expiration time
    formatted_expiration_time = expiration_time_user_tz.strftime('%Y-%m-%d %H:%M:%S %Z')
    
    message = MessageSchema(
        subject="Confirm your email",
        recipients=[email],
        body=f"Hi {first_name}!\n\nPlease click the following link to confirm your email address:\n\nhttps://autojobserve-emailverification.netlify.app?token={jwt_token}\n\n"
             f"This link will expire at {formatted_expiration_time}.",
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_reset_password_email(email: str, username: str, reset_token: str, user_timezone: str):
    try:
        # Determine user's time zone using the provided 'user_timezone' parameter
        user_tz = pytz.timezone(user_timezone)
        
        # Calculate the expiration time in the user's time zone
        expiration_time_utc = datetime.now() + timedelta(hours=1)
        expiration_time_user_tz = expiration_time_utc.astimezone(user_tz)
        
        # Format the expiration time
        formatted_expiration_time = expiration_time_user_tz.strftime('%Y-%m-%d %H:%M:%S %Z')
        
        # Email content
        email_subject = "Password Reset"
        email_body = f"Hi {username}!\n\nPlease click the following link to reset your password:\n\n" \
                     f"https://autojobserveresetpassword.netlify.app?token={reset_token}\n\n" \
                     f"Remember to look in your spam folder, where automated messages sometimes filter. " \
                     f"If you still can't log in, please contact support.\n\n" \
                     f"This link will expire at {formatted_expiration_time}."

        message = MessageSchema(
            subject=email_subject,
            recipients=[email],
            body=email_body,
            subtype="html",
        )

        # Logging: Before sending the password reset email
        logging.info(f"Sending password reset email to {email}...")

        fm = FastMail(conf)
        await fm.send_message(message)

        # Logging: After successfully sending the password reset email
        logging.info(f"Password reset email sent successfully to {email}")

    except Exception as e:
        # Logging: If there's an error sending the email
        logging.error(f"Failed to send password reset email to {email}: {str(e)}")
        raise e


async def reset_success_email(email: str): 
    message = MessageSchema(
        subject="Password Reset Success",
        recipients=[email],
        body=f"Dear user,\n\nYour password has been successfully reset.\n\nBest regards,\nThe Password Reset Team",
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message) 

async def send_deactivation_email(email: str, first_name: str, deactivation_date):
        message = MessageSchema(
        subject="AutoJobServe Account Deactivation Confirmation",
        recipients=[email],
        body=f"Dear {first_name},\n\n\n\n" \
            "We hope this email finds you well. We are writing to confirm that your request to deactivate your account on AutoJobServe has been successfully processed. Your account is now in a deactivated state, and your profile and associated information are no longer visible to other users.\n\n" \
            f"Please be aware that your account will remain deactivated for a period of 30 days. During this time, you have the option to reactivate your account by simply logging in and selecting the reactivation option. However, if you do not reactivate your account within the next 30 days, it will be permanently deleted from our system.\n\n" \
            "We want to assure you that your account and personal information will be securely stored and protected during the deactivation period. You will not receive any notifications, emails, or communications from AutoJobServe during this time.\n\n" \
            f"If you have changed your mind and wish to reactivate your account, we kindly request that you do so before {deactivation_date}. After this period, all your data will be permanently removed from our platform, and you will no longer have access to your previous account details.\n\n" \
            "If you have any questions or require further assistance, please do not hesitate to reach out to our support team at support@Autojobserve.bincom.net. We are here to help!\n\n" \
            "Thank you for being a part of AutoJobServe, and we look forward to serving you again in the future.\n\n" \
            "Best regards,\n\n" \
            "Your Name\n\n" \
            "AutoJobServe Team",
        subtype="html",
    ) 
        fm = FastMail(conf)
        await fm.send_message(message)
      
      
async def send_deletion_reminder_email(email: str, first_name: str, reminder_date: datetime):
    subject = "Important: Your Account Deletion Reminder"

    message_body = f"Dear {first_name},\n\n"
    message_body += f"We hope this email finds you in good health and high spirits. We would like to bring to your attention that your account on AutoJobServe is scheduled for permanent deletion in {reminder_date}, as per your previous request to deactivate your account.\n\n"
    message_body += "If you have had a change of heart and wish to continue utilizing AutoJobServe, we encourage you to reactivate your account promptly. Reactivating is a simple process - just log in using your previous credentials.\n\n"
    message_body += "By reactivating your account, you will regain full access to your profile, job applications, and other personalized features on AutoJobServe. This presents an opportunity for you to pick up where you left off and continue your job search journey with us.\n\n"
    message_body += "It is essential to note that once the 3-day period has lapsed, your account and all associated data will be permanently deleted from our system. This includes your profile information, job applications, and any saved preferences.\n\n"
    message_body += "Should you require any assistance or have any inquiries, please do not hesitate to contact our dedicated support team at support@autojobserve.bincom.net. We are here to provide guidance and support throughout the reactivation process.\n\n"
    message_body += "Thank you for considering the reactivation of your AutoJobServe account. We deeply value your presence within our community and remain committed to supporting you in your job search endeavors.\n\n"
    message_body += "Best regards,\n\n"
    message_body += "[Your Name]\nAutoJobServe Team"

    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=message_body,
        subtype="html"
    )
    fm = FastMail(conf) 
    await fm.send_message(message)    


async def send_delete_confirmation_email(email: str, first_name: str):
        message = MessageSchema(
        subject="Account Deletion Confirmation",
        recipients=[email],
        body=f"Dear {first_name},\n\n\n\n" \
              "We are writing to inform you that your account on AutoJobServe has been permanently deleted in accordance with your request. All your profile information and associated data have been successfully removed from our system.\n\n" \
              "We understand that this decision was made after careful consideration, and we fully respect your choice. We would like to express our gratitude for your participation in the AutoJobServe community during your time with us.\n\n" \
              "Please be aware that you will no longer have access to your account, job applications, or any other personalised features on AutoJobServe. Your information has been securely and completely removed from our platform.\n\n" \
              "If you decide to return to AutoJobServe in the future, please note that you will need to create a new account and start afresh. We will be more than happy to assist you with this process if necessary.\n\n" \
              "Should you have any questions or require further assistance, please do not hesitate to contact our support team at support@Autojobserve.bincom.net. We are here to provide you with the help you need.\n\n" \
              "Once again, thank you for being a part of AutoJobServe. We wish you the best of luck in all your future endeavours.\n\n" \
              "Sincerely,\n\n\n\n\n" \
              "[Your Name]\n" \
              "AutoJobServe Team",
        subtype="html",
    ) 
        fm = FastMail(conf)
        await fm.send_message(message)             


async def send_feedback_email(name: str, email: str, subject: str, message: str):
    feedback_message = MessageSchema(
        subject="Feedback Received",
        recipients=["pmobincomglobal@bincom.net"], 
        body=f"Name: {name}\nEmail: {email}\nSubject: {subject}\nMessage: {message}",
        subtype="plain",
    )

    fm = FastMail(conf)
    await fm.send_message(feedback_message) 


# function that triggers 3 days before the 30 day expires. 
async def schedule_deletion_reminder(email, first_name, reminder_date): 

    now = datetime.utcnow()
    time_until_reminder = reminder_date - now

    # Check if the reminder date is in the future
    if time_until_reminder > timedelta(seconds=0):
        await asyncio.sleep(time_until_reminder.total_seconds())
        await send_deletion_reminder_email(email, first_name, reminder_date) 


# Function that triggers immediately after the 30 day period is over. 
async def schedule_delete_confirmation_email(email, first_name, deletion_date):
    now = datetime.utcnow()

    # Calculate the time remaining until deletion_date
    time_until_deletion = deletion_date - now

    # Check if the deletion date has passed
    if time_until_deletion.total_seconds() <= 0:
        # Deletion date has passed, send the confirmation email
        await send_delete_confirmation_email(email, first_name)       


async def send_email_notification(user_email, job_title):
    try:
        message = MessageSchema(
            subject='Job Application Successful',
            recipients=[user_email],
            body=f'Congratulations! You have successfully applied for the job: {job_title}',
            subtype="html",
        )
        fm = FastMail(conf)
        await fm.send_message(message)
    except Exception as e:
        # Handle email sending errors
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")