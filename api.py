#!/usr/bin/env python
# 
# (C) 2011 Matt Cooper <vtbassmatt@gmail.com>
# TripSplitter RESTful API

# Python
import webapp2
import logging
import json

# AppEngine
from google.appengine.api import users
from google.appengine.ext import db

# Deps
from deps.dateutil.parser import parse as dateparse

# Local
from models import Trip, Expense
from infra.jsonextension import GqlEncoder
from infra.authz import Authz, PermissionError
from config import Config

class TripListHandler(webapp2.RequestHandler):
    def get(self):
        errors = []
        output = ""
        
        try:
            # determine what trips to show this user
            # TODO: authorized users can see more trips than just their own
            user = users.get_current_user()
            trips = Trip.all()
            trips.filter('owner = ', user)
            
            # return 10 trips to the user
            output = GqlEncoder().encode(trips.fetch(limit=10))
        except Exception as e:
            logging.exception(e)
            errors.append({"message":"Unexpected error listing trips"})
        
        if len(errors) > 0:
            output = json.dumps({"error":errors})
        
        self.response.headers["Content-type"] = "application/json"
        self.response.out.write(output)

class TripHandler(webapp2.RequestHandler):
    def get(self, trip_key):
        
        errors = []
        output = ""
        user = users.get_current_user()
        authz = Authz(user)
        self.response.headers["Content-type"] = "application/json"

        if trip_key == "new":
            self.response.headers["Content-type"] = "text/html"
            try:
                authz.createTrip()
                output = self._form_html()
            except PermissionError:
                output = "You are not authorized to create trips."

        else:
            try:
                # get the trip
                trip = Trip.get(trip_key)
                
                # verify the user is authorized to read the trip
                authz.readTrip(trip)
                
                # format trip data
                output = GqlEncoder().encode(trip)
                    
            except db.BadKeyError:
                errors.append({"message":"Invalid trip key"})
            except PermissionError:
                errors.append({"message":"You are not authorized to view that trip"})            
            except Exception as e:
                logging.exception(e)
                errors.append({"message":"Unexpected error loading trip"})
        
        if len(errors) > 0:
            output = json.dumps({"error":errors})
            
        self.response.out.write(output)
    
    def _form_html(self):
        """Scaffolding - allows creating a new trip"""
        post_url = webapp2.uri_for('trip', trip_key='new')
        return """<html><body>
    <h1>New Trip</h1>
    <form action="%s" method="post">
        <div>Trip Name: <input type="text" name="name"/>*</div>
        <div>Trip Password: <input type="text" name="password"/>*</div>
        <div>Start Date: <input type="text" name="startdate"/></div>
        <div>End Date: <input type="text" name="enddate"/></div>
        <ul>
        <li>Traveler: <input type="text" name="traveler"/></li>
        <li>Traveler: <input type="text" name="traveler"/></li>
        <li>Traveler: <input type="text" name="traveler"/></li>
        <li>Traveler: <input type="text" name="traveler"/></li>
        <li>Traveler: <input type="text" name="traveler"/></li>
        <li>Traveler: <input type="text" name="traveler"/></li>
        <li>Traveler: <input type="text" name="traveler"/></li>
        <li>Traveler: <input type="text" name="traveler"/></li>
        <li>Traveler: <input type="text" name="traveler"/></li>
        <li>Traveler: <input type="text" name="traveler"/></li>
        </ul>
        <div><input type="submit" value="Create Trip"/></div>
    </form>
</body></html>
            """ % (post_url,)
    
    def post(self, trip_key):

        errors = []
        output = ""
        user = users.get_current_user()
        authz = Authz(user)
        self.response.headers["Content-type"] = "application/json"
        
        # check for authorization to create new trips & verify this is in fact
        # a request to create a new trip
        try:
            # user allowed to create trips?
            authz.createTrip()
            
            #TODO: allow updates
            if trip_key != 'new':
                raise PermissionError("Updates are not allowed; must create a new trip")
            
        except PermissionError as e:
            # this permission error could have come from authz or locally
            errors.append({"message":e.args})
        
        # bail if we hit authz errors        
        if len(errors) > 0:
            output = json.dumps({"error":errors})
            self.response.out.write(output)
        
        # user is allowed, so go ahead and try to create this thing
        name = self.request.get('name')
        password = self.request.get('password')
        
        if name == "" or password == "":
            errors.append({"message":"Trip name and password are required."})
        else:
            try:
                trip = Trip(name=name,
                            password=password,
                            owner=user)
                
                # get traveler names
                raw_travelers = self.request.get_all("traveler")
                if len(raw_travelers) > Config.limits.travelers_per_trip:
                    logging.warning('Attempt to add too many travelers: %s', user.nickname)
                    raw_travelers = raw_travelers[:Config.limits.travelers_per_trip]
                travelers = []
                for traveler in raw_travelers:
                    if traveler.strip() != "":
                        travelers.append(traveler.strip())
                trip.travelers = travelers
                
                # get dates
                # TODO: validation that these dates are sane and properly ordered
                start_date = dateparse(self.request.get('startdate'))
                end_date = dateparse(self.request.get('enddate'))
                trip.start_date = start_date.date()
                trip.end_date = end_date.date()
                
                trip.put()
                
                output = json.dumps({"key":"%s" % trip.key()})
            except Exception as e:
                logging.exception(e)
                errors.append({"message":"Unexpected error creating trip"})

        if len(errors) > 0:
            output = json.dumps({"error":errors})

        self.response.headers["Content-type"] = "application/json"
        self.response.out.write(output)

