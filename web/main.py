#!/usr/bin/env python
# 
# (C) 2011 Matt Cooper <vtbassmatt@gmail.com>
# TripSplitter Main Webapp

import os

import webapp2
import jinja2

from config import Config

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'))

class RootHandler(webapp2.RequestHandler):
    def get(self, path):
        self.response.out.write('<html><body>')
        self.response.out.write('<p>Hello, you&apos;ve reached /%s.</p>' % path)
        self.response.out.write('<p>No one is available to take your call right now.</p>')
        self.response.out.write('<p>Try <a href="/app">the app instead</a>.</p>')
        self.response.out.write('</body></html>')

class AppHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        # set self.request, self.response, and self.app
        # per the webapp2 documentation
        self.initialize(request, response)
        
        # figure out the appropriate scripts to include
        (use_min, static_dir) = (Config.app.use_min, Config.app.static_dir)
        underscore = 'underscore'
        backbone = 'backbone'
        if use_min:
            underscore += '-min'
            backbone += '-min'
        underscore += '.js'
        backbone += '.js'
        
        # build the template_boilerplate object
        self.template_boilerplate = {
            'underscore_js': static_dir + underscore,
            'jquery_js': static_dir + 'jquery-1.7.1.min.js',
            'json2_js': static_dir + 'json2.js',
            'backbone_js': static_dir + backbone,
            'tripsplitter_js': static_dir + 'tripsplitter.js',
            'index_css': static_dir + 'index.css',
        }
    
    def get(self):
        template_values = {
        #    'test': 'test!',
        }
        # add appropriate scripts, styles, etc. to the template vars
        template_values.update(self.template_boilerplate)
        
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([
    webapp2.Route(r'/app', handler=AppHandler),
    webapp2.Route(r'/<path>', handler=RootHandler),
        ], debug=True)
