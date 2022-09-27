import sqlite3 as sql
import itertools
import copy
import math
from datetime import datetime
import config

#Import excel writer script if needed
if config.create_excel:
    import excel_writer

#Setup db connection
conn = sql.connect(config.teams_db)
cur = conn.cursor()

#Function for rendering time w/o padding
def convert_time(timestamp, include_p=False):
    hour = datetime.fromtimestamp(timestamp).strftime("%I")
    while hour[:1] == "0":
        hour = hour[1:]
    if include_p:
        minute_string = ":%M %p"
    else:
        minute_string = ":%M"
    return(hour + datetime.fromtimestamp(timestamp).strftime(minute_string))

#Generate team objects
teams = {}
teams_raw = cur.execute("SELECT teamNumber FROM teams ORDER BY teamNumber ASC").fetchall()
for teamrow in teams_raw:
    teams[int(teamrow[0])] = {"match_count": 0, "last_match": -999, "previous_opponents": [], "previous_tables": {}, "blackout_start": 0, "blackout_end": 0}
    for table in range(config.general["match_tablepaircount"]*2):
        teams[int(teamrow[0])]["previous_tables"][table] = 0

if config.enable_judging:
    #Create judging blocks
    judging_blocks = {}
    block_count = math.ceil(len(teams)/(config.general["judging_roomcount"]*config.general["judging_catcount"]))
    block_length = (config.general["judging_inlength"] + config.general["judging_outlength"]) * config.general["judging_catcount"]
    for i in range(1, block_count+1):
        start_time = config.general["judging_start"] + (block_length * (i - 1))
        judging_blocks[i] = {"teams": [], "start_time": start_time}

    #Assign judging blocks
    block = 1
    for teamnumber in teams.keys():
        judging_blocks[block]["teams"].append(teamnumber)
        teams[teamnumber]["blackout_start"] = judging_blocks[block]["start_time"] - config.general["judging_teamgrace"]
        teams[teamnumber]["blackout_end"] = judging_blocks[block]["start_time"] + (config.general["judging_catcount"] * (config.general["judging_inlength"] + config.general["judging_outlength"])) - config.general["judging_outlength"] + config.general["judging_teamgrace"]
        if len(judging_blocks[block]["teams"]) >= config.general["judging_roomcount"]*config.general["judging_catcount"]:
            block += 1

    #Create judging sessions
    judging_sessions = []
    for blockdata in judging_blocks.values():
        while len(blockdata["teams"]) < config.general["judging_roomcount"] * config.general["judging_catcount"]:
            blockdata["teams"].append(-1)
        time_shift = -1
        for shift in [0] + list(range(config.general["judging_catcount"]))[::-1][:-1]:
            time_shift += 1
            start_time = blockdata["start_time"] + (time_shift * (config.general["judging_inlength"] + config.general["judging_outlength"]))
            session = {"start_time": start_time, "end_time": start_time + config.general["judging_inlength"], "teams": []}
            for i in range(len(blockdata["teams"])):
                i_shifted = (i + (shift * config.general["judging_roomcount"])) % (config.general["judging_roomcount"] * config.general["judging_catcount"])
                session["teams"].append(blockdata["teams"][i_shifted])
            judging_sessions.append(session)

    #Print judging sessions
    if config.print_output:
        print("\nJudging sessions:")
        [print(x) for x in judging_sessions]
        print("Ends at", convert_time(judging_sessions[len(judging_sessions)-1]["end_time"], True))

#Generate possible arrangements of teams
def get_arrangements(pair_count):
    result = []
    for pair_arrangement in list(itertools.permutations(range(pair_count))):
        for reverses in list(itertools.product([0, 1], repeat=pair_count)):
            temp = {}
            temp["pairs"] = pair_arrangement
            temp["reverses"] = reverses
            result.append(temp)
    return(result)

#Get team -1 with correct data
def getFillerTeam():
    output = {"number": -1, "match_count": 0, "last_match": 0, "previous_opponents": [], "previous_tables": {}, "blackout_start": None, "blackout_end": None}
    for table in range(config.general["match_tablepaircount"]*2):
        output["previous_tables"][table] = 0
    return(output)

