from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from pynput.keyboard import Controller, Key
from selenium.webdriver.support.ui import WebDriverWait,Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException,StaleElementReferenceException
import time
import os
import pandas as pd

# Define constants
GLASSDOOR_URL = "https://www.glassdoor.com/index.htm"
KEYWORD = "data scientist"
NUM_PAGES = 6
CSV_FILENAME = 'data_scientist_jobs.csv'

# Get login credentials from environment variables
Gd_user = os.environ.get('GLASSDOOR_USER')
Gd_password = os.environ.get('GLASSDOOR_PASSWORD')

# Define a function to setup the driver
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options, service=Service(ChromeDriverManager().install()))
    driver.implicitly_wait(3)
    return driver

# Define a function to perform the login
def login_glassdoor(driver):
    if Gd_user and Gd_password:
        url = "https://www.glassdoor.com/index.htm"
        driver.get(url)
        time.sleep(1)
        
        username_field = driver.find_element(By.NAME, "username")
        username_field.send_keys(Gd_user)

        cntd_with_email_btn = driver.find_element(By.XPATH, '//*[@id="InlineLoginModule"]/div/div/div[1]/div/div/div/div/form/div[2]/button')
        cntd_with_email_btn.click()
        time.sleep(0.1)

        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(Gd_password)
        time.sleep(0.1)
    
        login_btn = driver.find_element(By.XPATH, '//*[@id="InlineLoginModule"]/div/div/div[1]/div/div/div/div/form/div[2]/button')
        login_btn.click()
        time.sleep(1)
    else:
        print("Login credentials not found in environment variables.")
    return
    
def search_job(driver,keyword, scroll_count=1):
    Job = driver.find_element(By.XPATH, '//*[@id="ContentNav"]/li[2]/a')
    for _ in range(scroll_count):
        try:
            Job.click()  
            time.sleep(1) 
            Job.send_keys(Keys.ARROW_RIGHT)  
            time.sleep(1)  
        except StaleElementReferenceException:
            # If the element becomes stale, find it again
            Job = driver.find_element(By.XPATH, '//*[@id="ContentNav"]/li[2]/a')
            time.sleep(1)
        try:
    
            reloadlink = driver.find_element(By.LINK_TEXT,'reload')
            reloadlink.click()
        except:
            pass
            time.sleep(1)
        try:
            search_input = driver.find_element(By.ID,'sc.keyword')
            search_input.send_keys("data scientist")
            search_input.send_keys(Keys.ENTER)
            time.sleep(1)
        except:
            pass
def job_reference(driver,num):   
     
    try:
        Link = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH,f'//*[@id="MainCol"]/div[1]/ul/li[{num}]/div/div/a')))
        return Link.get_attribute('href')
    except:                                                            
        pass
        
def has_easy_apply(driver):
    try:
        # Check if the Easy Apply button exists
         driver.find_element(By.XPATH, '//*[@id="JDCol"]/div/article/div/div[1]/div/div/div[1]/div[3]/div[2]/div/div[1]/button')
         return True
    except:
        pass    
    try:
        driver.find_element(By.XPATH,'//*[@id="JDCol"]/div/article/div/div[1]/div/div/div[1]/div[3]/div[2]/div/div[1]/a') 
        return False
    except NoSuchElementException:
        pass

             
