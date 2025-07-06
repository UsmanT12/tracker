from General_Funcs import populate_box_score_table
from url_funcs import get_boxscore_links
from config import *

#Script to store box score stats into postgres database
def main():
    box_scorelinks = get_boxscore_links(SCHEDULE_URL)
    for url in box_scorelinks:
        populate_box_score_table(url)
    
    
    #TODO create a script to store stats from populate_box_score_table into postgres database
    
if __name__ == '__main__':
    main()