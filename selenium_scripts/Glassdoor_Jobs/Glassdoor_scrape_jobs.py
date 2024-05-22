import time
import logging
import os
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException,StaleElementReferenceException,ElementNotInteractableException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from sqlalchemy import exc

from selenium_scripts.Glassdoor_Jobs.Glassdoor_save_jobs import save_Glassdoor_jobs
from autojobserve.usable_functions import *

def configure_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument("--ignore-ssl-errors=yes")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disk-cache-size=0")
   # return options

#def drivers():
    #options = configure_chrome_options()
    driver = webdriver.Remote(
        command_executor="http://selenium-hub-auto:4444/wd/hub",
        options=options
    )
    url = "https://www.glassdoor.com/index.htm"
    driver.get(url)
    time.sleep(1)
    return driver
def job_permalink(driver,job_count):   
     
    try:
        Link = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH,f'//*[@id="left-column"]/div[2]/ul/li[{job_count}]/div/div/div[1]/div[1]/a[2]')))
        return Link.get_attribute('href')
    except:                                                            
        print('An error occurred while getting link')
def easy_apply_button(driver):
        try:
            driver.find_element(By.XPATH, '//*[@id="app-navigation"]/div[3]/div[2]/div[2]/div[1]/header/div[3]/div[2]/div/button/span').text
            return True
        except NoSuchElementException:
            return False       

#closes job_alert prompt
def close(driver):
        try:
            driver.find_element(By.XPATH, '//*[@id="JAModal"]/div/div[2]/span').click()
            time.sleep(5)
        except (NoSuchElementException, ElementClickInterceptedException):
            time.sleep(5)
    
def scrape_job_details(driver,db):
        
        job_count = 0
        time.sleep(5)
        job_list = driver.find_elements(By.CLASS_NAME,'JobsList_jobListItem__JBBUV')
        print(f"Beginning: {len(job_list)}")
        time.sleep(15)
        #try:
            #for job_item in range (len(job_cards)):
        for job_item in range (job_count,len(job_list)):
                #try:
                    time.sleep(5)
                    job_list[job_item].click()
                    close(driver)
                    time.sleep(5)
            
                    job_title = driver.find_element(By.CLASS_NAME, 'JobCard_jobTitle___7I6y').get_attribute("textContent")
                    close(driver)
                    try:
                        company_element = driver.find_elements(By.CLASS_NAME,  'EmployerProfile_employerInfo__7VkqD')[job_item]
                        company_name = company_element.text if company_element else ""
                        #print(len(company))  # Getting the length of the company name
                    except Exception:
                        company_name= 'not stated'
                    close(driver)

                    location = driver.find_element(By.CLASS_NAME, 'JobDetails_location__MbnUM').text
                    close(driver)
                    try:
                       job_description = driver.find_element(By.XPATH, '//*[@id="app-navigation"]/div[3]/div[2]/div[2]/div/section/div/div[1]').text 
                    except Exception:
                        job_description = 'not stated'
                    close(driver)

                    try:
                        job_salary = driver.find_element(By.CLASS_NAME, 'SalaryEstimate_averageEstimate__xF_7h').text
                    except StaleElementReferenceException:
                            job_salary = ''
                    except Exception:
                            job_salary = 'not stated'       
                    close(driver)
                    is_easy_apply = easy_apply_button(driver)
                    close(driver)
                    url = job_permalink(driver,job_item+ 1)
                    
                    #job_count =+1
                    logging.info(f"Job saved: {job_title}")
                    print(f"{job_item + 1},Job Title: {job_title},Company:{company_name},Salary:{job_salary}, Location: {location}, Job Description: {job_description}, Easy_Apply:{is_easy_apply}, Job_Reference:{url}")
                    #save_Glassdoor_jobs(db,company,job_title,job_salary,is_easy_apply, job_location, job_description, url)
                    save_jobs(db, job_title, job_salary, location, url, company_name,is_easy_apply, job_description) 
                    time.sleep(10)
                        
                #except ElementClickInterceptedException as e:
                    #print(e)
        job_count = len(job_list)
        #except Exception as e:
        #print(f"An error occurred: {str(e)}")  
        return job_count

def login_glassdoor(job_title,db):
        driver = configure_chrome_options()
        Gd_user = os.environ.get('GLASSDOOR_USER')
        Gd_password = os.environ.get('GLASSDOOR_PASSWORD')
    
        if not Gd_user or not Gd_password:
            print("Login credentials not found in environment variables")
            time.sleep(10)
            return
        
        
        username_field = driver.find_element(By.ID, "inlineUserEmail")
        username_field.send_keys(Gd_user)

        cntd_with_email_btn = driver.find_element(By.XPATH, '//*[@id="InlineLoginModule"]/div/div[1]/div/div/div/div/form/div[2]/button')
        cntd_with_email_btn.click()
        time.sleep(5)

        password_field = driver.find_element(By.ID, "inlineUserPassword")
        password_field.send_keys(Gd_password)

        login_btn = driver.find_element(By.XPATH, '//*[@id="InlineLoginModule"]/div/div[1]/div/div/div/div/form/div[2]/button')
        login_btn.click()
        time.sleep(5)
            
    #def search_jobs(driver, job_title):
        job_page_url = "https://www.glassdoor.com/Job/index.htm"
        driver.get(job_page_url)
        time.sleep(10)

        search_input = driver.find_element(By.ID, 'searchBar-jobTitle')
        search_input.send_keys(job_title)
        search_input.send_keys(Keys.ENTER)
        time.sleep(5)

        close(driver)
        search_input = driver.find_element(By.ID, 'searchBar-location')
        search_input.send_keys("Nigeria")
        search_input.send_keys(Keys.ENTER)

        scrape_job_details(driver,db)   
        time.sleep(5)
        
       