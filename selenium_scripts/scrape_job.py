import time
import sys
import logging

#import undetected_chromedriver as uc
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException, WebDriverException, ElementNotInteractableException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
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
    
    url = "https://jobserve.com/"
    driver.get(url)
    time.sleep(5)
    return driver


def scrape_job_data(db,driver,job_title=None): 
    #driver = drivers()
    time.sleep(5)
    driver.find_element(By.XPATH, '//*[@id="reset"]/a').click()
    time.sleep(10)
    search_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="txtKey"]')))
    if job_title != None:
        search_input.send_keys(job_title)
        search_input.send_keys(Keys.ENTER)   
        print(f"Entered job title: {job_title}")
        time.sleep(10)  
        #logging.exception(f"Error occurred while searching job title: {str(e)}") 
        job_count = 0
        for i in range(1,50):        
            time.sleep(10)            
            jobs = driver.find_elements(By.ID,'JobDetailPanel') 
            time.sleep(15)
            for job in jobs:
                job_title = job.find_element(By.ID, 'td_jobpositionlink').text
                time.sleep(5)
                company_name = job.find_element(By.XPATH, '//*[@id="md_recruiter"]/a/span/span').text 
                time.sleep(5)
                job_type = job.find_element(By.ID, 'td_job_type').get_attribute("textContent")
                time.sleep(5)
                try:
                    job_salary = job.find_element(By.XPATH, '//*[@id="md_rate"]').get_attribute("textContent")
                    time.sleep(5)
                except StaleElementReferenceException:
                    job_salary = ''
                except NoSuchElementException:
                    job_salary = 'not stated'

                skills = job.find_element(By.ID, 'md_skills').get_attribute('textContent')
                time.sleep(5)
                skills = skills.split('\n')
                location_address = job.find_element(By.ID,'md_location').get_attribute('textContent')
                time.sleep(5)
                url = job.find_element(By.ID, "md_permalink").get_attribute("href")
                time.sleep(5)

                save_jobs(db, company_name=company_name, job_title=job_title, job_salary=job_salary, location=location_address, url=url, skills=skills, job_type=job_type, is_easy_apply=None, job_description=None, job_requirements=None)
                #save_jobs(db,company_name,job_title, job_salary, location, url, skills, job_type)
                print(f" {i+1},Company:{company_name}, Job_Title:{job_title}, Salary:{job_salary}, Skills:{skills}, Location:{location_address}, Reference:{url}, Job_type:{job_type}")           
                time.sleep(1)
                driver.find_element(By.CSS_SELECTOR, 'body').send_keys(Keys.ARROW_DOWN)
                logging.info(f"Job saved: {job_title}")
                print(i)
                job_count+=1
                time.sleep(5)
        driver.quit()

        return job_count

