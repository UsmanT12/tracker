import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import calendar
import psycopg2
import config


def _is_dnp(minutes):
    """Return True when a stored minutes value represents zero playing time."""
    if minutes is None:
        return True
    if isinstance(minutes, timedelta):
        return minutes.total_seconds() == 0

    value = str(minutes).strip()
    if not value:
        return True

    try:
        return all(float(part) == 0 for part in value.split(':'))
    except ValueError:
        return False


def show_player_fg_pct_calendar(player_name=None):
    """
    Display a player's field goal percentage across games in a calendar heatmap format.
    If no player is specified, asks for input.
    """
    conn = psycopg2.connect(
        host=config.DB_HOST,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        port=config.DB_PORT
    )
    
    cursor = conn.cursor()
    
    # If no player specified, get a list of players and ask user to select one
    if player_name is None:
        cursor.execute("SELECT DISTINCT player FROM player_stats ORDER BY player")
        players = [row[0] for row in cursor.fetchall()]
        
        print("Available players:")
        for i, player in enumerate(players):
            print(f"{i+1}. {player}")
        
        selection = int(input("Enter player number: ")) - 1
        player_name = players[selection]
    
    # Query to get game dates, FG%, attempts, minutes for the selected player
    cursor.execute("""
        SELECT game_date, fg_pct, fgm, fga, team, minutes
        FROM player_stats 
        WHERE player = %s 
        ORDER BY game_date
    """, (player_name,))
    
    games = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not games:
        print(f"No games found for {player_name}")
        return
    
    # Convert to pandas DataFrame for easier manipulation
    df = pd.DataFrame(games, columns=['date', 'fg_pct', 'fgm', 'fga', 'team', 'minutes'])
    
    # Create figure with calendar-style subplots
    first_date = df['date'].min()
    last_date = df['date'].max()
    
    # Calculate the number of months to display
    num_months = (last_date.year - first_date.year) * 12 + last_date.month - first_date.month + 1
    
    # Instead of one long figure, organize months in a grid (max 3 columns)
    cols = min(3, num_months)
    rows = (num_months + cols - 1) // cols  # Ceiling division
    
    # Set up the figure with a more balanced layout
    fig = plt.figure(figsize=(15, 4 * rows))
    
    # Get the max FG% for color scaling (cap at 100%)
    # Filter out games where player didn't attempt any shots
    shooting_games = df[df['fga'] > 0]
    if len(shooting_games) > 0:
        # FG% is stored as a decimal (0-1), convert to 0-100 scale for display
        max_fg_pct = 100.0  # Always cap at 100%
    else:
        max_fg_pct = 100.0
    
    # Process each month
    current_date = datetime(first_date.year, first_date.month, 1).date()
    
    for i in range(num_months):
        # Create a subplot in a grid layout
        ax = fig.add_subplot(rows, cols, i + 1)
        
        year = current_date.year
        month = current_date.month
        
        # Create calendar layout
        cal = calendar.monthcalendar(year, month)
        
        # Create heatmap data
        cal_data = np.zeros((len(cal), 7))
        cal_data[:] = np.nan  # Set to NaN so empty days are white
        
        # Filter data for current month
        month_start = current_date
        if month == 12:
            month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        month_data = df[(df['date'] >= month_start) & (df['date'] <= month_end)]
        
        # Fill in FG% data
        for _, game in month_data.iterrows():
            day = game['date'].day
            for week_idx, week in enumerate(cal):
                if day in week:
                    day_idx = week.index(day)
                    # Only use FG% for games where shots were attempted
                    if game['fga'] > 0:
                        cal_data[week_idx, day_idx] = game['fg_pct']  # Convert from 0-1 to 0-100 scale
                    else:
                        # For games with no attempts, mark differently
                        cal_data[week_idx, day_idx] = np.nan
                    break
        
        # Create heatmap with a sequential colormap (good for percentages)
        im = ax.imshow(cal_data, cmap='RdYlGn', vmin=0, vmax=max_fg_pct)
        
        # Add day numbers and FG%
        for week_idx, week in enumerate(cal):
            for day_idx, day in enumerate(week):
                if day != 0:
                    fg_pct = cal_data[week_idx, day_idx]
                    if not np.isnan(fg_pct):
                        # Add team abbreviation to make it more informative
                        game_date = datetime(year, month, day).date()
                        game_row = month_data[month_data['date'] == game_date]
                        team = game_row['team'].values[0]
                        fgm = game_row['fgm'].values[0]
                        fga = game_row['fga'].values[0]
                        
                        minutes = game_row['minutes'].values[0]
                        
                        # Format text with day, FG%, and attempts - using .1f to show one decimal place
                        fg_pct_text = f"{fg_pct:.1f}%" if fg_pct is not None else "N/A"
                        
                        # Always use black text for consistency and readability
                        text_color = 'black'
                        
                        if _is_dnp(minutes):
                            # Override cell color to grey for DNP games
                            # Create a rectangle patch with grey color
                            rect = plt.Rectangle((day_idx-0.5, week_idx-0.5), 1, 1, 
                                              fill=True, color='lightgrey', alpha=0.7, zorder=0)
                            ax.add_patch(rect)
                            text_content = f"{day}\n{fg_pct_text}\n{fgm}-{fga}\n(DNP)"
                        else:
                            text_content = f"{day}\n{fg_pct_text}\n{fgm}-{fga}"
                            
                        ax.text(day_idx, week_idx, text_content, 
                               ha='center', va='center', fontsize=8, 
                               color=text_color,
                               fontweight='bold')
                    else:
                        ax.text(day_idx, week_idx, f"{day}", ha='center', va='center', 
                               fontsize=9, color='gray')
        
        # Set labels
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        ax.set_xticks(np.arange(len(days)))
        ax.set_xticklabels(days)
        ax.set_yticks([])
        ax.set_title(f"{calendar.month_name[month]} {year}", fontweight='bold')
        
        # Add grid lines
        ax.grid(which='major', color='w', linestyle='-', linewidth=1.5)
        
        # Advance to next month
        if month == 12:
            current_date = datetime(year + 1, 1, 1).date()
        else:
            current_date = datetime(year, month + 1, 1).date()
    
    # Add a colorbar with clear percentage formatting
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])  # [left, bottom, width, height]
    cbar = fig.colorbar(im, cax=cbar_ax)
    cbar.set_label('Field Goal %', fontweight='bold')
    
    # Create tick formatter that shows percentages with one decimal place
    import matplotlib.ticker as mtick
    cbar.ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=1))
    
    # Add legend for FG% levels with correct percentage formatting
    legend_elements = [
        plt.Line2D([0], [0], marker='s', color='w', 
                  markerfacecolor=im.cmap(0.1), markersize=10, label='0-25%'),
        plt.Line2D([0], [0], marker='s', color='w', 
                  markerfacecolor=im.cmap(0.33), markersize=10, label='25-50%'),
        plt.Line2D([0], [0], marker='s', color='w', 
                  markerfacecolor=im.cmap(0.66), markersize=10, label='50-75%'),
        plt.Line2D([0], [0], marker='s', color='w', 
                  markerfacecolor=im.cmap(0.9), markersize=10, label='75-100%')
    ]
    
    # Add legend at the bottom
    fig.legend(handles=legend_elements, loc='lower center', 
              ncol=4, frameon=True, fontsize='small')
    
    plt.suptitle(f"{player_name} - Field Goal Percentage by Game", fontsize=18, fontweight='bold')
    plt.subplots_adjust(
        left=0.05, right=0.9, bottom=0.08, top=0.9,
        wspace=0.2, hspace=0.4
    )
        
    plt.show()

