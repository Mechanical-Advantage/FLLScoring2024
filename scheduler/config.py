# File paths
teams_db = "../data.db"
excel_path = "schedule.xlsx"

# Names lists
tables_long = ["Red 1", "Red 2", "Blue 1", "Blue 2", "Yellow 1", "Yellow 2"] # for match overview
tables_short = ["R1", "R2", "B1", "B2", "Y1", "Y2"] # for team schedules
judging_rooms = ["Room R1", "Room R2", "Room P1", "Room P2", "Room C1", "Room C2"] # for judging overview
judging_catnames = ["Judging"] # for team schedules

# General config
enable_judging = True
allow_singles = False # should teams be allowed to play without an opponent? (ignored if all other teams have completed their matches)
general = {
"match_tablepaircount": 3, # how many pairs of tables are available for matches?
"match_countperteam": 5, # how many matches should each team play?
"match_starttime": 1575727200, # unix time, when does the first match begin?
"match_cycletime": 480, # secs, how long between the start of each match?
"match_breakfrequency": 5, # how many matches should be played between each break?
"match_breaklength": 1, # how many matches should each break last?
"match_endjointhreshold": 1, # how few matches are required to join the final two sections?
"match_teamgrace": 1, # how many match cycles must separate two matches with the same team?
"judging_roomcount": 3, # how many rooms are available FOR EACH CATEGORY?
"judging_catcount": 1, # how many judging categories?
"judging_start": 1575727200, # unix time, when does the first judging session begin?
"judging_inlength": 600, # secs, how long does each judging session take?
"judging_outlength": 300, # secs, how long should the break between judging sessions take?
"judging_teamgrace": 600 # secs, how long before or after judging should a team be excluded from matches?
}

# Debug
print_output = True
team_schedule_tester = False
create_excel = True
