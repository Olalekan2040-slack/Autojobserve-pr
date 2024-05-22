import time
import sys
import logging

import undetected_chromedriver as uc
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from sqlalchemy import exc


from autojobserve.usable_functions import *

def drivers():
    # options = webdriver.ChromeOptions() 
    options = Options()
    options.add_argument("--ignore-ssl-errors=yes")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disk-cache-size=0") 

    driver = webdriver.Remote(
        command_executor="http://selenium-hub-auto:4444/wd/hub",
        options=options)
    
    return driver


def scrape_all(db):
    driver = drivers()
    #get the ur
    driver.get("https://jobserve.com/")
    time.sleep(10)
    reset_button = driver.find_element(By.XPATH, '//*[@id="reset"]')
    reset_button.click()
    time.sleep(5)    
    job_role = driver.find_element(By.ID, 'txtKey')
    time.sleep(5)
    # job_role.send_keys(job_title)
    # time.sleep(5)
    job_role.send_keys(Keys.RETURN)
    time.sleep(5)

    job_count = 0
    
    for i in range(1, 60):
        time.sleep(5)
        jobs = driver.find_element(By.ID, 'JobDetailPanel')
        time.sleep(5)
        job_title = jobs.find_element(By.ID, 'td_jobpositionlink').text
        print(job_title)
        time.sleep(5)
        company_name = jobs.find_element(By.ID, 'md_recruiter').text 
        time.sleep(5)
        job_type = jobs.find_element(By.ID, 'td_job_type').get_attribute("textContent")
        time.sleep(5)
        try:
            salary = jobs.find_element(By.XPATH, '//*[@id="md_rate"]').get_attribute("textContent")
            time.sleep(5)
        except StaleElementReferenceException:
            salary = ''
        except NoSuchElementException:
            salary = 'not stated'

        job_skills = jobs.find_element(By.ID, 'md_skills').get_attribute('textContent')
        time.sleep(5)
        skills = job_skills.split('\n')
        location = jobs.find_element(By.ID,'md_location').get_attribute('textContent')
        time.sleep(5)
        url = jobs.find_element(By.ID, "md_permalink").get_attribute("href")
        time.sleep(5)

        # create job
        create_job(job_title, salary, skills, location, url, company_name, job_type, db)

        
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, 'body').send_keys(Keys.ARROW_DOWN)
        logging.info(f"Job saved: {job_title}")
        print(i)
        job_count+=1
        time.sleep(5)
    driver.quit()

    return job_count