#Create single mach
def create_match(start_time, end_time, match_number):
    #Get list of possible teams
    teams_sorted = []
    incomplete_count = 0
    for teamnumber in teams.keys():
        outside_blackout = (teams[teamnumber]["blackout_start"] <= start_time and teams[teamnumber]["blackout_end"] <= start_time) or (teams[teamnumber]["blackout_start"] >= end_time and teams[teamnumber]["blackout_end"] >= end_time)
        matches_incomplete = teams[teamnumber]["match_count"] < config.general["match_countperteam"]
        match_grace_complete = match_number - teams[teamnumber]["last_match"] > config.general["match_teamgrace"]
        if matches_incomplete:
            incomplete_count += 1
        if outside_blackout and matches_incomplete and match_grace_complete:
            temp_team = copy.deepcopy(teams[teamnumber])
            temp_team["number"] = teamnumber
            teams_sorted.append(temp_team)

    #Sort teams
    teams_sorted = sorted(teams_sorted, key=lambda team: (team["last_match"], team["number"]))

    #Add extra teams
    while len(teams_sorted) < config.general["match_tablepaircount"] * 2:
        teams_sorted.append(getFillerTeam())

    #Create pairs
    pairs = []
    for i in range(config.general["match_tablepaircount"]):
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
            if (not config.allow_singles) and teams_sorted[1]["number"] == -1 and incomplete_count > 1:
                pairs.pop()
                pairs.append([getFillerTeam()] * 2)
                continue
            else:
                pairs[i].append(teams_sorted[1])
                teams_sorted.remove(teams_sorted[1])
        teams_sorted.remove(teams_sorted[0])

    #Test possible arrangements
    arrangements = []
    for arrangement_base in get_arrangements(config.general["match_tablepaircount"]):
        arrangement = {"teams": [], "table_repeats": 0}
        for pair_number in arrangement_base["pairs"]:
            reversed = arrangement_base["reverses"][pair_number]

            team1 = pairs[pair_number][reversed]
            arrangement["teams"].append(team1["number"])
            arrangement["table_repeats"] += team1["previous_tables"][len(arrangement["teams"])-1]

            team2 = pairs[pair_number][1-reversed]
            arrangement["teams"].append(team2["number"])
            arrangement["table_repeats"] += team2["previous_tables"][len(arrangement["teams"])-1]
        arrangements.append(arrangement)

    #Find optimal arrangement
    teams_final = sorted(arrangements, key=lambda arrangement: (arrangement["table_repeats"],) + tuple(arrangement["teams"]))[0]["teams"]

    #Update team data
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

    #Return result
    return({"start_time": start_time, "end_time": end_time, "teams": teams_final})

#Check if all teams have played enough matches
def matches_complete():
    complete = True
    for data in teams.values():
        if data["match_count"] < config.general["match_countperteam"]:
            complete = False
    return(complete)

#Generate matches
last_break = 0
def generate_matches(break_limit=None):
    global last_break
    matches = []
    match_number = 0
    matches_cycle = 0
    last_played = True
    start_time = config.general["match_starttime"] - config.general["match_cycletime"]
    while not matches_complete():
        match_number += 1
        start_time += config.general["match_cycletime"]
        matches_cycle += 1
        if matches_cycle > config.general["match_breakfrequency"] + config.general["match_breaklength"]:
            matches_cycle = 1
        if break_limit == None:
            past_break_limit = False
        else:
            past_break_limit = match_number >= break_limit

        if matches_cycle > config.general["match_breakfrequency"] and not past_break_limit:
            last_break = match_number
            last_played = False
            matches.append({"start_time": start_time, "end_time": start_time + config.general["match_cycletime"], "teams": [-1] * config.general["match_tablepaircount"] * 2})
        else:
            match_to_append = create_match(start_time, start_time + config.general["match_cycletime"], match_number)
            matches.append(match_to_append)
            if match_to_append["teams"] == [-1] * config.general["match_tablepaircount"] * 2:
                if last_played:
                    matches_cycle = config.general["match_breakfrequency"] + 1
                    last_played = False
                else:
                    matches_cycle -= 1
            else:
                last_played = True
    return(matches)

#Regenerate matches if break too close to end
teams_backup = copy.deepcopy(teams)
matches = generate_matches()
if len(matches) - last_break <= config.general["match_endjointhreshold"]:
    teams = teams_backup
    matches = generate_matches(break_limit=last_break-config.general["match_breaklength"]+1)

#Print matches
if config.print_output:
    print("\nMatches:")
    [print(x) for x in matches]
    print("Ends at", convert_time(matches[len(matches)-1]["end_time"], True))

#Get schedule for team
def get_team_schedule(team_query):
    schedule_items = []
    if config.enable_judging:
        for session in judging_sessions:
            if team_query in session["teams"]:
                room = session["teams"].index(team_query)
                judging_type = config.judging_catnames[math.floor(room/config.general["judging_roomcount"])]
                schedule_items.append({"start_time": session["start_time"], "end_time": session["end_time"], "title": judging_type + " Judging", "location": config.judging_rooms[room]})
    match_number = 0
    for match in matches:
        match_number += 1
        if team_query in match["teams"]:
            schedule_items.append({"start_time": match["start_time"], "end_time": match["end_time"], "title": "Match " + str(match_number), "location": "Table " + config.tables_short[match["teams"].index(team_query)]})
    return(sorted(schedule_items, key=lambda x: (x["start_time"],)))

#Create excel file
if config.create_excel:
    if config.enable_judging:
        temp_sessions = judging_sessions
    else:
        temp_sessions = None

    team_schedules = {}
    for team in [int(x[0]) for x in teams_raw]:
        team_schedules[team] = get_team_schedule(team)
    excel_writer.create(judging_sessions=temp_sessions, matches=matches, team_schedules=team_schedules)

#Team schedule generator
if config.team_schedule_tester:
    if config.print_output:
        print()
    team_query = int(input("Enter a team number: "))
    for item in get_team_schedule(team_query):
        print(convert_time(item["start_time"]) + "-" + convert_time(item["end_time"]) + ") " + item["title"] + " (" + item["location"] + ")")
