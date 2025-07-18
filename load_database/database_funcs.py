from config import *
import psycopg2
from General_Funcs import populate_box_score_table

def single_print_data(url):
    team1_stats, team2_stats = populate_box_score_table(url)
    for i in range(len(team1_stats)):
        print(f"Team 1 Player {i+1} Stats: {team1_stats[i]} \n")
    for i in range(len(team2_stats)):
        print(f"Team 2 Player {i+1} Stats: {team2_stats[i]} \n")
    
def insert_game_data(url):
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    cursor = conn.cursor()

    team1_stats, team2_stats = populate_box_score_table(url)
    
    # Insert each player's stats
    for player_data in team1_stats + team2_stats:
        # Function to split shot attempts into made and attempted
        def split_shots(shot_string, default=(0,0)):
            try:
                if '-' in shot_string:
                    made, attempted = map(int, shot_string.split('-'))
                    return made, attempted
                return default
            except (ValueError, TypeError):
                return default
        
        # Split the shot values
        fgm, fga = split_shots(player_data.get('FGM-A', '0-0'))
        tpm, tpa = split_shots(player_data.get('3PM-A', '0-0'))
        ftm, fta = split_shots(player_data.get('FTM-A', '0-0'))
        
        # Create a new dictionary with clean keys for SQL parameters
        clean_data = {
            'player': player_data.get('PLAYER', ''),
            'team': player_data.get('TEAM', ''),
            'date': player_data.get('DATE', None),
            'min': player_data.get('MIN', '0'),
            'fgm': fgm,
            'fga': fga,
            'fgpct': player_data.get('FG%', 0),
            'tpm': tpm,
            'tpa': tpa,
            'tppct': player_data.get('3P%', 0),
            'ftm': ftm,
            'fta': fta,
            'ftpct': player_data.get('FT%', 0),
            'plusminus': player_data.get('+/-', 0),
            'oreb': player_data.get('OREB', 0),
            'dreb': player_data.get('DREB', 0),
            'reb': player_data.get('REB', 0),
            'ast': player_data.get('AST', 0),
            'pf': player_data.get('PF', 0),
            'stl': player_data.get('STL', 0),
            'tov': player_data.get('TO', 0),
            'blk': player_data.get('BS', 0),
            'pts': player_data.get('PTS', 0)
        }
        
        cursor.execute("""
            INSERT INTO player_stats (
                player, team, game_date, minutes, 
                fgm, fga, fg_pct, tpm, tpa, tp_pct, 
                ftm, fta, ft_pct, plus_minus, 
                oreb, dreb, reb, ast, pf, stl, tov, blk, pts
            ) 
            VALUES (
                %(player)s, %(team)s, %(date)s, %(min)s, 
                %(fgm)s, %(fga)s, %(fgpct)s, %(tpm)s, %(tpa)s, %(tppct)s, 
                %(ftm)s, %(fta)s, %(ftpct)s, %(plusminus)s,
                %(oreb)s, %(dreb)s, %(reb)s, %(ast)s, %(pf)s, 
                %(stl)s, %(tov)s, %(blk)s, %(pts)s
            )
            ON CONFLICT (player, team, game_date) 
            DO UPDATE SET
                minutes = EXCLUDED.minutes,
                fgm = EXCLUDED.fgm,
                fga = EXCLUDED.fga,
                fg_pct = EXCLUDED.fg_pct,
                tpm = EXCLUDED.tpm,
                tpa = EXCLUDED.tpa,
                tp_pct = EXCLUDED.tp_pct,
                ftm = EXCLUDED.ftm,
                fta = EXCLUDED.fta,
                ft_pct = EXCLUDED.ft_pct,
                plus_minus = EXCLUDED.plus_minus,
                oreb = EXCLUDED.oreb,
                dreb = EXCLUDED.dreb,
                reb = EXCLUDED.reb,
                ast = EXCLUDED.ast,
                pf = EXCLUDED.pf,
                stl = EXCLUDED.stl,
                tov = EXCLUDED.tov,
                blk = EXCLUDED.blk,
                pts = EXCLUDED.pts
        """, clean_data)
    
    conn.commit()
    cursor.close()
    conn.close()

    if team1_stats and team2_stats:
        print(f'Successfully added {team1_stats[0]["TEAM"].upper()} vs {team2_stats[0]["TEAM"].upper()} on {team1_stats[0]["DATE"]}')