def scrape_job(db,job_title=None, location=None):
    driver=drivers()
    
    driver.find_element(By.XPATH, '//*[@id="reset"]/a').click()
    time.sleep(10)
    search_input = driver.find_element(By.ID, 'txtKey')
    time.sleep(10)
    
    drop_down = driver.find_element(By.XPATH, '//*[@id="ddcountries"]/div')
    drop_down.click() 
    time.sleep(10)
    #location = location.lower()        
    if location is not None and job_title is not None: 
        location_option_xpath = f'//*[@id="ddcountries"]/ul/li/a[text()="{location}"]'
        location_element = WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH, location_option_xpath)))   
        location_element.click()
        time.sleep(10) 
        return scrape_job_data(db,driver=driver,job_title=job_title)
    elif location is not None and job_title is None:
        #if location is not None:                                       
        location_option_xpath = f'//*[@id="ddcountries"]/ul/li/a[text()="{location}"]'
        location_element = WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH, location_option_xpath)))   
        location_element.click()
        time.sleep(10)
        search_btn = driver.find_element(By.ID,'btnSearch')
        if search_btn:
            search_btn.click()
            time.sleep(5)
            job_count = 0
            for i in range(1,50):        
                time.sleep(10)            
                jobs = driver.find_elements(By.ID,'JobDetailPanel') 
                time.sleep(15)
                for job in jobs:
                    job_title = job.find_element(By.ID, 'td_jobpositionlink').text
                    time.sleep(5)
                    company_name = job.find_element(By.XPATH, '//*[@id="md_recruiter"]/a/span/span').text 
                    time.sleep(5)
                    job_type = job.find_element(By.ID, 'td_job_type').get_attribute("textContent")
                    time.sleep(5)
                    try:
                        job_salary = job.find_element(By.XPATH, '//*[@id="md_rate"]').get_attribute("textContent")
                        time.sleep(5)
                    except StaleElementReferenceException:
                        job_salary = ''
                    except NoSuchElementException:
                        job_salary = 'not stated'

                    skills = job.find_element(By.ID, 'md_skills').get_attribute('textContent')
                    time.sleep(5)
                    skills = skills.split('\n')
                    location_address = job.find_element(By.ID,'md_location').get_attribute('textContent')
                    time.sleep(5)
                    url = job.find_element(By.ID, "md_permalink").get_attribute("href")
                    time.sleep(5)

                    save_jobs(db, company_name=company_name, job_title=job_title, job_salary=job_salary, location=location_address, url=url, skills=skills, job_type=job_type, is_easy_apply=None, job_description=None, job_requirements=None)
                    #save_jobs(db,company_name,job_title, job_salary, location, url, skills, job_type)
                    print(f" {i+1},Company:{company_name}, Job_Title:{job_title}, Salary:{job_salary}, Skills:{skills}, Location:{location_address}, Reference:{url}, Job_type:{job_type}")           
                    time.sleep(1)
                    driver.find_element(By.CSS_SELECTOR, 'body').send_keys(Keys.ARROW_DOWN)
                    logging.info(f"Job saved: {job_title}")
                    print(i)
                    job_count+=1
                    time.sleep(5)
            driver.quit()
            return job_count
    elif location is  None and job_title is not None:
            if 'United States of America':
                location = 'United States of America'
                time.sleep(10)
                search_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="txtKey"]')))
                if job_title is not  None:
                    search_input.send_keys(job_title)
                    search_input.send_keys(Keys.ENTER)   
                    print(f"Entered job title: {job_title}")
                    time.sleep(10)  
                    #logging.exception(f"Error occurred while searching job title: {str(e)}") 
                    job_count = 0
                    for i in range(1,50):        
                        time.sleep(10)            
                        jobs = driver.find_elements(By.ID,'JobDetailPanel') 
                        time.sleep(15)
                        for job in jobs:
                            job_title = job.find_element(By.ID, 'td_jobpositionlink').text
                            time.sleep(5)
                            company_name = job.find_element(By.XPATH, '//*[@id="md_recruiter"]/a/span/span').text 
                            time.sleep(5)
                            job_type = job.find_element(By.ID, 'td_job_type').get_attribute("textContent")
                            time.sleep(5)
                            try:
                                job_salary = job.find_element(By.XPATH, '//*[@id="md_rate"]').get_attribute("textContent")
                                time.sleep(5)
                            except StaleElementReferenceException:
                                job_salary = ''
                            except NoSuchElementException:
                                job_salary = 'not stated'

                            skills = job.find_element(By.ID, 'md_skills').get_attribute('textContent')
                            time.sleep(5)
                            skills = skills.split('\n')
                            location_address = job.find_element(By.ID,'md_location').get_attribute('textContent')
                            time.sleep(5)
                            url = job.find_element(By.ID, "md_permalink").get_attribute("href")
                            time.sleep(5)

                            save_jobs(db, company_name=company_name, job_title=job_title, job_salary=job_salary, location=location_address, url=url, skills=skills, job_type=job_type, is_easy_apply=None, job_description=None, job_requirements=None)
                            #save_jobs(db,company_name,job_title, job_salary, location, url, skills, job_type)
                            print(f" {i+1},Company:{company_name}, Job_Title:{job_title}, Salary:{job_salary}, Skills:{skills}, Location:{location_address}, Reference:{url}, Job_type:{job_type}")           
                            time.sleep(1)
                            driver.find_element(By.CSS_SELECTOR, 'body').send_keys(Keys.ARROW_DOWN)
                            logging.info(f"Job saved: {job_title}")
                            print(i)
                            job_count+=1
                            time.sleep(5)
                    driver.quit()

                    return job_count
    else:
            if 'United States of America':
                location = 'United States of America'
                time.sleep(10)
                search_btn = driver.find_element(By.ID,'btnSearch')
                if search_btn:
                    search_btn.click()
                    time.sleep(5)
                    job_count = 0
                    for i in range(1,50):        
                        time.sleep(10)            
                        jobs = driver.find_elements(By.ID,'JobDetailPanel') 
                        time.sleep(15)
                        for job in jobs:
                            job_title = job.find_element(By.ID, 'td_jobpositionlink').text
                            time.sleep(5)
                            company_name = job.find_element(By.XPATH, '//*[@id="md_recruiter"]/a/span/span').text 
                            time.sleep(5)
                            job_type = job.find_element(By.ID, 'td_job_type').get_attribute("textContent")
                            time.sleep(5)
                            try:
                                job_salary = job.find_element(By.XPATH, '//*[@id="md_rate"]').get_attribute("textContent")
                                time.sleep(5)
                            except StaleElementReferenceException:
                                job_salary = ''
                            except NoSuchElementException:
                                job_salary = 'not stated'

                            skills = job.find_element(By.ID, 'md_skills').get_attribute('textContent')
                            time.sleep(5)
                            skills = skills.split('\n')
                            location_address = job.find_element(By.ID,'md_location').get_attribute('textContent')
                            time.sleep(5)
                            url = job.find_element(By.ID, "md_permalink").get_attribute("href")
                            time.sleep(5)

                            save_jobs(db, company_name=company_name, job_title=job_title, job_salary=job_salary, location=location_address, url=url, skills=skills, job_type=job_type, is_easy_apply=None, job_description=None, job_requirements=None)
                            #save_jobs(db,company_name,job_title, job_salary, location, url, skills, job_type)
                            print(f" {i+1},Company:{company_name}, Job_Title:{job_title}, Salary:{job_salary}, Skills:{skills}, Location:{location_address}, Reference:{url}, Job_type:{job_type}")           
                            time.sleep(1)
                            driver.find_element(By.CSS_SELECTOR, 'body').send_keys(Keys.ARROW_DOWN)
                            logging.info(f"Job saved: {job_title}")
                            print(i)
                            job_count+=1
                            time.sleep(5)
                    driver.quit()
                    return job_count
            