#!/usr/bin/env python
# 
# (C) 2011 Matt Cooper <vtbassmatt@gmail.com>
# TripSplitter Homepage

import webapp2
from google.appengine.api import users

class MainHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        
        if user:
            greeting = "Hello %s" % user.nickname()
            see_trips = '<a href="/app">Go to the app</a>'
            login_link = '<a href="%s">%s</a>' % (users.create_logout_url("/"), "Log out")
        else:
            greeting = "Hello."
            see_trips = 'You must login first.'
            login_link = '<a href="%s">%s</a>' % (users.create_login_url("/"), "Log in")
            
        self.response.out.write("""
        <html><body>
        <p>%s</p>
        <p>%s</p>
        <p>%s</p>
        </body></html>""" % (greeting, login_link, see_trips))

app = webapp2.WSGIApplication([
    webapp2.Route(r'/', handler=MainHandler),
        ], debug=True)