def fetch_jobs(driver, keyword, num_pages):
    url = "https://www.glassdoor.com/Job/united-states-data-scientist-jobs-SRCH_IL.0,13_IN1_KO14,28.htm?"
    driver.get(url)
    time.sleep(1)
    
    
    job_data = []


    current_page = 1
    

    while current_page <= num_pages: 
        done = False
        while not done:
            job_cards = driver.find_elements(By.XPATH, "//article[@id='MainCol']//ul/li[@data-adv-type='GENERAL']")
            for card in range(len(job_cards)):
                job_entry = {}
                job_cards[card].click()
                time.sleep(1)
                
                try:
                   Show_More = driver.find_element(By.XPATH,'//*[@id="JobDescriptionContainer"]/div[2]')
                   Show_More.click()
                   time.sleep(1)
                except NoSuchElementException:
                  print('#ERROR: no such element')
                time.sleep(1)
                try:
                 driver.find_element(By.XPATH,'//*[@id="JobDescriptionContainer"]/div[2]').click()
                 time.sleep(0.1)
                except ElementNotInteractableException:
                    Show_More.click()
                    driver.implicitly_wait(1)
                    print('#ERROR: not interactable')
                    driver.find_element(By.XPATH,'//*[@id="JobDescriptionContainer"]/div[2]').click()
                    time.sleep(1)

                
                try:
                    job_entry['company'] = driver.find_element(By.XPATH, '//*[@id="JDCol"]/div/article/div/div[1]/div/div/div[1]/div[3]/div[1]/div[1]/div').text
                    job_entry['job title'] = driver.find_element(By.XPATH, '//*[@id="JDCol"]/div/article/div/div[1]/div/div/div[1]/div[3]/div[1]/div[2]').text   
                    job_entry['location'] = driver.find_element(By.XPATH, '//*[@id="JDCol"]/div/article/div/div[1]/div/div/div[1]/div[3]/div[1]/div[3]').text
                    job_entry['job description'] = driver.find_element(By.XPATH, '//*[@id="JobDescriptionContainer"]').text
                    job_entry['salary estimate'] = driver.find_element(By.XPATH, '//*[@id="JDCol"]/div/article/div/div[2]/div[1]/div[2]/div/div/div[2]/div[1]').text
                    job_entry['job_reference'] = job_reference (driver,card+1)
                    job_entry['has_easy_apply'] = has_easy_apply(driver) 
                except NoSuchElementException:                            
                                        
                      pass                                             
                        
                try:                                  
                                                   
                      job_data.append(job_entry)              
                      
                    
                except:
                    # Handle exceptions
                      pass

            
            
                done = True  # Set done to True after processing all job cards
        
        if done:
            print(str(current_page) + ' out of ' + str(num_pages) + ' pages done')
            next_button = driver.find_element(By.XPATH, '//*[@id="MainCol"]/div[2]/div/div[1]/button[7]')
            next_button.click()
            current_page = current_page + 1          
            time.sleep(4)

            
    df = pd.DataFrame(job_data)
    return pd.DataFrame(job_data)