class ExpenseListHandler(webapp2.RequestHandler):
    def get(self, trip_key):

        errors = []
        output = ""
        user = users.get_current_user()
        authz = Authz(user)
        self.response.headers["Content-type"] = "application/json"
        
        # verify access to the trip
        try:
            # get the trip
            trip = Trip.get(trip_key)
            
            # verify the user is authorized to read the trip
            authz.readTrip(trip)
            
        except PermissionError:
            errors.append({"message":"You are not authorized to view that trip"})
        except db.BadKeyError:
            errors.append({"message":"Invalid trip key"})
        except Exception as e:
            logging.exception(e)
            errors.append({"message":"Unexpected error loading trip"})
            
        # if errors encountered so far, bail
        if len(errors) > 0:
            output = json.dumps({"error":errors})
            self.response.out.write(output)
            return
        
        # next, get the list of expenses
        try:
            expenses = Expense.all()
            expenses.ancestor(trip)
            output = GqlEncoder().encode(expenses.fetch(limit=200))
        except db.BadKeyError:
            errors.append({"message":"Invalid trip key"})
        except Exception as e:
            logging.exception(e)
            errors.append({"message":"Unexpected error listing expenses"})
        
        if len(errors) > 0:
            output = json.dumps({"errors":errors})
        
        self.response.headers["Content-type"] = "application/json"
        self.response.out.write(output)

