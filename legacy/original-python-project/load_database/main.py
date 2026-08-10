import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from database_funcs import *
from url_funcs import get_boxscore_links
import config

#Script to store box score stats into postgres database
# TODO: Add ability to change year for schedule
def main():
    box_scorelinks = get_boxscore_links(SCHEDULE_URL)
    for url in box_scorelinks:
        insert_game_data(url)
   
if __name__ == '__main__':
    main()