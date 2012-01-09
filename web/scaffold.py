#!/usr/bin/env python
# 
# (C) 2011 Matt Cooper <vtbassmatt@gmail.com>
# TripSplitter scaffolding

import webapp2
from google.appengine.api import users
from models import Trip

class ScaffoldHandler(webapp2.RequestHandler):
    def get(self, path):
        user = users.get_current_user()
        
        self.response.out.write('<html><body>')
        self.response.out.write('<h1>SCAFFOLD</h1>')
        if path == 'trip':
            self.response.out.write(self._tripScaffold())
        elif path[:7] == 'expense':
            self.response.out.write(self._expenseScaffold(path[8:]))
        else:
            self.response.out.write('<div>Whoops, I don\'t recognize "%s".</div>' % path)
        self.response.out.write('</body></html>')
    
    def _tripScaffold(self):
        """Scaffolding - allows creating a new trip"""
        post_url = '/api/trip'
        return """<html><body>
    <h2>New Trip</h2>
    <form action="%s" method="post">
        <div>Trip Name: <input type="text" name="name"/>*</div>
        <div>Trip Password: <input type="text" name="password"/>*</div>
        <div>Start Date: <input type="text" name="start_date"/></div>
        <div>End Date: <input type="text" name="end_date"/></div>
        <ul>
        <li>Traveler: <input type="text" name="travelers"/></li>
        <li>Traveler: <input type="text" name="travelers"/></li>
        <li>Traveler: <input type="text" name="travelers"/></li>
        <li>Traveler: <input type="text" name="travelers"/></li>
        <li>Traveler: <input type="text" name="travelers"/></li>
        <li>Traveler: <input type="text" name="travelers"/></li>
        <li>Traveler: <input type="text" name="travelers"/></li>
        <li>Traveler: <input type="text" name="travelers"/></li>
        <li>Traveler: <input type="text" name="travelers"/></li>
        <li>Traveler: <input type="text" name="travelers"/></li>
        </ul>
        <div><input type="submit" value="Create Trip"/></div>
    </form>
</body></html>
            """ % (post_url,)

    def _expenseScaffold(self, trip_key):
        if trip_key == '':
            return "Pass in a trip key like this:  /expense<u>$tripkey</u>"
            
        trip = Trip.get(trip_key)
        
        return self._expenseScaffoldInternal(trip)
        
    def _expenseScaffoldInternal(self, trip):
        """Scaffolding - allows creating a new expense"""
        post_url = '/api/trip/%s/expense' % trip.key()
        
        traveler_dropdown_src = """<option value="%s">%s</option>"""
        traveler_dropdown = "".join(
            [traveler_dropdown_src % (str,str) for str in trip.travelers])
        
        traveler_checkboxes_src = """        <div>
            <input type="checkbox" name="traveler" value="%s" checked>
            <label for="traveler">%s</label>
        </div>"""
        traveler_checkboxes = "".join(
            [traveler_checkboxes_src % (str,str) for str in trip.travelers])
        
        return """<html><body>
    <h1>New Expense for '%s'</h1>
    <form action="%s" method="post">
        <div>Expense: <input type="text" name="desc"/>*</div>
        <div>Cost: $<input type="text" name="value"/>*</div>
        <div>Date: <input type="text" name="expensedate"/></div>
        <div>Payer: <select name="payer">%s</select>*</div>
        <div>Consumers:
        %s
        </div>
        <div><input type="submit" value="Create Expense"/></div>
    </form>
</body></html>
            """ % (trip.name, post_url, traveler_dropdown, traveler_checkboxes)


app = webapp2.WSGIApplication([
    webapp2.Route(r'/scaffold/<path>', handler=ScaffoldHandler),
        ], debug=True)