def show_player_points_calendar(player_name=None):
    """
    Display a player's points across games in a calendar heatmap format.
    If no player is specified, asks for input.
    """
    conn = psycopg2.connect(
        host=config.DB_HOST,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        port=config.DB_PORT
    )
    
    cursor = conn.cursor()
    
    # If no player specified, get a list of players and ask user to select one
    if player_name is None:
        cursor.execute("SELECT DISTINCT player FROM player_stats ORDER BY player")
        players = [row[0] for row in cursor.fetchall()]
        
        print("Available players:")
        for i, player in enumerate(players):
            print(f"{i+1}. {player}")
        
        selection = int(input("Enter player number: ")) - 1
        player_name = players[selection]
    
    # Query to get game dates, points, minutes, and opponent for the selected player
    cursor.execute("""
        SELECT game_date, pts, team, minutes 
        FROM player_stats 
        WHERE player = %s 
        ORDER BY game_date
    """, (player_name,))
    
    games = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not games:
        print(f"No games found for {player_name}")
        return
    
    # Convert to pandas DataFrame for easier manipulation
    df = pd.DataFrame(games, columns=['date', 'points', 'team', 'minutes'])
    
    # Calculate the season average from games in which the player appeared
    played_df = df[~df['minutes'].apply(_is_dnp)]
    avg_points = played_df['points'].mean() if not played_df.empty else 0
    
    # Create figure with calendar-style subplots
    first_date = df['date'].min()
    last_date = df['date'].max()
    
    # Calculate the number of months to display
    num_months = (last_date.year - first_date.year) * 12 + last_date.month - first_date.month + 1
    
    # Instead of one long figure, organize months in a grid (max 3 columns)
    cols = min(3, num_months)
    rows = (num_months + cols - 1) // cols  # Ceiling division
    
    # Set up the figure with a more balanced layout
    fig = plt.figure(figsize=(15, 4 * rows))
    
    # Process each month
    current_date = datetime(first_date.year, first_date.month, 1).date()
    
    # Create data for point differences from player's average
    cal_data_raw = {}  # To store raw points values
    cal_data_diff = {}  # To store difference from average
    
    for i in range(num_months):
        # Create a subplot in a grid layout
        ax = fig.add_subplot(rows, cols, i + 1)
        
        year = current_date.year
        month = current_date.month
        
        # Create calendar layout
        cal = calendar.monthcalendar(year, month)
        
        # Create heatmap data for points difference from average
        cal_data = np.zeros((len(cal), 7))
        cal_data[:] = np.nan  # Set to NaN so empty days are white
        
        # Also store raw points for display
        cal_data_points = np.zeros((len(cal), 7))
        cal_data_points[:] = np.nan
        
        # Filter data for current month
        month_start = current_date
        if month == 12:
            month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        month_data = df[(df['date'] >= month_start) & (df['date'] <= month_end)]
        
        # Fill in points data
        for _, game in month_data.iterrows():
            day = game['date'].day
            for week_idx, week in enumerate(cal):
                if day in week:
                    day_idx = week.index(day)
                    points = game['points']
                    
                    # Store raw points value
                    cal_data_points[week_idx, day_idx] = points
                    
                    # Store difference from average for coloring
                    cal_data[week_idx, day_idx] = points - avg_points
                    break
        
        # Store month data in dictionaries
        month_key = f"{year}-{month}"
        cal_data_raw[month_key] = cal_data_points
        cal_data_diff[month_key] = cal_data
        
        # Find the max deviation from average to set color scale symmetrically
        max_dev = np.nanmax(np.abs(cal_data))
        max_dev = max(max_dev, 8)  # At least 8 points deviation for visibility
        
        # Create heatmap with diverging colormap centered on player's average
        im = ax.imshow(cal_data, cmap='RdYlGn', vmin=-max_dev, vmax=max_dev)
        
        # Add day numbers and points
        for week_idx, week in enumerate(cal):
            for day_idx, day in enumerate(week):
                if day != 0:
                    pts = cal_data_points[week_idx, day_idx]
                    if not np.isnan(pts):
                        # Add team abbreviation to make it more informative
                        game_date = datetime(year, month, day).date()
                        game_row = month_data[month_data['date'] == game_date]
                        team = game_row['team'].values[0]
                        minutes = game_row['minutes'].values[0]
                        
                        # Calculate deviation from average
                        pts_diff = pts - avg_points
                        
                        # Always use black text for consistency and readability
                        text_color = 'black'
                        
                        if _is_dnp(minutes):
                            # Override cell color to grey for DNP games
                            # Create a rectangle patch with grey color
                            rect = plt.Rectangle((day_idx-0.5, week_idx-0.5), 1, 1, 
                                              fill=True, color='lightgrey', alpha=0.7, zorder=0)
                            ax.add_patch(rect)
                            text_content = f"{day}\n{int(pts)}\n(DNP)"
                        else:
                            text_content = f"{day}\n{int(pts)}"
                        
                        # Format text with day and points (team name removed)
                        ax.text(day_idx, week_idx, text_content, 
                               ha='center', va='center', fontsize=9, 
                               color=text_color,
                               fontweight='bold')
                    else:
                        ax.text(day_idx, week_idx, f"{day}", ha='center', va='center', 
                               fontsize=9, color='gray')
        
        # Set labels
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        ax.set_xticks(np.arange(len(days)))
        ax.set_xticklabels(days)
        ax.set_yticks([])
        ax.set_title(f"{calendar.month_name[month]} {year}", fontweight='bold')
        
        # Add grid lines
        ax.grid(which='major', color='w', linestyle='-', linewidth=1.5)
        
        # Advance to next month
        if month == 12:
            current_date = datetime(year + 1, 1, 1).date()
        else:
            current_date = datetime(year, month + 1, 1).date()
    
    # Add a colorbar showing deviation from player average
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])  # [left, bottom, width, height]
    cbar = fig.colorbar(im, cax=cbar_ax)
    cbar.set_label(f'Points +/- Avg ({avg_points:.1f})', fontweight='bold')
    
    # Add explanation of the color coding
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    fig.text(0.5, 0.02, f"Green = Above Average | Yellow = Near Average | Red = Below Average", 
             ha='center', va='center', bbox=props)
    
    plt.suptitle(f"{player_name} - Points by Game\nSeason Avg: {avg_points:.1f} pts", 
                fontsize=18, fontweight='bold')
    plt.subplots_adjust(
        left=0.05, right=0.9, bottom=0.1, top=0.88,
        wspace=0.2, hspace=0.4
    )
        
    plt.show()

