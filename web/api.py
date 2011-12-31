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
            self.response.set_status(400);
            output = json.dumps({"error":errors})
        
        self.response.headers["Content-type"] = "application/json"
        self.response.out.write(output)

    def post(self):

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
                        
        except PermissionError as e:
            # this permission error could have come from authz or locally
            errors.append({"message":e.args})
        
        # bail if we hit authz errors        
        if len(errors) > 0:
            self.response.set_status(400);
            output = json.dumps({"error":errors})
            self.response.out.write(output)
            return
        
        # user is allowed, so go ahead and try to create this thing
        logging.debug(self.request.body)
        
        data = self._unpack_post_request()
        logging.debug(data)
        
        if data['name'] == "" or data['password'] == "":
            errors.append({"message":"Trip name and password are required."})
        else:
            try:
                trip = Trip(name=data['name'],
                            password=data['password'],
                            owner=user)
                
                # get traveler names
                raw_travelers = data['traveler']
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
                start_date = dateparse(data['start_date'])
                end_date = dateparse(data['end_date'])
                trip.start_date = start_date.date()
                trip.end_date = end_date.date()
                
                trip.put()
                
                output = json.dumps({"id":"%s" % trip.key()})
            except Exception as e:
                logging.exception(e)
                errors.append({"message":"Unexpected error creating trip"})

        if len(errors) > 0:
            self.response.set_status(400);
            output = json.dumps({"error":errors})

        self.response.headers["Content-type"] = "application/json"
        self.response.out.write(output)
    
    def _unpack_post_request(self):
        """Unpack the request body whether it's form-encoded or JSON"""
        
        # TODO: it makes me nervous that in my POST functions,
        #       I use an empty string for data not sent by the app.  These
        #       should probably be None instead
        
        scalars = ('name', 'password', 'start_date', 'end_date')
        vectors = ('traveler', )
        if self.request.headers['Content-type'].startswith('application/json'):
            data = json.loads(self.request.body)
            for key in scalars:
                if not key in data:
                    data[key] = ""
            for key in vectors:
                if not key in data:
                    data[key] = []
        else:
            data = dict([(key,self.request.get(key)) for key in scalars])
            data.update( dict([(key,self.request.get_all(key)) for key in vectors]) )
        
        return data

class TripHandler(webapp2.RequestHandler):
    def get(self, trip_key):
        
        errors = []
        output = ""
        user = users.get_current_user()
        authz = Authz(user)
        self.response.headers["Content-type"] = "application/json"

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

    def put(self, trip_key):

        errors = []
        output = ""
        user = users.get_current_user()
        authz = Authz(user)
        self.response.headers["Content-type"] = "application/json"

        try:
            # get the trip
            trip = Trip.get(trip_key)
            
            # verify the user is authorized to update the trip
            authz.updateTrip(trip)
            
        except db.BadKeyError:
            errors.append({"message":"Invalid trip key"})
        except PermissionError:
            errors.append({"message":"You are not authorized to view that trip"})            
        except Exception as e:
            logging.exception(e)
            errors.append({"message":"Unexpected error loading trip"})
        
        # bail if we hit authz errors        
        if len(errors) > 0:
            self.response.set_status(400);
            output = json.dumps({"error":errors})
            self.response.out.write(output)
            return
        
        # now that we know the user is authorized, perform the update
        logging.info(self.request.body)
        try:
            data = self._unpack_put_request()
            logging.debug(data)
            
            # TODO: accept these other properties
            properties = ('name', 'password',) #'start_date', 'end_date', 'traveler')
            for prop in properties:
                if prop in data:
                    # TODO: validate the data (for instance, dates will almost
                    #       certainly fail without some scrubbing)
                    setattr(trip, prop, data[prop])
            
            trip.put()
            
            # per the Backbone documentation, this method needs to:
            #   "[w]hen returning a JSON response, send down the attributes of
            #   the model that have been changed by the server, and need to be
            #   updated on the client"
            output = GqlEncoder().encode({'modify_date':trip.modify_date})
                    
        except NotImplementedError as e:
            errors.append({"message":e.args})
        except Exception as e:
            logging.exception(e)
            errors.append({"message":"Unexpected error updating trip"})
        
        if len(errors) > 0:
            self.response.set_status(400);
            output = json.dumps({"error":errors})
            
        self.response.out.write(output)
        
    def _unpack_put_request(self):
        """Translate JSON into a Python object"""
        scalars = ('name', 'password', 'start_date', 'end_date')
        vectors = ('traveler', )
        if self.request.headers['Content-type'] == 'application/json':
            data = json.loads(self.request.body)
        else:
            raise NotImplementedError("PUT only accepts JSON-formatted data")
        
        return data
    
    def delete(self, trip_key):
        
        errors = []
        output = ""
        user = users.get_current_user()
        authz = Authz(user)
        self.response.headers["Content-type"] = "application/json"

        try:
            # get the trip
            trip = Trip.get(trip_key)
            
            # verify the user is authorized to delete the trip
            authz.deleteTrip(trip)
            
            # delete the trip
            trip.delete()
            
            # TODO: delete related expenses
                
        except db.BadKeyError:
            errors.append({"message":"Invalid trip key"})
        except PermissionError:
            errors.append({"message":"You are not authorized to delete that trip"})
        except db.NotSavedError:
            errors.append({"message":"Unable to delete trip"})
        except Exception as e:
            logging.exception(e)
            errors.append({"message":"Unexpected error deleting trip"})
        
        if len(errors) > 0:
            self.response.set_status(400);
            output = json.dumps({"error":errors})
            
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
            self.response.set_status(400);
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
            self.response.set_status(400);
            output = json.dumps({"errors":errors})
        
        self.response.headers["Content-type"] = "application/json"
        self.response.out.write(output)

    def post(self, trip_key):
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
            self.response.set_status(400);
            output = json.dumps({"error":errors})
            self.response.out.write(output)
            return

        # having passed authz, let's try creating the expense
        desc = self.request.get('desc')
        value = self.request.get('value')
        payer = self.request.get('payer')
        travelers = self.request.get_all('traveler')

        if desc == "" or value == "" or payer == "":
            errors.append({"message":"Description name, value, and payer are required."})
        elif len(travelers) == 0:
            errors.append({"message":"At least one person must be specified as a traveler."})
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
                
                # TODO: make sure these travelers are actually on the trip
                expense.travelers = travelers
                
                # TODO: ensure the payer is actually a traveler
                expense.payer = payer
                
                expense.put()
                
                output = json.dumps({"id":"%s" % expense.key()})
            except Exception as e:
                logging.exception(e)
                errors.append({"message":"Unexpected error creating expense"})
        
        if len(errors) > 0:
            self.response.set_status(400);
            output = json.dumps({"error":errors})

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
            self.response.set_status(400);
            output = json.dumps({"error":errors})
            self.response.out.write(output)
            return


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
            self.response.set_status(400);
            output = json.dumps({"error":errors})
            
        self.response.out.write(output)
    
    #def put(self, trip_key):
    #    TODO: allow updates
    #    pass


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
