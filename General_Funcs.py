from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_utils import get_webdriver
from players import *
from datetime import datetime, timedelta

# Global variables to store xpaths for team names and box score tables
TEAM_NAME_PATH = '_TeamName__name_1k5qz_11'
BOX_SCORE_TABLE_PATH = 'BoxScore_BoxScore__table__62P7f'

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
    date = (f'{date_element.text.strip()}')
    date = convert_date(date)
    
    team1_arr = team_player_stats(team1_table, players, date, team1_name)
    team2_arr = team_player_stats(team2_table, players, date, team2_name)

    # print_player_stats(team1_table, Team_dict[team1_name])
    # print_player_stats(team2_table, Team_dict[team2_name])
    
    driver.quit()
    return team1_arr, team2_arr
    
    
def team_player_stats(table, player_names_list, date, team_name):
    rows = table.find_elements(By.TAG_NAME, 'tr')
    headers = [header.text.strip() for header in rows[0].find_elements(By.TAG_NAME, 'th')]
    team_array = []
    
    # First, get all players from the box score
    boxscore_players = get_boxscore_players(rows, headers)
    
    # Then, find matches between box score players and your player list
    for boxscore_player_name, stats in boxscore_players.items():
        # Check if this box score player matches anyone in your player list
        matching_player = find_matching_player(boxscore_player_name, player_names_list)
        if matching_player:
            stats['PLAYER'] = matching_player  # Use your standardized player name
            stats['TEAM'] = team_name
            stats['DATE'] = date
            stats = convert_data(stats)
            team_array.append(stats)
    
    return team_array

# Gets all players from the box score with their stats
def get_boxscore_players(rows, headers):
    boxscore_players = {}
    
    # Skip the header row (index 0)
    for row in rows[1:]:
        # Only process rows that have data cells (td)
        if row.find_elements(By.TAG_NAME, 'td'):
            # Get all stats for this player
            player_stats = row.find_elements(By.TAG_NAME, 'td')
            
            # Create dictionary with header keys and stat values
            player_dict = {headers[i]: player_stats[i].text.strip() for i in range(len(headers))}
            
            # The player name is typically the first column, but check if it exists
            player_name = player_dict.get('PLAYER', '')
            if player_name:
                boxscore_players[player_name] = player_dict
    
    return boxscore_players

# Find a matching player name between box score and your list
def find_matching_player(boxscore_name, player_names_list):
    # Try exact match first
    if boxscore_name in player_names_list:
        return boxscore_name
    
    # Try case-insensitive match
    for player_name in player_names_list:
        if player_name.lower() == boxscore_name.lower():
            return player_name
    
    # No match found
    return None

# Returns stats of players from a team in array format
# def team_player_stats(table, player_names, date, team_name):
#     rows = table.find_elements(By.TAG_NAME, 'tr')
#     headers = [header.text.strip() for header in rows[0].find_elements(By.TAG_NAME, 'th')]
#     team_array = []
    
#     for player_name in player_names:
#         player_stats = get_player_stats(player_name, rows, headers)
#         player_stats['TEAM'] = team_name
#         player_stats['DATE'] = date
#         player_stats = convert_data(player_stats)
#         team_array.append(player_stats)

#     return team_array

# # prints the dictionary of each player's stats
# # used for debugging puposes
# def print_player_stats(table, player_names):
#     rows = table.find_elements(By.TAG_NAME, 'tr')
#     headers = [header.text.strip() for header in rows[0].find_elements(By.TAG_NAME, 'th')]

#     for player_name in player_names:
#         player_stats = get_player_stats(player_name, rows, headers)
#         print(player_stats['PLAYER'])
#         print(player_stats, '\n')

# # Gets the stats of a player from box score table and returns the stats as a dictionary
# def get_player_stats(player_name, rows, headers):
#     player_rows = [row for row in rows if player_name in row.text]
#     if not player_rows:
#         player_dict = {'PLAYER': player_name}
#         return player_dict
    
#     player_row = player_rows[0]
#     player_stats = player_row.find_elements(By.TAG_NAME, 'td')
#     player_dict = {headers[i]: player_stats[i].text.strip() for i in range(len(headers))}

#     return player_dict
    

def convert_date(date_str):
    # date_str is expected Friday, May 24, 2024
    cleaned_date_str = date_str.replace(',', '')
    parts = cleaned_date_str.split()
    parts[1] = months[parts[1]]
    converted_date = f"{parts[3]}-{parts[1]:02d}-{parts[2]}"
    
    return converted_date

def convert_data(player_dict):
    """
    Converts player dictionary data to a database-friendly format with proper types.
    Handles missing fields and provides safe defaults while preserving original data names.
    """
    if 'PLAYER' not in player_dict or len(player_dict) <= 2:
        return {
            'PLAYER': player_dict.get('PLAYER', ''),
            'TEAM': player_dict.get('TEAM', ''),
            'DATE': player_dict.get('DATE', None),
            'MIN': timedelta(minutes=0),
            'FGM-A': '0-0', 'FG%': 0.0,
            '3PM-A': '0-0', '3P%': 0.0,
            'FTM-A': '0-0', 'FT%': 0.0,
            '+/-': 0, 'OREB': 0, 'DREB': 0, 'REB': 0,
            'AST': 0, 'PF': 0, 'STL': 0, 'TO': 0, 'BS': 0, 'PTS': 0
        }

    def safe_time(time_str):
        try:
            if ':' in str(time_str):
                mins, secs = time_str.split(':')
                return timedelta(minutes=int(mins), seconds=int(secs))
            return timedelta(minutes=int(time_str))
        except (ValueError, AttributeError):
            return timedelta(minutes=0)

    def safe_float(value, default=0.0):
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def safe_int(value, default=0):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    date_value = player_dict.get('DATE', None)
    if isinstance(date_value, str):
        try:
            date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
        except ValueError:
            pass

    return {
        'PLAYER': player_dict.get('PLAYER', ''),
        'TEAM': player_dict.get('TEAM', ''),
        'DATE': date_value,
        'MIN': safe_time(player_dict.get('MIN', '0')),
        'FGM-A': player_dict.get('FGM-A', '0-0'),
        'FG%': safe_float(player_dict.get('FG%', 0)),
        '3PM-A': player_dict.get('3PM-A', '0-0'),
        '3P%': safe_float(player_dict.get('3P%', 0)),
        'FTM-A': player_dict.get('FTM-A', '0-0'),
        'FT%': safe_float(player_dict.get('FT%', 0)),
        '+/-': safe_int(player_dict.get('+/-', 0)),
        'OREB': safe_int(player_dict.get('OREB', 0)),
        'DREB': safe_int(player_dict.get('DREB', 0)),
        'REB': safe_int(player_dict.get('REB', 0)),
        'AST': safe_int(player_dict.get('AST', 0)),
        'PF': safe_int(player_dict.get('PF', 0)),
        'STL': safe_int(player_dict.get('STL', 0)),
        'TO': safe_int(player_dict.get('TO', 0)),
        'BS': safe_int(player_dict.get('BS', 0)),
        'PTS': safe_int(player_dict.get('PTS', 0))
    }