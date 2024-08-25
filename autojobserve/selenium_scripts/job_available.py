import os
import re

from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc


def check_job(joblink):
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--disable-gpu")
    #driver = uc.Chrome(options=chrome_options)
    driver = webdriver.Remote(
        command_executor="http://selenium-hub:4444/wd/hub",
        desired_capabilities=DesiredCapabilities.EDGE)
    #driver.maximize_window() #maximize window size

    driver.implicitly_wait(30)

    #get the url
    driver.get(joblink)

    my_current_url = driver.current_url
    
    driver.quit()
    return my_current_url


    