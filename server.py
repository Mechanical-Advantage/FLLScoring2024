import random
import string
import cherrypy
import os
from pathlib import Path
import sqlite3 as sql
import json


class StringMaker(object):
    @cherrypy.expose
    def index(self):
        return

    @cherrypy.expose
    def generate(self, length=9):
        return ''.join(random.sample(string.hexdigits, int(length)))

    @cherrypy.expose
    def greeting(self, name):
        return "Hello " + name + "!"

    @cherrypy.expose
    def saveMatch(self, team, match, referee, field, score, GPScore, teamInitials, precisionTokens):
        print("Team: " + team + "\nMatch: " + match + "\nReferee:  " + referee + "\nfield: " + field + "\nScore " +
              score + "\nGPScore " + GPScore + "\nTeam Initials: " + teamInitials + "\nPrecision Tokens: " + precisionTokens)

        conn_global = sql.connect("data.db")
        cur_global = conn_global.cursor()
        cur_global.execute(
            "INSERT INTO matches(team, match, referee, field, score, GPScore, teamInitials, precisionTokens) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (team, match, referee, field, score, GPScore, teamInitials, precisionTokens))
        conn_global.commit()
        conn_global.close()
        return

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

if __name__ == '__main__':
    cherrypy.config.update(
        {"server.socket_port": 8080, "server.socket_host": "0.0.0.0"})
    cherrypy.quickstart(StringMaker(), '/', config={
        "/static": {
            'tools.staticdir.on': True,
            "tools.staticdir.dir": os.getcwd() + os.path.sep + "static"
        }
    })
