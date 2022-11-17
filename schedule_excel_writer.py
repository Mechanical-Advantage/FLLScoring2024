import xlsxwriter
from datetime import datetime
import config
import math


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


def create(judging_sessions=None, matches=[], team_schedules={}, team_list=[]):
    # Initialization
    workbook = xlsxwriter.Workbook(config.schedule_path)
    formats = {}

    # Add formats
    formats["teams_title"] = workbook.add_format(
        {"bold": True, "bg_color": "#CA96E0"})
    formats["teams_headers"] = workbook.add_format(
        {"align": "center", "bold": True, "top": True, "bottom": True})
    formats["matches_title"] = workbook.add_format(
        {"bold": True, "bg_color": "#00FF00"})
    formats["matches_headers"] = workbook.add_format(
        {"align": "center", "bold": True, "top": True, "bottom": True})
    formats["matches_headers_time"] = workbook.add_format(
        {"align": "center", "bold": True, "top": True, "bottom": True, "left": True})
    formats["matches_data"] = workbook.add_format({"align": "center"})
    formats["matches_data_time"] = workbook.add_format({"align": "center", "bold": True, "left": True})
    formats["judging_title"] = workbook.add_format(
        {"bold": True, "bg_color": "#00FFFF"})
    formats["judging_headers"] = workbook.add_format(
        {"align": "center", "valign": "vcenter", "bold": True, "top": True, "text_wrap": True})
    formats["judging_data"] = workbook.add_format({"align": "center"})
    formats["table_title"] = workbook.add_format(
        {"bold": True, "bg_color": "#FFC266"})
    formats["table_full_title"] = workbook.add_format(
        {"align": "center", "valign": "vcenter", "bold": True, "bg_color": "#FFC266", "font_size": 30})
    formats["table_full_headers"] = workbook.add_format(
        {"align": "center", "valign": "vcenter", "bold": True, "top": True, "bottom": True, "text_wrap": True, "font_size": 20})
    formats["table_full_data"] = workbook.add_format(
        {"align": "center", "valign": "vcenter", "font_size": 20})
    formats["schedule_title"] = workbook.add_format(
        {"bold": True, "bg_color": "#FFFF00"})

    # Create team list
    teams_sheet = workbook.add_worksheet("Team List")
    teams_sheet.merge_range(0, 0, 0, 1, "TEAM LIST", formats["teams_title"])
    teams_sheet.write(1, 0, "Number", formats["teams_headers"])
    teams_sheet.write(1, 1, "Name", formats["teams_headers"])
    teams_sheet.set_column(1, 1, 25)
    for i in range(len(team_list)):
        teams_sheet.write(i + 2, 0, team_list[i][0])
        teams_sheet.write(i + 2, 1, team_list[i][1])

    # Create match overview setup
    matches_sheet = workbook.add_worksheet("Match Schedule")
    matches_sheet.merge_range(0, 0, 0, round(len(
        config.schedule_tables_long) / 2 * 3), "ROBOT ROUNDS SCHEDULE", formats["matches_title"])
    matches_sheet.write(1, 0, "Match #", formats["matches_headers"])
    for i in range(int(len(config.schedule_tables_long) / 2)):
        matches_sheet.set_column((i * 3) + 1, (i * 3) + 1, 6)
        matches_sheet.write(1, (i * 3) + 1, "Time", formats["matches_headers_time"])
        matches_sheet.write(
            1, (i * 3) + 2, config.schedule_tables_long[i * 2], formats["matches_headers"])
        matches_sheet.write(
            1, (i * 3) + 3, config.schedule_tables_long[i * 2 + 1], formats["matches_headers"])

    # Fill in match data
    table_offsettime = config.schedule_match_cycletime / (len(config.schedule_tables_long) / 2)
    match_number = 0
    for match in matches:
        match_number += 1
        matches_sheet.write(match_number + 1, 0, match_number, formats["matches_data"])
        for i in range(int(len(config.schedule_tables_long) / 2)):
            start_time = match["start_time"] + i * table_offsettime
            matches_sheet.write(match_number + 1, (i * 3) + 1, convert_time(
                start_time), formats["matches_data_time"])
            team_1 = match["teams"][i * 2]
            team_1 = "" if team_1 == -1 else team_1
            team_2 = match["teams"][i * 2 + 1]
            team_2 = "" if team_2 == -1 else team_2
            matches_sheet.write(
                match_number + 1, (i * 3) + 2, team_1, formats["matches_data"])
            matches_sheet.write(
                match_number + 1, (i * 3) + 3, team_2, formats["matches_data"])

    if judging_sessions != None:
        # Create judging overview setup
        judging_sheet = workbook.add_worksheet("Judging Schedule")
        judging_sheet.set_column(0, 0, 12)
        judging_sheet.set_column(1, len(config.schedule_tables_long), 8)
        judging_sheet.merge_range(0, 0, 0, len(
            config.schedule_judging_rooms), "JUDGING SESSION SCHEDULE", formats["judging_title"])
        judging_sheet.write(1, 0, "Time", formats["judging_headers"])
        for i in range(len(config.schedule_judging_rooms)):
            judging_sheet.write(
                1, i + 1, config.schedule_judging_rooms[i], formats["judging_headers"])

        # Fill in judging data
        i = -1
        for session in judging_sessions:
            i += 1
            format = formats["judging_data"]

            judging_sheet.write(
                i + 2, 0, convert_time(session["start_time"]) + "-" + convert_time(session["end_time"]), format)
            room = -1
            for team in session["teams"]:
                room += 1
                if team == -1:
                    to_write = ""
                else:
                    to_write = team
                judging_sheet.write(i + 2, room + 1, to_write, format)

    # Create sheets for each table
    for table_number in range(int(len(config.schedule_tables_long))):
        table_sheet = workbook.add_worksheet(
            "Table " + config.schedule_tables_short[table_number] + " Schedule")
        table_sheet.set_column(0, 2, 15)
        table_sheet.merge_range(
            0, 0, 0, 2, "TABLE " + config.schedule_tables_short[table_number] + " SCHEDULE", formats["table_title"])
        table_sheet.write(1, 0, "Match", formats["matches_headers"])
        table_sheet.write(1, 1, "Time", formats["matches_headers"])
        table_sheet.write(1, 2, "Team", formats["matches_headers"])

        table_sheet_full = workbook.add_worksheet(
            "Table " + config.schedule_tables_short[table_number] + " Schedule (full)")
        table_sheet_full.set_page_view()
        table_sheet_full.center_horizontally()
        table_sheet_full.set_column(0, 2, 27)
        table_sheet_full.set_row(0, 35)
        table_sheet_full.set_row(1, 35)
        table_sheet_full.merge_range(
            0, 0, 0, 2, "TABLE " + config.schedule_tables_short[table_number] + " SCHEDULE", formats["table_full_title"])
        table_sheet_full.write(1, 0, "Match", formats["table_full_headers"])
        table_sheet_full.write(1, 1, "Time", formats["table_full_headers"])
        table_sheet_full.write(1, 2, "Team", formats["table_full_headers"])

        row = 0
        match_number = 0
        specific_table_offset = math.floor(table_number / 2) * table_offsettime
        for match in matches:
            team = match["teams"][table_number]
            match_number += 1
            if team != -1:
                row += 1
                table_sheet.write(row + 1, 0, match_number,
                                  formats["matches_data"])
                table_sheet.write(row + 1, 1, convert_time(match["start_time"] + specific_table_offset) + "-" + convert_time(
                    match["start_time"] + specific_table_offset + table_offsettime), formats["matches_data"])
                table_sheet.write(row + 1, 2, team, formats["matches_data"])
                table_sheet_full.write(
                    row + 1, 0, match_number, formats["table_full_data"])
                table_sheet_full.write(row + 1, 1, convert_time(match["start_time"] + specific_table_offset) + "-" + convert_time(
                    match["start_time"] + specific_table_offset + table_offsettime), formats["table_full_data"])
                table_sheet_full.write(
                    row + 1, 2, team, formats["table_full_data"])
                table_sheet_full.set_row(row + 1, 35)

    # Creates spreadsheets for each team's schedules
    for team, schedule in team_schedules.items():
        team_sheet = workbook.add_worksheet("Team " + str(team) + " Schedule")
        team_sheet.set_column(0, 2, 18)
        team_sheet.merge_range(
            0, 0, 0, 2, "TEAM " + str(team) + " SCHEDULE", formats["schedule_title"])
        team_sheet.write(1, 0, "Time", formats["matches_headers"])
        team_sheet.write(1, 1, "Activity", formats["matches_headers"])
        team_sheet.write(1, 2, "Location", formats["matches_headers"])

        row = 2
        for i in schedule:
            team_sheet.write(row, 0, convert_time(
                i["start_time"]) + "-" + convert_time(i["end_time"]), formats["matches_data"])
            team_sheet.write(row, 1, i["title"], formats["matches_data"])
            team_sheet.write(row, 2, i["location"], formats["matches_data"])
            row += 1

    # Close workbook
    workbook.close()
