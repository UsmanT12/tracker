from database_funcs import *
from url_funcs import get_boxscore_links
from config import *

#Script to store box score stats into postgres database
# TODO: Add ability to change year for schedule
def main():
    box_scorelinks = get_boxscore_links(SCHEDULE_URL)
    for url in box_scorelinks:
        insert_game_data(url)
   
if __name__ == '__main__':
    main()