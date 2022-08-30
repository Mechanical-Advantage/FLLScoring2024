import random
import string
import cherrypy
import os 
from pathlib import Path 

class StringMaker(object):
   @cherrypy.expose
   def index(self):
      return "Hello! How are you?"
   
   @cherrypy.expose
   def generate(self, length=9):
      return ''.join(random.sample(string.hexdigits, int(length)))

   @cherrypy.expose
   def greeting(self, name):
       return "Hello " + name + "!"
	
   @cherrypy.expose
   def saveMatch(self, team, match, referee, table, score, GPScore, teamInitials, precisionTokens):
        print("Team: " + team + "\nMatch: " + match + "\nReferee:  " +  referee + "\nTable: " + table + "\nScore " + score + "\nGPScore " + GPScore + "\nTeam Initials: " + teamInitials + "\nPrecision Tokens: " + precisionTokens)
        
        conn_global = sql.connect(db_global)
        cur_global = conn_global.cursor()
        cur_global.execute(
            "INSERT INTO matches(team, match, referee, table, score, GPScore, teamInitials, precisionTokens) VALUES (team, match, referee, table, score, GPScore, teamInitials, precisionTokens)")
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

