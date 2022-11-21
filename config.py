# File paths
db_path = "data.db"
schedule_path = "schedule.xlsx"

# Names lists for schedule
schedule_tables_long = ["Red 1", "Red 2", "Blue 1", "Blue 2",
                        "Yellow 1", "Yellow 2"]  # for match overview
schedule_tables_short = ["R1", "R2", "B1",
                         "B2", "Y1", "Y2"]  # for team schedules
schedule_judging_rooms = ["Room 1", "Room 2", "Room 3", "Room 4"]  # for judging overview

# General config for schedule
schedule_starttime = 1668952800  # unix time, when does the first match & judging session begin?
schedule_match_countperteam = 5  # how many matches should each team play?
schedule_match_cycletime = 600  # secs, how long between the start of each match?
schedule_match_breakfrequency = 5  # how many matches should be played between each break?
schedule_match_breaklength = 1  # how many matches should each break last?
schedule_match_teamgrace = 1  # how many match cycles must separate two matches with the same team?
schedule_judging_inlength = 1800  # secs, how long does each judging session take?
schedule_judging_outlength = 900  # secs, how long should the break between judging sessions take?
schedule_judging_teamgrace = 900  # secs, how long before or after judging should a team be excluded from matches?

# General config for playoffs
playoffs_starttime = 1668967200
playoffs_cycletime = 600
playoffs_matchnumberstart = 50
