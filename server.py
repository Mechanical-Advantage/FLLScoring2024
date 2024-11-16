import json
import math
import os
import sqlite3 as sql
import threading
import time
from datetime import datetime

import cherrypy
from ws4py.messaging import TextMessage
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket

import config


class Root(object):
    @cherrypy.expose
    def index(self):
        return """ <h1>FLL Scrimmage Pages:</h1>
        <br>
        <a href='/static/Form.html'>Score Entry</a>
        <br>
        <a href='/static/rankDisplay_headsup.html'>Ranking Display (With Heads-Up)</a>
        <br>
        <a href='/static/rankDisplay.html'>Ranking Display</a>
        <br>
        <a href='/playoffs'>Playoffs Display</a>
        <br>
        <a href='/playoffsAdvanced'>Playoffs Display (Advanced)</a>
        <br>
        <a href='/static/timerDisplay.html'>Timer Display</a>
        <br>
        <a href='/static/timercontrol.html'>Timer Control</a>
        <br>
        <a href='/GPScore'>GPScore Summary</a>
        <br>
        """

    @cherrypy.expose
    def ws(self):
        pass

    @cherrypy.expose
    def playoffs(self):
        with open("static" + os.path.sep + "playoffs.html", "r") as playoffs:
            html = playoffs.read()
            new_html = html.replace("$show_matches", "false")
            return new_html

    @cherrypy.expose
    def playoffsAdvanced(self):
        with open("static" + os.path.sep + "playoffs.html", "r") as playoffs:
            html = playoffs.read()
            new_html = html.replace("$show_matches", "true")
            return new_html

    @cherrypy.expose
    def saveMatch(self, team, match, referee, field, score, GPScore, teamInitials, precisionTokens, scoreDetail):
        print("Team: " + team + "\nMatch: " + match + "\nReferee:  " + referee + "\nfield: " + field + "\nScore: " +
              score + "\nGPScore: " + GPScore + "\nTeam Initials: " + teamInitials + "\nPrecision Tokens: " + precisionTokens + "\nScore Detail: " + scoreDetail)

        conn_global = sql.connect("data.db")
        cur_global = conn_global.cursor()
        cur_global.execute(
            "INSERT INTO matches(team, match, referee, field, score, GPScore, teamInitials, precisionTokens, scoreDetail) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (team, match, referee, field, score, GPScore, teamInitials, precisionTokens, scoreDetail))
        conn_global.commit()
        conn_global.close()
        return

    @cherrypy.expose
    def getMatch(self, team, match):
        print("getMatch(", team, ",", match, ")")
        conn_global = sql.connect("data.db")
        cur_global = conn_global.cursor()
        cur_global.execute(
            'SELECT * FROM matches WHERE team=? and match=?',(team, match))
        rows = cur_global.fetchall()[0][8]
        print(rows)
        conn_global.commit()
        conn_global.close()
        return (rows)
    
    @cherrypy.expose
    def getMatches(self):
        conn_global = sql.connect("data.db")
        cur_global = conn_global.cursor()
        matches = cur_global.execute("select * from matches").fetchall()
        match_data = []

    @cherrypy.expose
    def getData(self):
        conn_global = sql.connect("data.db")
        cur_global = conn_global.cursor()

        teams = cur_global.execute("select * from teams").fetchall()
        team_data = []
        for team in teams:
            avgScore = cur_global.execute(
                "select avg(score) from matches where team = ?", (team[0],)).fetchall()[0][0]
            avgScore = 0 if avgScore == None else avgScore
            maxScore = cur_global.execute(
                "select max(score) from matches where team = ?", (team[0],)).fetchall()[0][0]
            maxScore = 0 if maxScore == None else maxScore
            allScores = cur_global.execute(
                "select (score) from matches where team = ? order by score DESC", (team[0],)).fetchall()
            allScores = [x[0] for x in allScores]

            team_data.append({
                "TeamNumber": team[0],
                "TeamName": team[1],
                "AverageScore": avgScore,
                "MaxScore": maxScore,
                "AllScores": allScores
            })

        team_data = sorted(team_data, key=lambda team: team["TeamNumber"])
        team_data = sorted(
            team_data, key=lambda team: team["AllScores"], reverse=True)

        conn_global.close()
        return json.dumps(team_data)

    @cherrypy.expose
    def GPScore(self):
        html = ""
        conn_global = sql.connect("data.db")
        cur_global = conn_global.cursor()

        teams = cur_global.execute("select * from teams").fetchall()
        team_data = []
        for team in teams:
            GPScore = cur_global.execute(
                "select avg(GPScore) from matches where team = ?", (team[0],)).fetchall()[0][0]
            GPScore = 0 if GPScore == None else GPScore
            team_data.append(GPScore)
            html += str(team[0]) + " - " + str(GPScore) + "<br>"

        return html

    @cherrypy.expose
    def playoff_api(self):
        def get_winners(cur):
            winners = {}
            max_match = cur.execute(
                "SELECT MAX(match_number) FROM playoff_structure").fetchall()[0][0]
            for match in range(1, max_match + 1):
                results = cur.execute(
                    "SELECT team FROM matches WHERE match=? ORDER BY score DESC, precisionTokens DESC, GPScore DESC, team ASC", (match,)).fetchall()
                if len(results) >= 2:
                    winners[match] = results[0][0]
            return (winners)

        def get_name(cur, team):
            return cur.execute("SELECT TeamName FROM teams WHERE TeamNumber=?", (team,)).fetchall()[0][0]

        conn = sql.connect("data.db")
        cur = conn.cursor()

        # Get max stage
        max_stage = cur.execute(
            "SELECT MAX(stage) FROM playoff_structure").fetchall()[0][0]

        # Get start time and cycle time
        start_time = config.playoffs_starttime
        cycle_time = config.playoffs_cycletime

        # Determine winners
        winners = get_winners(cur)

        # Fetch base matches
        matches = cur.execute(
            "SELECT match_number,schedule_number,stage,team1,team2 FROM playoff_structure ORDER BY match_number").fetchall()
        for i in range(len(matches)):
            matches[i] = {"number": matches[i][0], "schedule_number": matches[i][1],
                          "stage": matches[i][2], "team1": matches[i][3], "team2": matches[i][4]}

        # Convert to output format
        matches_output = []
        matches_sides = {}
        for match in matches[::-1]:
            output = {"match": match["number"], "inputs": [], "winner": 0}

            # Add teams and inputs
            for key in ["team1", "team2"]:
                if match[key][:1] == "w":
                    source_match = cur.execute(
                        "SELECT match_number FROM playoff_structure WHERE id=? LIMIT 1", (match[key][1:],)).fetchall()[0][0]
                    output["inputs"].append(source_match)
                    if source_match in winners:
                        output[key] = str(winners[source_match])
                        output[key + "Name"] = str(get_name(cur, winners[source_match]))
                    else:
                        output[key] = ""
                        output[key + "Name"] = ""
                else:
                    output[key] = str(match[key])
                    output[key + "Name"] = str(get_name(cur, match[key]))

                # Get score
                if output[key] != "":
                    score = cur.execute("SELECT score FROM matches WHERE match=? AND team=? LIMIT 1", (
                        match["number"], output[key])).fetchall()
                    if len(score) > 0:
                        output[key] += " - " + str(score[0][0]) + " pts"
                        output[key + "Name"] += " - " + str(score[0][0]) + " pts"

            # Add winner
            if match["number"] in winners and output["team1"] != "" and output["team2"] != "":
                if winners[match["number"]] == int(output["team1"].split(" - ")[0]):
                    output["winner"] = 1
                elif winners[match["number"]] == int(output["team2"].split(" - ")[0]):
                    output["winner"] = 2
                else:
                    output["winner"] = 0

            # Add column
            if match["stage"] == max_stage:
                if len(output["inputs"]) >= 1:
                    matches_sides[output["inputs"][0]] = "left"
                if len(output["inputs"]) >= 2:
                    matches_sides[output["inputs"][1]] = "right"
                output["column"] = 0
            else:
                if matches_sides[match["number"]] == "left":
                    output["column"] = match["stage"] - max_stage
                else:
                    output["column"] = max_stage - match["stage"]
                for i in output["inputs"]:
                    matches_sides[i] = matches_sides[match["number"]]

            # Function for rendering time w/o padding
            def convert_time(timestamp):
                hour = datetime.fromtimestamp(timestamp).strftime("%I")
                while hour[:1] == "0":
                    hour = hour[1:]
                minute_string = ":%M"
                return (hour + datetime.fromtimestamp(timestamp).strftime(minute_string))

            # Add time
            match_start = start_time + \
                ((match["schedule_number"] - 1) * cycle_time)
            match_end = start_time + (match["schedule_number"] * cycle_time)
            output["time"] = convert_time(
                match_start) + "-" + convert_time(match_end)

            matches_output.append(output)

        conn.close()
        return json.dumps(matches_output)


# WebSocket handling
current_match_index = 0
timer_start = None
websocket_clients = []


def websocket_send_timer_thread():
    global timer_start
    global websocket_clients
    while True:
        time.sleep(0.1)
        data = None
        if timer_start != None:
            elapsed_time = time.time() - timer_start
            if elapsed_time > 150:
                data = 0
            else:
                data = 150 - math.floor(elapsed_time)
        message = TextMessage(json.dumps({"type": "timer", "data": data}))
        for client in websocket_clients:
            client.send(message)


def websocket_send_matches():
    global current_match
    conn = sql.connect("data.db")
    cur = conn.cursor()
    matches = cur.execute("SELECT * FROM match_schedule").fetchall()[current_match_index:]
    matches = [{
        "number": x[0],
        "field": x[1],
        "teamNumbers": [x[2], x[3]],
        "teamNames":[(cur.execute("SELECT TeamName FROM teams WHERE TeamNumber=?", (x[2],)).fetchall()[0][0] if x[2] != -1 else ""), (cur.execute("SELECT TeamName FROM teams WHERE TeamNumber=?", (x[3],)).fetchall()[0][0] if x[3] != -1 else "")]
    } for x in matches]
    conn.close()
    message = TextMessage(json.dumps({"type": "matches", "data": matches}))
    for client in websocket_clients:
        client.send(message)


class WebSocketHandler(WebSocket):
    def _save_data(self):
        global current_match_index
        global timer_start
        state = {
            "match": current_match_index,
            "starttime": timer_start
        }
        open("timer_status.txt", "w").write(json.dumps(state))

    def received_message(self, message):
        global current_match_index
        global timer_start
        message = json.loads(str(message))
        if message["type"] == "start":
            timer_start = time.time()
        elif message["type"] == "reset":
            timer_start = None
        elif message["type"] == "changematch":
            timer_start = None
            current_match_index += message["data"]
            if current_match_index < 0:
                current_match_index = 0
            websocket_send_matches()
        self._save_data()

    def opened(self):
        cherrypy.log("WebSocket connection opened from \"" + self.peer_address[0] + "\"")
        websocket_clients.append(self)
        websocket_send_matches()

    def closed(self, code, _):
        cherrypy.log("WebSocket connection closed from \"" + self.peer_address[0] + "\"")
        websocket_clients.remove(self)


if __name__ == '__main__':
    if os.path.exists("timer_status.txt"):
        timer_state = json.loads(open("timer_status.txt", "r").read())
        current_match_index = timer_state["match"]
        timer_start = timer_state["starttime"]
    threading.Thread(target=websocket_send_timer_thread, daemon=True).start()
    WebSocketPlugin(cherrypy.engine).subscribe()
    cherrypy.tools.websocket = WebSocketTool()
    cherrypy.config.update(
        {"server.socket_port": 8080, "server.socket_host": "0.0.0.0"})
    cherrypy.quickstart(Root(), '/', config={
        "/static": {
            'tools.staticdir.on': True,
            "tools.staticdir.dir": os.getcwd() + os.path.sep + "static"
        },
        "/ws": {
            "tools.websocket.on": True,
            "tools.websocket.handler_cls": WebSocketHandler
        }
    })
