import time
import logging
import os
import sys
#import pickle

#import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from sqlalchemy import exc

from selenium_scripts.Glassdoor_Jobs.Glassdoor_save_jobs import save_Glassdoor_jobs 
# from autojobserve.usable_functions import save_jobs

def configure_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument("--ignore-ssl-errors=yes")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disk-cache-size=0")
    return options

def drivers():
    options = configure_chrome_options()
    driver = webdriver.Remote(
        command_executor="http://selenium-hub-auto:4444/wd/hub",
        options=options
    )
    #with uc.Chrome() as driver:
    url = "https://www.glassdoor.com/index.htm"
    driver.get(url)
    time.sleep(1)    
    return driver

def job_permalink(driver,job_count):   
     
    try:
        Link = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, f'//*[@id="left-column"]/div[1]/ul/li[{job_count}]/div/div/div[1]/div[1]/a[2]')))                                                                         
        return Link.get_attribute('href')
        
    except:                                                            
        print('An error occurred while getting link')

def easy_apply_button(driver):                                      
        try:  
            driver.find_element(By.XPATH, '//*[@id="app-navigation"]/div[4]/div[2]/div[2]/div[1]/header/div[3]/div[2]/div/button/span').text
            return True                           
        except NoSuchElementException:
            return False       
 

def close_pop_up(driver):
    time.sleep(5)
    try:
        driver.find_elements(By.CLASS_NAME, "SVGInline modal_closeIcon").click()
        time.sleep(10)          
        driver.find_elements(By.CLASS_NAME, "SVGInline modal_closeIcon").click()
    except (NoSuchElementException, ElementClickInterceptedException,StaleElementReferenceException):
        time.sleep(10)



def close(driver):
        try:
            driver.find_element(By.CLASS_NAME, "SVGInline modal_closeIcon").click()
            time.sleep(10)
        except (NoSuchElementException, ElementClickInterceptedException,StaleElementReferenceException):
            time.sleep(5)

def show_more_jobs(driver):                       
    try:
        show_more_button = driver.find_element(By.CLASS_NAME, 'JobsList_buttonWrapper__ticwb')
        print("Found Show More button")
        if show_more_button.is_displayed():
            print("Show More button is displayed")
            show_more_button.click()
            print("Clicked on Show More button")
            time.sleep(2)  
            return True
    except NoSuchElementException:
        print("Show More button not found")
        return False
    
def search_location(driver,location=None):
        search_input = driver.find_element(By.ID, 'searchBar-location')
        if location:
            search_input.send_keys(location)
            search_input.send_keys(Keys.ENTER) 
            search_input.clear()
            
def search_job_title(driver,job_title=None):
        search_input = driver.find_element(By.ID, 'searchBar-jobTitle') 
        if job_title:
            search_input.send_keys(job_title)   
            search_input.send_keys(Keys.ENTER) 
            search_input.clear() 
                 
def scrape_job_details(driver, db):  
    
        job_count = 0
        time.sleep(15)
        while True:       
            job_list = driver.find_elements(By.CLASS_NAME,'JobsList_jobListItem__wjTHv')
            print(f"Beginning: {len(job_list)}")
                        
            #for job_item in range (job_count,len(job_list)-1):  
            for job_item in range (job_count,50):  
                try:   
                    time.sleep(5)
                    job_list[job_item].click()
                    close(driver)
                    time.sleep(5)
                    try:                        
                        title = driver.find_element(By.XPATH, '//*[@id="jd-job-title-1009195300543"]')
                        job_title = title.text
                    except Exception:
                         job_title = 'not stated'
                    close(driver)
                    is_easy_apply = easy_apply_button(driver)
                    close(driver)
                    try:
                        company_element = driver.find_elements(By.CLASS_NAME,  'EmployerProfile_employerInfo__d8uSE')[job_item]
                        company_name = company_element.text if company_element else ""
                        #print(len(company))  # Getting the length of the company name
                    except Exception:
                        company_name = 'not stated'
                    close(driver)
                    url = job_permalink(driver, job_item + 1)
                    close(driver)
                    location = driver.find_element(By.CLASS_NAME, 'JobDetails_location__mSg5h').text
                    close(driver)
                    try:
                          job_description = driver.find_element(By.XPATH, '//*[@id="app-navigation"]/div[4]/div[2]/div[2]/div[1]/section/div[2]/div[1]').text
                    except StaleElementReferenceException:
                          job_description = ''
                    except Exception:
                           job_description = 'not stated'
                    close(driver)
                    try:
                            job_salary = driver.find_element(By.CLASS_NAME, 'SalaryEstimate_salaryRange__brHFy').text
                    except StaleElementReferenceException:
                            job_salary = ''
                    except Exception:
                            job_salary = 'not stated'
                    
                    print(f"{job_item +1 },Job Title: {job_title}, Company:{company_name} Location: {location},Easy_Apply:{is_easy_apply},Job_salary:{job_salary} Job Description: {job_description},Job_Reference:{url}")
                    
                    save_Glassdoor_jobs(db, company_name,job_title, job_salary,is_easy_apply, location, job_description, url)
                    # save_jobs(db,company_name,job_title, job_salary, location, is_easy_apply, job_description, url)
                    #save_jobs(db, company_name, job_title, job_salary, location, url, skills,job_requirement,job_description,is_easy_apply,job_type)
                    print(f"Job saved: {job_title}")
                    #driver.find_element(By.CSS_SELECTOR, 'body').send_keys(Keys.ARROW_DOWN)
                    time.sleep(10)
                    
                except Exception as e: 
                    print(e) 
            job_count = len(job_list)
            # if job_count >= 50:
            #    break
           
            if show_more_jobs(driver):
                print(f"Next round:{job_count}")
                time.sleep(15)
                if job_count >= 50:
                   break
            else:
                break
            
        print("Scraping completed") 
        return job_count
           
def login_glassdoor(db,job_title=None,location=None):
    driver = drivers()   
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

    close(driver)   


    job_page_url = "https://www.glassdoor.com/Job/index.htm"
    driver.get(job_page_url)
    time.sleep(10)
    
    close(driver)
    
    search_job_title(driver,job_title)
    close(driver)

    search_location(driver,location)
    close(driver)
    scrape_job_details(driver, db) 
    time.sleep(5)
    
    #close(driver)
    
    
    