class ExpenseHandler(webapp2.RequestHandler):
    def get(self, trip_key, expense_key):
        
        errors = []
        output = ""
        user = users.get_current_user()
        authz = Authz(user)
        self.response.headers["Content-type"] = "application/json"
        
        # first, verify they have access to the trip
        try:
            # get the trip
            trip = Trip.get(trip_key)
            
            # verify the user is authorized to read the trip
            authz.readTrip(trip)
            
        except PermissionError:
            errors.append({"message":"You are not authorized to view that trip"})
        except db.BadKeyError:
            errors.append({"message":"Invalid trip key"})
        except Exception as e:
            logging.exception(e)
            errors.append({"message":"Unexpected error loading trip"})
            
        # if errors encountered so far, bail
        if len(errors) > 0:
            output = json.dumps({"error":errors})
            self.response.out.write(output)
            return

        # next, figure out whether this is a new expense or a read
        if expense_key == "new":
            self.response.headers["Content-type"] = "text/html"
            try:
                authz.createExpense(trip)
                output = self._form_html(trip)
            except PermissionError:
                output = "You are not authorized to create expenses."

        else:
            # this is a read of an existing expense
            # instead of directly authorizing the read of an expense, we
            # ensure that the expense is tied to the specified trip
            try:
                # get the expense
                expense = Expense.get(expense_key)
                
                # ensure the expense belongs to the trip
                if expense.parent_key() != trip.key():
                    raise PermissionError("Expense is not tied to that trip")
                
                # format expense data
                output = GqlEncoder().encode(expense)
                    
            except db.BadKeyError:
                errors.append({"message":"Invalid expense key"})
            except PermissionError as e:
                errors.append({"message":e.args})
            except Exception as e:
                logging.exception(e)
                errors.append({"message":"Unexpected error loading expense"})

        if len(errors) > 0:
            output = json.dumps({"error":errors})
            
        self.response.out.write(output)
    
    def _form_html(self, trip):
        """Scaffolding - allows creating a new expense"""
        post_url = webapp2.uri_for('expense', trip_key=trip.key(), expense_key='new')
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
        %s
        <div><input type="submit" value="Create Expense"/></div>
    </form>
</body></html>
            """ % (trip.name, post_url, traveler_checkboxes)
    
    def post(self, trip_key, expense_key):
        errors = []
        output = ""
        user = users.get_current_user()
        authz = Authz(user)
        self.response.headers["Content-type"] = "application/json"

        # check for authorization to create expenses for this trip & verify this
        # is in fact a request to create a new expense
        try:
            # get the trip
            trip = Trip.get(trip_key)
            
            # verify the user is authorized to create an expense on this trip
            authz.createExpense(trip)
            
            #TODO: allow updates
            if expense_key != 'new':
                raise PermissionError("Updates are not allowed; must create a new expense")
            
        except PermissionError as e:
            # this permission error could have come from authz or locally
            errors.append({"message":e.args})
        except db.BadKeyError:
            errors.append({"message":"Invalid trip key"})
        except Exception as e:
            logging.exception(e)
            errors.append({"message":"Unexpected error loading trip"})
        
        # bail if we hit authz errors        
        if len(errors) > 0:
            output = json.dumps({"error":errors})
            self.response.out.write(output)
            return

        # having passed authz, let's try creating the expense
        desc = self.request.get('desc')
        value = self.request.get('value')

        if desc == "" or value == "":
            errors.append({"message":"Description name and value are required."})
        else:            
            try:
                expense = Expense(
                    parent=trip.key(),
                    creator=user,
                    description=desc,
                    value=int(value),
                    currency="USD",
                )
                
                # get the expense date
                expense_date = dateparse(self.request.get('expensedate'))
                expense.expense_date = expense_date.date()
                
                # TODO: get the right travelers and payer
                expense.travelers = ['Matt', 'Christy']
                expense.payer = user.nickname()
                expense.put()
                
                output = json.dumps({"key":"%s" % expense.key()})
            except Exception as e:
                logging.exception(e)
                errors.append({"message":"Unexpected error creating expense"})
        
        if len(errors) > 0:
            output = json.dumps({"error":errors})

        self.response.headers["Content-type"] = "application/json"
        self.response.out.write(output)

app = webapp2.WSGIApplication([
    webapp2.Route(r'/api/trip',
        handler=TripListHandler, name='trip-list'),
    webapp2.Route(r'/api/trip/<trip_key>',
        handler=TripHandler, name='trip'),
    webapp2.Route(r'/api/trip/<trip_key>/expense',
        handler=ExpenseListHandler, name='expense-list'),
    webapp2.Route(r'/api/trip/<trip_key>/expense/<expense_key>', 
        handler=ExpenseHandler, name='expense'),
        ], debug=True)
