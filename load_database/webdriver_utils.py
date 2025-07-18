from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from config import CHROME_DRIVER_PATH

def get_webdriver():
    service = Service(executable_path=CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service)
    return driver