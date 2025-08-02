from Graphs import *

def main():
    print("\nWNBA Stats Tracker")
    print("-----------------")
    print("1. View all player stats")
    print("2. View points calendar for a player")
    print("3. View field goal percentage calendar for a player")
    print("4. View field goal attempts calendar (FGM/FGA)")
    print("5. Analyze field goal efficiency")
    choice = input("Choose an option: ")
    
    if choice == '1':
        display_all_stats()
    elif choice == '2':
        show_player_points_calendar()
    elif choice == '3':
        show_player_fg_pct_calendar()
    elif choice == '4':
        show_player_fg_attempts_calendar()
    elif choice == '5':
        analyze_fg_efficiency()
    else:
        print("Invalid option. Please try again.")
        main()

if __name__ == '__main__':
    main()