import sqlite3 as sql
import itertools
import copy
import math
from datetime import datetime
import config
import schedule_excel_writer as excel_writer

# Setup db connection
conn = sql.connect(config.db_path)
cur = conn.cursor()


# Function for rendering time w/o padding
def convert_time(timestamp, include_p=False):
    hour = datetime.fromtimestamp(timestamp).strftime("%I")
    while hour[:1] == "0":
        hour = hour[1:]
    if include_p:
        minute_string = ":%M %p"
    else:
        minute_string = ":%M"
    return(hour + datetime.fromtimestamp(timestamp).strftime(minute_string))


# Generate team objects
teams = {}
teams_raw = cur.execute(
    "SELECT TeamNumber FROM teams ORDER BY teamNumber ASC").fetchall()
for teamrow in teams_raw:
    teams[int(teamrow[0])] = {"match_count": 0, "last_match": -999, "previous_opponents": [],
                              "previous_tables": {}, "blackout_start": 0, "blackout_end": 0}
    for table in range(len(config.schedule_tables_long)):
        teams[int(teamrow[0])]["previous_tables"][table] = 0

# Create judging sessions
judging_sessions = []
judging_session_count = math.ceil(len(teams)/len(config.schedule_judging_rooms))
judging_session_length = config.schedule_judging_inlength + config.schedule_judging_outlength
for i in range(judging_session_count):
    start_time = config.schedule_starttime + (judging_session_length * i)
    judging_sessions.append({"teams": [], "start_time": start_time,
                             "end_time": start_time + config.schedule_judging_inlength})

# Assign judging sessions
i = 0
for teamnumber in teams.keys():
    judging_sessions[i]["teams"].append(teamnumber)
    teams[teamnumber]["blackout_start"] = judging_sessions[i]["start_time"] - \
        config.schedule_judging_teamgrace
    teams[teamnumber]["blackout_end"] = judging_sessions[i]["end_time"] + config.schedule_judging_teamgrace
    if len(judging_sessions[i]["teams"]) >= len(config.schedule_judging_rooms):
        i += 1

# Print judging sessions
print("\nJudging sessions:")
[print(x) for x in judging_sessions]
print("Ends at", convert_time(
    judging_sessions[len(judging_sessions)-1]["end_time"], True))


# Generate possible arrangements of teams
def get_arrangements(pair_count):
    result = []
    for pair_arrangement in list(itertools.permutations(range(pair_count))):
        for reverses in list(itertools.product([0, 1], repeat=pair_count)):
            temp = {}
            temp["pairs"] = pair_arrangement
            temp["reverses"] = reverses
            result.append(temp)
    return(result)


# Get team -1 with correct data
def getFillerTeam():
    output = {"number": -1, "match_count": 0, "last_match": 0, "previous_opponents": [],
              "previous_tables": {}, "blackout_start": None, "blackout_end": None}
    for table in range(int(len(config.schedule_tables_long))):
        output["previous_tables"][table] = 0
    return(output)


# Create single mach
def create_match(start_time, end_time, match_number):
    # Get list of possible teams
    teams_sorted = []
    incomplete_count = 0
    for teamnumber in teams.keys():
        outside_blackout = (teams[teamnumber]["blackout_start"] <= start_time and teams[teamnumber]["blackout_end"] <= start_time) or (
            teams[teamnumber]["blackout_start"] >= end_time and teams[teamnumber]["blackout_end"] >= end_time)
        matches_incomplete = teams[teamnumber]["match_count"] < config.schedule_match_countperteam
        match_grace_complete = match_number - \
            teams[teamnumber]["last_match"] > config.schedule_match_teamgrace
        if matches_incomplete:
            incomplete_count += 1
        if outside_blackout and matches_incomplete and match_grace_complete:
            temp_team = copy.deepcopy(teams[teamnumber])
            temp_team["number"] = teamnumber
            teams_sorted.append(temp_team)

    # Sort teams
    teams_sorted = sorted(teams_sorted, key=lambda team: (
        team["last_match"], team["number"]))

    # Add extra teams
    while len(teams_sorted) < len(config.schedule_tables_long):
        teams_sorted.append(getFillerTeam())

    # Create pairs
    pairs = []
    for i in range(int(len(config.schedule_tables_long)/2)):
        pairs.append([])
        pairs[i].append(teams_sorted[0])
        first_team = True
        for team in teams_sorted:
            if (team["number"] not in pairs[i][0]["previous_opponents"]) and (team["number"] != -1) and (not first_team):
                pairs[i].append(team)
                teams_sorted.remove(team)
                break
            first_team = False
        if len(pairs[i]) == 1:
            if teams_sorted[1]["number"] == -1 and incomplete_count > 1:
                # They are the last team to schedule in this match, but others are incomplete (hold off scheduling them)
                pairs.pop()
                pairs.append([getFillerTeam()] * 2)
                continue
            else:
                # The next team is a previous opponent, or this is the last team to be scheduled
                team = teams_sorted[1]
                pairs[i].append(team)
                teams_sorted.remove(team)

        teams_sorted.remove(teams_sorted[0])

    # Test possible arrangements
    arrangements = []
    for arrangement_base in get_arrangements(int(len(config.schedule_tables_long)/2)):
        arrangement = {"teams": [], "table_repeats": 0}
        for pair_number in arrangement_base["pairs"]:
            reversed = arrangement_base["reverses"][pair_number]

            team1 = pairs[pair_number][reversed]
            arrangement["teams"].append(team1["number"])
            arrangement["table_repeats"] += team1["previous_tables"][len(
                arrangement["teams"])-1]

            team2 = pairs[pair_number][1-reversed]
            arrangement["teams"].append(team2["number"])
            arrangement["table_repeats"] += team2["previous_tables"][len(
                arrangement["teams"])-1]
        arrangements.append(arrangement)

    # Find optimal arrangement
    teams_final = sorted(arrangements, key=lambda arrangement: (
        arrangement["table_repeats"],) + tuple(arrangement["teams"]))[0]["teams"]

    # Update team data
    table = -1
    for teamnumber in teams_final:
        table += 1
        if teamnumber != -1:
            teams[teamnumber]["match_count"] += 1
            teams[teamnumber]["last_match"] = match_number
            teams[teamnumber]["previous_tables"][table] += 1

            if table % 2 == 0:
                opponent = teams_final[table + 1]
            else:
                opponent = teams_final[table - 1]
            if opponent not in teams[teamnumber]["previous_opponents"]:
                teams[teamnumber]["previous_opponents"].append(opponent)

    # Return result
    return({"start_time": start_time, "end_time": end_time, "teams": teams_final})


