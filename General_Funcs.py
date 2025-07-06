from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_utils import get_webdriver
from players import players, Team_dict

# Global variables to store xpaths for team names and box score tables
TEAM_NAME_PATH = '_TeamName__name_1k5qz_11'
BOX_SCORE_TABLE_PATH = 'BoxScore_BoxScore__table__62P7f'

#TODO: make stats into a returnable value instead of printing them
def populate_box_score_table(url):
    driver = get_webdriver()
    driver.get(url)

    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, BOX_SCORE_TABLE_PATH))
    )
    box_score_tables = driver.find_elements(By.CLASS_NAME, BOX_SCORE_TABLE_PATH)
    
    team_names = driver.find_elements(By.CLASS_NAME, TEAM_NAME_PATH)
    team_names_text = [team.text for team in team_names]
    if team_names_text:
        team1_name = team_names_text[-1]
        team2_name = team_names_text[-2]
        team1_table = box_score_tables[1]
        team2_table = box_score_tables[0]
    else:
        print('No team names found.')
        return
    
    date_element = driver.find_element(By.CLASS_NAME, '_GameStatusExpanded__date_so8ca_12')
    if date_element:
        print(f'Game Date: {date_element.text.strip()}')
    
    print(f'{team1_name} Team Stats:')
    print_player_stats(team1_table, Team_dict[team1_name])

    print(f'{team2_name} Team Stats:')
    print_player_stats(team2_table, Team_dict[team2_name])

    driver.quit()

# prints the dictionary of each player's stats
# used for debugging puposes
def print_player_stats(table, player_names):
    rows = table.find_elements(By.TAG_NAME, 'tr')
    headers = [header.text.strip() for header in rows[0].find_elements(By.TAG_NAME, 'th')]

    for player_name in player_names:
        player_stats = get_player_stats(player_name, rows, headers)
        print(player_stats['PLAYER'])
        print(player_stats, '\n')

# Gets the stats of a player from box score table and returns the stats as a dictionary
def get_player_stats(player_name, rows, headers):
    player_rows = [row for row in rows if player_name in row.text]
    if not player_rows:
        player_dict = {'PLAYER': player_name}
        return player_dict
    
    player_row = player_rows[0]
    player_stats = player_row.find_elements(By.TAG_NAME, 'td')
    player_dict = {headers[i]: player_stats[i].text.strip() for i in range(len(headers))}
    
    return player_dict