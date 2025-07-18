import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_utils import get_webdriver
from config import SCHEDULE_URL
import time

#Returns boxscore links from WNBA schedule page, given the url
def get_boxscore_links(url):
        
    driver = get_webdriver()
    driver.get(url)
        
    all_game_cards = []
    # Scroll loop to collect game cards
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Wait for new content to load

        new_height = driver.execute_script("return document.body.scrollHeight")
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'GameSection_GameSection__CDIMc'))
        )
        game_cards = driver.find_elements(By.CLASS_NAME, '_GameTile__container_12tan_23')
        all_game_cards.extend(game_cards)
        
        if new_height == last_height:
            break
        last_height = new_height
    all_game_cards = list(set(all_game_cards))

    boxscore_links = []

    for game in all_game_cards:
        link_element = game.find_element(By.CLASS_NAME, "_GameTile__game_12tan_30")
        link = link_element.get_attribute("href") + '/boxscore'
        boxscore_links.append(link)

    print(f"Number of Boxscore Links: {len(boxscore_links)}")
    driver.quit()
    
    return boxscore_links