def apply_for_job(driver):
    url = ("https://www.glassdoor.com/Job/united-states-jobs") 
    driver.get(url)
    time.sleep(1)          
    
    #closes jobalert prompt
    try:
        More = driver.find_element(By.XPATH,'//*[@id="JAModal"]/div/div[2]/span')
        More.click()
        time.sleep(3)
    except NoSuchElementException:
        print('#ERROR: no such element')
        time.sleep(5)
    try:
        driver.find_element(By.XPATH,'//*[@id="JAModal"]/div/div[2]/span').click()
        time.sleep(2)
    except ElementNotInteractableException:
        More.click()
        driver.implicitly_wait(1)
        print('#ERROR: not interactable')
        driver.find_element(By.XPATH,'//*[@id="JAModal"]/div/div[2]/span').click()
        time.sleep(1)
    except:
        pass 

    #selects filter
    try:
        More = driver.find_element(By.XPATH,'//*[@id="DKFilters"]/div/div[1]/div[2]/div[1]/span[1]')
        More.click()
        time.sleep(1)
    except NoSuchElementException:
        print('#ERROR: no such element')
        time.sleep(1)
    try:
        driver.find_element(By.XPATH,'//*[@id="DKFilters"]/div/div[1]/div[2]/div[2]/div[14]/label/div').click()
        time.sleep(1)
    except ElementNotInteractableException:
        More.click()
        driver.implicitly_wait(1)
        print('#ERROR: not interactable')
        driver.find_element(By.XPATH,'//*[@id="DKFilters"]/div/div[1]/div[2]/div[1]/span[1]').click()
        time.sleep(1)
    try:
        apply_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="JDCol"]/div/article/div/div[1]/div/div/div[1]/div[3]/div[2]/div/div[1]/button')))
        apply_button.click()               
        time.sleep(1)
    except:                       
        pass   
    initial_handle = driver.current_window_handle
    while len(driver.window_handles) == 1:
        time.sleep(1)

    new_handle = [handle for handle in driver.window_handles if handle != initial_handle][0]
    driver.switch_to.window(new_handle)
    WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    print("Switched to new window")
 
    try:
        Resume = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ia-container"]/div/div/div/main/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[1]/div/div')))
        Resume.click()
        time.sleep(1)
    except:
        pass
    try:
        keyboard = Controller()

        keyboard.type("C:\\Users\\AmazingTech\\VICTORIA DAPPA GREAT.pdf")
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        time.sleep(1)
    except:
       pass
    try:
        Continue = driver.find_element(By.XPATH,'//*[@id="ia-container"]/div/div/div/main/div[2]/div[2]/div/div/div[2]/div/button/div')
        Continue.click()                        
        time.sleep(0.1) 
    except:
        pass
    try:
        Address = driver.find_element(By.XPATH,'//*[@id="input-q_202cbd7d315e5270ef14e379b642eab9"]')
        Address.send_keys("Apapa, Lagos State")
        time.sleep(0.1)
    except:
        pass
    try:
        Zipcode = driver.find_element(By.XPATH,'//*[@id="input-q_91854e63880f55c119b18f3e53c8cdda"]')
        Zipcode.send_keys("100011")
        time.sleep(0.1)
    except:
        pass
    try:
         Previous_employment = driver.find_element(By.XPATH,'//*[@id="input-q_fdaa0b921dfc703ee2244cc048806521"]/label[2]/span[1]')
         Previous_employment.click()
         time.sleep(0.1)
    except:
        pass
    try:
        Employed_relatives = driver.find_element(By.XPATH,'//*[@id="input-q_da5427dee089aa7dd7ec455e3964a75e"]/label[2]/span[1]')
        Employed_relatives.click()
        time.sleep(0.1)
    except:
        pass
    try:
        Visa_sponsorship = driver.find_element(By.XPATH,'//*[@id="input-q_cb1c577cc81bd61827427533b116f5b5"]/label[1]/span[1]')
        Visa_sponsorship.click()
        time.sleep(0.1)
    except:
        pass
    try:
         Terms_condition = driver.find_element(By.XPATH,'//*[@id="input-q_c3f6e381a3adf3329bdbaf1877f59581"]/label/span[1]')
         Terms_condition.click()
         time.sleep(0.1)
    except:
        pass
    try:
        Disability_radio = driver.find_element(By.XPATH,'//*[@id="input-q_86efe02c248de0b75e20cf14449c9af9"]/label[2]/span[1]')
        Disability_radio.click()
        time.sleep(0.1)
    except:
        pass
    try:
         Veteran_radio = driver.find_element(By.XPATH,'//*[@id="input-q_14dc0d97e570c98a544ed5f2db668d6d"]/label[3]/span[1]')
         Veteran_radio.click()
         time.sleep(0.1)
    except:
        pass
    try:
         Continue = driver.find_element(By.XPATH,'//*[@id="ia-container"]/div/div/div/main/div[2]/div[2]/div/div/div[2]/div/button/div')
         Continue.click()
         time.sleep(0.1)
    except:
        pass
    try:
        Resume = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ia-container"]/div/div/div/main/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[1]/div/div')))
        Resume.click()
        time.sleep(1)
    except:
        pass
    try:
        keyboard = Controller()

        keyboard.type("C:\\Users\\AmazingTech\\VICTORIA DAPPA GREAT.pdf")
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        time.sleep(1)
    except:
       pass
    try:
        Continue = driver.find_element(By.XPATH,'//*[@id="ia-container"]/div/div/div/main/div[2]/div[2]/div/div/div[2]/div/button/div')
        Continue.click()                        
        time.sleep(1) 
    except:
        pass
    try:
        Mass_commknowledge = driver.find_element(By.XPATH,'//*[@id="input-q_e7f0721c5e6c49cdd9e91ddfd774d77f"]/label[2]/span[1]')
        Mass_commknowledge.click()
        time.sleep(0.1)
    except:
        pass
    try:
         Race = driver.find_element(By.XPATH, '//*[@id="input-q_2cf00e356ba66c3306ac7388bd5d3df6"]')
         drp = Select(Race)
         drp.select_by_index(6)
         time.sleep(1)
    except:
        pass
    try:
        Gender = driver.find_element(By.XPATH,'//*[@id="input-q_a2bda3afb7844cb43cf5e84f6093f3b4"]/label[2]/span[1]')
        Gender.click()
        time.sleep(1)
    except Exception as e:
        print(f"Failed to fill details due to: {str(e)}")

    try:
        Submit = driver.find_element(By.XPATH, '//*[@id="ia-container"]/div/div/div/main/div[2]/div[2]/div/div/div[2]/div/button/div')
        Submit.click()
        time.sleep(1)
    except:
        pass

        # Switch back to the main window
    try:
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(0.1)
    except Exception as e:
        print(f"Failed to fill details due to: {str(e)}")

# Usage
def main():
    driver_instance = setup_driver()
    login_glassdoor(driver_instance)
    search_job(driver_instance, KEYWORD)
    #apply_for_job(driver_instance)
    df = fetch_jobs(driver_instance, KEYWORD, NUM_PAGES)
    df.to_csv(CSV_FILENAME, index=False)
    
    print("Job data saved to CSV.")
    print("Printing CSV contents:")
    print(df)
    driver_instance.close()

if __name__ == "__main__":
    main()
