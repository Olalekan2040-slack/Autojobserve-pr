import os
import time
import logging
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

# Set up logging
logging.basicConfig(filename='job_application.log', level=logging.INFO)

# Get the current directory where the script is located
current_directory = os.path.dirname(os.path.abspath(__file__))

# Specify the path to chromedriver relative to the script location
chromedriver_path = os.path.join(current_directory, "../chromedriver/chromedriver")

def apply_through_link(email, joblink, cvlink):
    # Configure Chrome options
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--disable-gpu")
    
    try:
        # Initialize the WebDriver with Chrome options and connect to the hub
        driver = webdriver.Remote(
            command_executor="http://selenium-hub-auto:4444/wd/hub",
            options=chrome_options 
        ) 

        # driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)


        # Set an implicit wait to handle elements that may take time to load
        driver.implicitly_wait(30)

        # Navigate to the job application page
        driver.get(joblink)

        # Find and fill in the email field
        email_field = driver.find_element(By.ID, 'Q0006_ans')
        email_field.send_keys(email)

        # Find and select the appropriate option for work permit
        select_work_permit = driver.find_element(By.ID, 'Q0133_ans')
        select_work_permit.send_keys("Work Permit Holder (No Sponsor Required)")

        # Check if the 'None but prepared to undertake security clearance' option exists
        try:
            select_security_clearance = driver.find_element(By.ID, 'Q0142_ans')
            select_security_clearance.send_keys("None but prepared to undertake security clearance")
        except NoSuchElementException:
            pass 

        # Upload CV
        cv_upload_field = driver.find_element(By.ID, 'filCV')
        cv_upload_field.send_keys(cvlink)

        # Click the 'Apply' button (modify this line according to your website's structure)
        # For example, if the button has a class name 'AppButton', you can use:
        # driver.find_element(By.CLASS_NAME, 'AppButton').click()

        # Wait for a few seconds to ensure the application is submitted
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'confirmation_message')))
        
        # Log success
        logging.info(f"Application submitted successfully for {email}")

    except Exception as e:
        # Log error
        logging.error(f"An error occurred: {str(e)}")
    finally:
        # Close the browser window
        driver.quit()
