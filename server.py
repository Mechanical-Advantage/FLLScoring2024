import random
import string
import cherrypy
import os 
from pathlib import Path 
import sqlite3 as sql

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
        print("Team: " + team + "\nMatch: " + match + "\nReferee:  " +  referee + "\nfield: " + field + "\nScore " + score + "\nGPScore " + GPScore + "\nTeam Initials: " + teamInitials + "\nPrecision Tokens: " + precisionTokens)
        
        conn_global = sql.connect("data.db")
        cur_global = conn_global.cursor()
        cur_global.execute(
            "INSERT INTO matches(team, match, referee, field, score, GPScore, teamInitials, precisionTokens) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(team, match, referee, field, score, GPScore, teamInitials, precisionTokens))
        conn_global.commit()
        conn_global.close()
        return
        
if __name__ == '__main__':
    cherrypy.config.update(
            {"server.socket_port":8080, "server.socket_host": "0.0.0.0"})
    cherrypy.quickstart(StringMaker (), '/', config={
        "/static": {
            'tools.staticdir.on' : True,
            "tools.staticdir.dir": os.getcwd() + "\\static"
        }
    })

