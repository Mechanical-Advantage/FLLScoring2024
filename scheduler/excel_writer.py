import xlsxwriter
from datetime import datetime
import config

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

def create(judging_sessions=None, matches=[], team_schedules={}):
    #Initialization
    workbook = xlsxwriter.Workbook(config.excel_path)
    formats = {}

    #Add formats
    formats["matches_title"] = workbook.add_format({"bold": True, "bg_color": "#00FF00"})
    formats["matches_headers"] = workbook.add_format({"align": "center", "bold": True, "top": True, "bottom": True})
    formats["matches_data"] = workbook.add_format({"align": "center"})
    formats["judging_title"] = workbook.add_format({"bold": True, "bg_color": "#00FFFF"})
    formats["judging_headers"] = workbook.add_format({"align": "center", "valign": "vcenter", "bold": True, "top": True, "text_wrap": True})
    formats["judging_data"] = workbook.add_format({"align": "center"})
    formats["judging_sectionstart"] = workbook.add_format({"align": "center", "top": True})
    formats["table_title"] = workbook.add_format({"bold": True, "bg_color": "#FFC266"})
    formats["table_full_title"] = workbook.add_format({"align": "center", "valign": "vcenter", "bold": True, "bg_color": "#FFC266", "font_size": 30})
    formats["table_full_headers"] = workbook.add_format({"align": "center", "valign": "vcenter", "bold": True, "top": True, "bottom": True, "text_wrap": True, "font_size": 20})
    formats["table_full_data"] = workbook.add_format({"align": "center", "valign": "vcenter", "font_size": 20})
    formats["schedule_title"] = workbook.add_format({"bold": True, "bg_color": "#FFFF00"})
    
    #Create match overview setup
    matches_sheet = workbook.add_worksheet("Match Schedule")
    matches_sheet.set_column(0, 1, 13)
    matches_sheet.set_column(2, len(config.tables_long) + 1, 8)
    matches_sheet.merge_range(0, 0, 0, len(config.tables_long) + 1, "OFFICIAL ROBOT ROUNDS SCHEDULE", formats["matches_title"])
    matches_sheet.write(1, 0, "Match Number", formats["matches_headers"])
    matches_sheet.write(1, 1, "Time", formats["matches_headers"])
    for i in range(len(config.tables_long)):
        matches_sheet.write(1, i + 2, config.tables_long[i], formats["matches_headers"])
    
    #Fill in match data
    match_number = 0
    for match in matches:
        match_number += 1
        matches_sheet.write(match_number + 1, 0, match_number, formats["matches_data"])
        matches_sheet.write(match_number + 1, 1, convert_time(match["start_time"]) + "-" + convert_time(match["end_time"]), formats["matches_data"])
        table = -1
        for team in match["teams"]:
            table += 1
            if team == -1:
                to_write = ""
            else:
                to_write = team
            matches_sheet.write(match_number + 1, table + 2, to_write, formats["matches_data"])

    if judging_sessions != None:
        #Create judging overview setup
        judging_sheet = workbook.add_worksheet("Judging Schedule")
        judging_sheet.set_column(0, 0, 12)
        judging_sheet.set_column(1, len(config.tables_long), 8)
        judging_sheet.merge_range(0, 0, 0, len(config.judging_rooms), "JUDGING SESSION SCHEDULE", formats["judging_title"])
        judging_sheet.write(1, 0, "Time", formats["judging_headers"])
        for i in range(len(config.judging_rooms)):
            judging_sheet.write(1, i + 1, config.judging_rooms[i], formats["judging_headers"])

        #Fill in judging data
        i = -1
        for session in judging_sessions:
            i += 1
            if config.general["judging_catcount"] == None or config.general["judging_catcount"] == 1:
                format = formats["judging_data"]
            else:
                if i % config.general["judging_catcount"] == 0:
                    format = formats["judging_sectionstart"]
                else:
                    format = formats["judging_data"]

            judging_sheet.write(i + 2, 0, convert_time(session["start_time"]) + "-" + convert_time(session["end_time"]), format)
            room = -1
            for team in session["teams"]:
                room += 1
                if team == -1:
                    to_write = ""
                else:
                    to_write = team
                judging_sheet.write(i + 2, room + 1, to_write, format)

    #Create sheets for each table
    for table_number in range(config.general["match_tablepaircount"]*2):
        table_sheet = workbook.add_worksheet("Table " + config.tables_short[table_number] + " Schedule")
        table_sheet.set_column(0, 2, 15)
        table_sheet.merge_range(0, 0, 0, 2, "TABLE " + config.tables_short[table_number] + " SCHEDULE", formats["table_title"])
        table_sheet.write(1, 0, "Match", formats["matches_headers"])
        table_sheet.write(1, 1, "Time", formats["matches_headers"])
        table_sheet.write(1, 2, "Team", formats["matches_headers"])
        
        table_sheet_full = workbook.add_worksheet("Table " + config.tables_short[table_number] + " Schedule (full)")
        table_sheet_full.set_page_view()
        table_sheet_full.center_horizontally()
        table_sheet_full.set_column(0, 2, 27)
        table_sheet_full.set_row(0, 35)
        table_sheet_full.set_row(1, 35)
        table_sheet_full.merge_range(0, 0, 0, 2, "TABLE " + config.tables_short[table_number] + " SCHEDULE", formats["table_full_title"])
        table_sheet_full.write(1, 0, "Match", formats["table_full_headers"])
        table_sheet_full.write(1, 1, "Time", formats["table_full_headers"])
        table_sheet_full.write(1, 2, "Team", formats["table_full_headers"])
        
        row = 0
        match_number = 0
        for match in matches:
            team = match["teams"][table_number]
            match_number += 1
            if team != -1:
                row += 1
                table_sheet.write(row + 1, 0, match_number, formats["matches_data"])
                table_sheet.write(row + 1, 1, convert_time(match["start_time"]) + "-" + convert_time(match["end_time"]), formats["matches_data"])
                table_sheet.write(row + 1, 2, team, formats["matches_data"])
                table_sheet_full.write(row + 1, 0, match_number, formats["table_full_data"])
                table_sheet_full.write(row + 1, 1, convert_time(match["start_time"]) + "-" + convert_time(match["end_time"]), formats["table_full_data"])
                table_sheet_full.write(row + 1, 2, team, formats["table_full_data"])
                table_sheet_full.set_row(row + 1, 35)

    #Creates spreadsheets for each team's schedules
    all_matches = workbook.add_worksheet("All Matches")
    all_matches_row = 0
    for team, schedule in team_schedules.items():
        team_sheet = workbook.add_worksheet("Team " + str(team) + " Schedule")
        team_sheet.set_column(0,2,18)
        team_sheet.merge_range(0, 0, 0, 2, "TEAM " + str(team) + " SCHEDULE", formats["schedule_title"])
        team_sheet.write(1, 0, "Time", formats["matches_headers"])
        team_sheet.write(1, 1, "Activity", formats["matches_headers"])
        team_sheet.write(1, 2, "Location", formats["matches_headers"])

        row = 2
        for i in schedule:
            team_sheet.write(row, 0, convert_time(i["start_time"]) + "-" + convert_time(i["end_time"]), formats["matches_data"])
            team_sheet.write(row, 1, i["title"], formats["matches_data"])
            team_sheet.write(row, 2, i["location"], formats["matches_data"])
            row += 1

            #Create a table of team number, match number, and table number
            if i["title"][:5] == "Match":
                all_matches.write(all_matches_row, 0, team)
                all_matches.write(all_matches_row, 1, int(i["title"][6:]))
                all_matches.write(all_matches_row, 2, config.tables_short.index(i["location"][6:]) + 1)
                all_matches_row = all_matches_row+1

    #Close workbook
    workbook.close()