# Move your original code to this function
def display_all_stats():
    conn = psycopg2.connect(
        host=config.DB_HOST,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        port=config.DB_PORT
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM player_stats ORDER BY player, game_date")
    
    records = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    
    print("\nPlayer Statistics:")
    print(" | ".join(column_names))
    print("-" * 100)
    
    for record in records:
        print(" | ".join(str(value) for value in record))
    
    print(f"\nTotal records: {len(records)}")
    
    cursor.close()
    conn.close()

def analyze_fg_efficiency(player_name=None, top_n=5):
    """
    Analyze field goal efficiency for a specific player or find the top/bottom shooters.
    
    Parameters:
    - player_name: If provided, shows detailed FG stats for this player. If None, shows top/bottom shooters.
    - top_n: Number of players to show in the top/bottom lists.
    """
    conn = psycopg2.connect(
        host=config.DB_HOST,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        port=config.DB_PORT
    )
    
    cursor = conn.cursor()
    
    if player_name is None:
        # Get list of players for user selection
        cursor.execute("SELECT DISTINCT player FROM player_stats ORDER BY player")
        players = [row[0] for row in cursor.fetchall()]
        
        print("\nAvailable players:")
        for i, player in enumerate(players):
            print(f"{i+1}. {player}")
        
        print("\nOr select an analysis option:")
        print(f"{len(players)+1}. Top {top_n} efficient shooters (min. 50 FGA)")
        print(f"{len(players)+2}. Bottom {top_n} efficient shooters (min. 50 FGA)")
        print(f"{len(players)+3}. Return to main menu")
        
        try:
            selection = int(input("\nEnter your selection: "))
            
            if selection == len(players) + 3:
                return
            elif selection == len(players) + 1 or selection == len(players) + 2:
                # Get top/bottom shooters with minimum 50 attempts
                cursor.execute("""
                    SELECT player, 
                           SUM(fgm) as total_fgm, 
                           SUM(fga) as total_fga, 
                           ROUND((SUM(fgm)::float / NULLIF(SUM(fga), 0) * 100)::numeric, 1) as fg_pct
                    FROM player_stats
                    GROUP BY player
                    HAVING SUM(fga) >= 50
                    ORDER BY fg_pct DESC
                """)
                
                rankings = cursor.fetchall()
                
                if selection == len(players) + 2:  # Bottom shooters
                    rankings.reverse()
                
                print(f"\n{'Top' if selection == len(players) + 1 else 'Bottom'} {top_n} Shooters (min. 50 FGA):")
                print(f"{'Rank':<5} {'Player':<25} {'FGM':<6} {'FGA':<6} {'FG%':<6}")
                print("-" * 55)
                
                for i, (player, fgm, fga, fg_pct) in enumerate(rankings[:top_n]):
                    print(f"{i+1:<5} {player:<25} {fgm:<6} {fga:<6} {fg_pct:<6}%")
                
                cursor.close()
                conn.close()
                return
            else:
                player_name = players[selection-1]
        except (ValueError, IndexError):
            print("Invalid selection. Please try again.")
            cursor.close()
            conn.close()
            return analyze_fg_efficiency(top_n=top_n)
    
    # Analysis for a single player
    cursor.execute("""
        SELECT game_date, opponent, fgm, fga, fg_pct, minutes
        FROM player_stats
        WHERE player = %s
        ORDER BY game_date
    """, (player_name,))
    
    games = cursor.fetchall()
    
    if not games:
        print(f"No games found for {player_name}")
        cursor.close()
        conn.close()
        return
    
    # Calculate totals and averages
    played_games = [game for game in games if not _is_dnp(game[5])]
    total_games = len(played_games)
    total_fgm = sum(game[2] for game in played_games)
    total_fga = sum(game[3] for game in played_games)
    avg_fg_pct = (total_fgm / total_fga * 100) if total_fga > 0 else 0
    
    # Calculate hot/cold streaks
    shooting_games = [game for game in played_games if game[3] > 0]
    fg_pcts = [game[4] for game in shooting_games]
    best_fg = max(fg_pcts) if fg_pcts else 0
    worst_fg = min(fg_pcts) if fg_pcts else 0
    
    # Find best/worst games
    best_game = next((game for game in shooting_games if game[4] == best_fg), None)
    worst_game = next((game for game in shooting_games if game[4] == worst_fg), None)
    
    # Print analysis
    print(f"\nField Goal Efficiency Analysis for {player_name}")
    print("-" * 50)
    print(f"Games Played: {total_games}")
    print(f"Total Makes: {total_fgm}")
    print(f"Total Attempts: {total_fga}")
    print(f"Season FG%: {avg_fg_pct:.1f}%")
    
    if best_game is not None:
        print(f"\nBest Shooting Game: {best_game[0]} vs {best_game[1]}")
        print(f"  {best_game[2]}-{best_game[3]} ({best_fg:.1f}%)")
    
    if worst_game is not None:
        print(f"\nWorst Shooting Game: {worst_game[0]} vs {worst_game[1]}")
        print(f"  {worst_game[2]}-{worst_game[3]} ({worst_fg:.1f}%)")
    
    # Print game-by-game breakdown
    print("\nGame-by-Game Breakdown:")
    print(f"{'Date':<12} {'Opponent':<10} {'FGM-FGA':<10} {'FG%':<6}")
    print("-" * 40)
    
    for game in games:
        date = game[0].strftime("%Y-%m-%d")
        opponent = game[1] or "Unknown"
        fgm = game[2]
        fga = game[3]
        fg_pct = game[4] if game[4] is not None else 0

        if _is_dnp(game[5]):
            print(f"{date:<12} {opponent:<10} {'DNP':<10} {'-':<6}")
        else:
            print(f"{date:<12} {opponent:<10} {fgm}-{fga:<10} {fg_pct:.1f}%")
    
    cursor.close()
    conn.close()

def show_player_fg_attempts_calendar(player_name=None):
    """
    Display a player's field goal attempts and makes across games in a calendar heatmap format.
    Shows the actual FGM/FGA values like 3/11 in each game.
    If no player is specified, asks for input.
    """
    conn = psycopg2.connect(
        host=config.DB_HOST,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        port=config.DB_PORT
    )
    
    cursor = conn.cursor()
    
    # If no player specified, get a list of players and ask user to select one
    if player_name is None:
        cursor.execute("SELECT DISTINCT player FROM player_stats ORDER BY player")
        players = [row[0] for row in cursor.fetchall()]
        
        print("Available players:")
        for i, player in enumerate(players):
            print(f"{i+1}. {player}")
        
        selection = int(input("Enter player number: ")) - 1
        player_name = players[selection]
    
    # Query to get game dates, FGM, FGA, team, and minutes for the selected player
    cursor.execute("""
        SELECT game_date, fgm, fga, team, minutes
        FROM player_stats 
        WHERE player = %s 
        ORDER BY game_date
    """, (player_name,))
    
    games = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not games:
        print(f"No games found for {player_name}")
        return
    
    # Convert to pandas DataFrame for easier manipulation
    df = pd.DataFrame(games, columns=['date', 'fgm', 'fga', 'team', 'minutes'])
    
    # Calculate player's season average FG%
    total_fgm = df['fgm'].sum()
    total_fga = df['fga'].sum()
    avg_fg_pct = (total_fgm / total_fga) * 100 if total_fga > 0 else 0
    
    # Create figure with calendar-style subplots
    first_date = df['date'].min()
    last_date = df['date'].max()
    
    # Calculate the number of months to display
    num_months = (last_date.year - first_date.year) * 12 + last_date.month - first_date.month + 1
    
    # Instead of one long figure, organize months in a grid (max 3 columns)
    cols = min(3, num_months)
    rows = (num_months + cols - 1) // cols  # Ceiling division
    
    # Set up the figure with a more balanced layout
    fig = plt.figure(figsize=(15, 4 * rows))
    
    # Process each month
    current_date = datetime(first_date.year, first_date.month, 1).date()
    
    for i in range(num_months):
        # Create a subplot in a grid layout
        ax = fig.add_subplot(rows, cols, i + 1)
        
        year = current_date.year
        month = current_date.month
        
        # Create calendar layout
        cal = calendar.monthcalendar(year, month)
        
        # Create heatmap data - we'll use FG% relative to player's average for coloring
        cal_data_fgpct = np.zeros((len(cal), 7))
        cal_data_fgpct[:] = np.nan  # Set to NaN so empty days are white
        
        # Also store FGM and FGA for display
        cal_data_fgm = np.zeros((len(cal), 7), dtype=int)
        cal_data_fga = np.zeros((len(cal), 7), dtype=int)
        cal_data_raw_pct = np.zeros((len(cal), 7))
        
        # Filter data for current month
        month_start = current_date
        if month == 12:
            month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        month_data = df[(df['date'] >= month_start) & (df['date'] <= month_end)]
        
        # Fill in data
        for _, game in month_data.iterrows():
            day = game['date'].day
            for week_idx, week in enumerate(cal):
                if day in week:
                    day_idx = week.index(day)
                    fgm = game['fgm']
                    fga = game['fga']
                    
                    # Store FGM and FGA
                    cal_data_fgm[week_idx, day_idx] = fgm
                    cal_data_fga[week_idx, day_idx] = fga
                    
                    # Calculate FG% for coloring, but only if shots were attempted
                    if fga > 0:
                        game_fg_pct = (fgm / fga) * 100
                        cal_data_raw_pct[week_idx, day_idx] = game_fg_pct
                        
                        # Store deviation from player's average for coloring
                        # This centers the color scale around the player's average
                        cal_data_fgpct[week_idx, day_idx] = game_fg_pct - avg_fg_pct
                    else:
                        cal_data_raw_pct[week_idx, day_idx] = np.nan
                        cal_data_fgpct[week_idx, day_idx] = np.nan
                    break
        
        # Find the max deviation from average to set color scale symmetrically
        valid_deviations = cal_data_fgpct[~np.isnan(cal_data_fgpct)]
        max_dev = (
            max(np.max(np.abs(valid_deviations)), 15)
            if valid_deviations.size
            else 15
        )
        
        # Create heatmap with diverging colormap centered on player's average
        im = ax.imshow(cal_data_fgpct, cmap='RdYlGn', vmin=-max_dev, vmax=max_dev)
        
        # Add day numbers and FGM/FGA
        for week_idx, week in enumerate(cal):
            for day_idx, day in enumerate(week):
                if day != 0:
                    fgm = cal_data_fgm[week_idx, day_idx]
                    fga = cal_data_fga[week_idx, day_idx]
                    
                    if fga > 0:  # Game with shots attempted
                        # Add team abbreviation to make it more informative
                        game_date = datetime(year, month, day).date()
                        game_row = month_data[month_data['date'] == game_date]
                        team = game_row['team'].values[0]
                        minutes = game_row['minutes'].values[0]
                        
                        # Get raw FG% for this game
                        fg_pct = cal_data_raw_pct[week_idx, day_idx]
                        
                        # Calculate deviation from average for text formatting
                        deviation = fg_pct - avg_fg_pct
                        
                        # Always use black text for consistency and readability
                        text_color = 'black'
                        
                        if _is_dnp(minutes):
                            # Override cell color to grey for DNP games
                            # Create a rectangle patch with grey color
                            rect = plt.Rectangle((day_idx-0.5, week_idx-0.5), 1, 1, 
                                              fill=True, color='lightgrey', alpha=0.7, zorder=0)
                            ax.add_patch(rect)
                            text_content = f"{day}\n{int(fgm)}/{int(fga)}\n{fg_pct:.1f}%\n(DNP)"
                        else:
                            text_content = f"{day}\n{int(fgm)}/{int(fga)}\n{fg_pct:.1f}%"
                            
                        ax.text(day_idx, week_idx, text_content, 
                              ha='center', va='center', fontsize=8, 
                              color=text_color,
                              fontweight='bold')
                    else:
                        ax.text(day_idx, week_idx, f"{day}", ha='center', va='center', 
                              fontsize=9, color='gray')
        
        # Set labels
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        ax.set_xticks(np.arange(len(days)))
        ax.set_xticklabels(days)
        ax.set_yticks([])
        ax.set_title(f"{calendar.month_name[month]} {year}", fontweight='bold')
        
        # Add grid lines
        ax.grid(which='major', color='w', linestyle='-', linewidth=1.5)
        
        # Advance to next month
        if month == 12:
            current_date = datetime(year + 1, 1, 1).date()
        else:
            current_date = datetime(year, month + 1, 1).date()
    
    # Add a colorbar showing deviation from player average
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])  # [left, bottom, width, height]
    cbar = fig.colorbar(im, cax=cbar_ax)
    cbar.set_label(f'Deviation from Avg FG% ({avg_fg_pct:.1f}%)', fontweight='bold')
    
    # Create tick formatter that shows percentages with one decimal place
    import matplotlib.ticker as mtick
    cbar.ax.yaxis.set_major_formatter(
        mtick.FuncFormatter(lambda value, _: f"{value:+.1f}%")
    )
    
    # Add legend explaining the display format and color coding
    legend_text = "Day\nFGM/FGA\nFG%"
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    
    # Add text explaining the color coding
    fig.text(0.5, 0.02, f"Format: {legend_text}\n"
             f"Green = Above Average | Yellow = Near Average | Red = Below Average", 
             ha='center', va='center', bbox=props)
    
    plt.suptitle(f"{player_name} - Field Goal Attempts by Game\nSeason Avg: {avg_fg_pct:.1f}%", 
                fontsize=18, fontweight='bold')
    plt.subplots_adjust(
        left=0.05, right=0.9, bottom=0.12, top=0.88,
        wspace=0.2, hspace=0.4
    )
        
    plt.show()
