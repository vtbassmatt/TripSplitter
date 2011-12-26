#!/usr/bin/env python
# 
# (C) 2011 Matt Cooper <vtbassmatt@gmail.com>
# TripSplitter Main Webapp

import webapp2
from google.appengine.api import users
from google.appengine.ext import db

class RootHandler(webapp2.RequestHandler):
    def get(self, path):
        user = users.get_current_user()
        
        self.response.out.write('<html><body>')
        self.response.out.write('<p>Hello, you&apos;ve reached /%s.</p>' % path)
        self.response.out.write('<p>No one is available to take your call right now.</p>')
        self.response.out.write('<p>Try <a href="/api/trip">the API instead</a>.</p>')
        self.response.out.write('</body></html>')

app = webapp2.WSGIApplication([
    webapp2.Route(r'/<path>', handler=RootHandler),
        ], debug=True)