# Check if all teams have played enough matches
def matches_complete():
    complete = True
    for data in teams.values():
        if data["match_count"] < config.schedule_match_countperteam:
            complete = False
    return(complete)


last_break = 0


# Generate matches
def generate_matches(break_limit=None):
    global last_break
    matches = []
    match_number = 0
    matches_cycle = 0
    last_played = True
    start_time = config.schedule_starttime - config.schedule_match_cycletime
    while not matches_complete():
        match_number += 1
        start_time += config.schedule_match_cycletime
        matches_cycle += 1
        if matches_cycle > config.schedule_match_breakfrequency + config.schedule_match_breaklength:
            matches_cycle = 1
        if break_limit == None:
            past_break_limit = False
        else:
            past_break_limit = match_number >= break_limit

        if matches_cycle > config.schedule_match_breakfrequency and not past_break_limit:
            last_break = match_number
            last_played = False
            matches.append({"start_time": start_time, "end_time": start_time +
                           config.schedule_match_cycletime, "teams": [-1] * len(config.schedule_tables_long)})
        else:
            match_to_append = create_match(
                start_time, start_time + config.schedule_match_cycletime, match_number)
            matches.append(match_to_append)
            if match_to_append["teams"] == [-1] * len(config.schedule_tables_long):
                if last_played:
                    matches_cycle = config.schedule_match_breakfrequency + 1
                    last_played = False
                else:
                    matches_cycle -= 1
            else:
                last_played = True
    return(matches)


# Regenerate matches if break too close to end
teams_backup = copy.deepcopy(teams)
matches = generate_matches()
if len(matches) - last_break <= 1:
    teams = teams_backup
    matches = generate_matches(
        break_limit=last_break-config.schedule_match_breaklength+1)

# Print matches
print("\nMatches:")
[print(x) for x in matches]
print("Ends at", convert_time(matches[len(matches)-1]["end_time"], True))


# Get schedule for teams
def get_team_schedule(team_query):
    schedule_items = []
    for session in judging_sessions:
        if team_query in session["teams"]:
            room = session["teams"].index(team_query)
            schedule_items.append({"start_time": session["start_time"], "end_time": session["end_time"],
                                   "title": "Judging", "location": config.schedule_judging_rooms[room]})

    match_number = 0
    table_offsettime = config.schedule_match_cycletime / (len(config.schedule_tables_long) / 2)
    for match in matches:
        match_number += 1
        if team_query in match["teams"]:
            start_time = match["start_time"] + (math.floor(match["teams"].index(team_query) / 2) * table_offsettime)
            schedule_items.append({"start_time": start_time, "end_time": start_time + table_offsettime, "title": "Match " + str(
                match_number), "location": "Table " + config.schedule_tables_short[match["teams"].index(team_query)]})
    return(sorted(schedule_items, key=lambda x: (x["start_time"],)))


# Write to database
cur.execute("DELETE FROM match_schedule")
match_number = 0
for match in matches:
    match_number += 1
    for i in range(int(len(match["teams"]) / 2)):
        team1 = match["teams"][i * 2]
        team2 = match["teams"][i * 2 + 1]
        if team1 != -1 or team2 != -1:
            cur.execute("INSERT INTO match_schedule(number, field, team1, team2) VALUES (?,?,?,?)",
                        (match_number, config.schedule_tables_long[i * 2].split(" ")[0], team1, team2))
conn.commit()


# Get team list
team_list = cur.execute(
    "SELECT TeamNumber,TeamName FROM teams ORDER BY TeamNumber ASC").fetchall()

# Create excel file
team_schedules = {}
for team in [int(x[0]) for x in teams_raw]:
    team_schedules[team] = get_team_schedule(team)
excel_writer.create(judging_sessions=judging_sessions,
                    matches=matches, team_schedules=team_schedules, team_list=team_list)

# Team schedule generator
# print()
# team_query = int(input("Enter a team number: "))
# for item in get_team_schedule(team_query):
#     print(convert_time(item["start_time"]) + "-" + convert_time(
#         item["end_time"]) + ") " + item["title"] + " (" + item["location"] + ")")
