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
        user = users.get_current_user()
        authz = Authz(user)
        self.response.headers["Content-type"] = "application/json"
        
        try:
            # get the list of trips to show the user
            trips = authz.listTrips()
            
            # return trips to the user
            output = GqlEncoder().encode(trips)
        except Exception as e:
            logging.exception(e)
            errors.append({"message":"Unexpected error listing trips"})
        
        if len(errors) > 0:
            self.response.set_status(400);
            output = json.dumps({"error":errors})
        
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
        #logging.debug(self.request.body)
        
        data = TripUnpacker().unpack_post(self.request)
        #logging.debug(data)
        
        if data['name'] == "" or data['password'] == "":
            errors.append({"message":"Trip name and password are required."})
        else:
            try:
                trip = Trip(name=data['name'],
                            password=data['password'],
                            owner=user)
                
                # get traveler names
                raw_travelers = data['travelers']
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
                #logging.debug("start date = " + str(start_date.date()))
                trip.end_date = end_date.date()
                #logging.debug("end date = " + str(end_date.date()))
                
                trip.put()
                
                output = GqlEncoder().encode({
                    "id":"%s" % trip.key(),
                    'modify_date':trip.modify_date,
                    'start_date':trip.start_date,
                    'end_date':trip.end_date,
                })
            except Exception as e:
                logging.exception(e)
                errors.append({"message":"Unexpected error creating trip"})

        if len(errors) > 0:
            self.response.set_status(400);
            output = json.dumps({"error":errors})

        self.response.out.write(output)
    
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
        logging.debug(self.request.body)
        try:
            data = TripUnpacker().unpack_put(self.request)
            logging.debug(data)
            
            properties = ('name', 'password', 'start_date', 'end_date', 'travelers')
            for prop in properties:
                if prop in data:
                    # TODO: validate the data (for instance, dates will almost
                    #       certainly fail without some scrubbing)
                    scrubbed = self._scrub(prop, data[prop])
                    setattr(trip, prop, scrubbed)
            
            trip.put()
            
            # per the Backbone documentation, this method needs to:
            #   "[w]hen returning a JSON response, send down the attributes of
            #   the model that have been changed by the server, and need to be
            #   updated on the client"
            # Dates need to be shown because their formatting can change
            output = GqlEncoder().encode({
                'modify_date':trip.modify_date,
                'start_date':trip.start_date,
                'end_date':trip.end_date,
            })
                    
        except NotImplementedError as e:
            errors.append({"message":e.args})
        except db.BadValueError as e:
            errors.append({"message":e.args})
        except Exception as e:
            logging.exception(e)
            errors.append({"message":"Unexpected error updating trip"})
        
        if len(errors) > 0:
            self.response.set_status(400);
            output = json.dumps({"error":errors})
            
        self.response.out.write(output)
            
    def _scrub(self, property, val):
        # TODO: scrub data according to the property name
        if property in ["start_date", "end_date"]:
            return dateparse(val).date()
        return val
    
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
            
            # delete related expenses
            try:
                expenses = Expense.all()
                expenses.ancestor(trip)
                expenses.fetch(limit=200)
                db.delete(expenses)
            except Exception as e:
                logging.exception(e)
                errors.append({"message":"Unexpected error deleting associated expenses"})
                
            # delete the trip
            trip.delete()
            
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
        data = ExpenseUnpacker().unpack_post(self.request)

        if data['description'] == "" or data['value'] == "" or data['payer'] == "":
            errors.append({"message":"Description, value, and payer are required."})
        elif len(data['travelers']) == 0:
            errors.append({"message":"At least one person must be specified as a traveler."})
        else:            
            try:
                expense = Expense(
                    parent=trip.key(),
                    creator=user,
                    description=data['description'],
                    value=int(data['value']),
                    currency="USD",
                )
                
                # get the expense date
                expense_date = dateparse(data['expense_date'])
                expense.expense_date = expense_date.date()
                
                # TODO: make sure these travelers are actually on the trip
                expense.travelers = data['travelers']
                
                # TODO: ensure the payer is actually a traveler
                expense.payer = data['payer']
                
                expense.put()
                
                output = GqlEncoder().encode({
                    "id":"%s" % expense.key(),
                    'modify_date':expense.modify_date,
                    'expense_date':expense.expense_date,
                    'value':expense.value,
                })
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
    
    def put(self, trip_key, expense_key):
        #TODO: allow updates
        pass

    def delete(self, trip_key, expense_key):
        errors = []
        output = ""
        user = users.get_current_user()
        authz = Authz(user)
        self.response.headers["Content-type"] = "application/json"

        try:
            # get the expense
            expense = Expense.get(expense_key)
            
            # verify the user is authorized to delete the expense
            authz.deleteExpense(expense)
            
            # delete the expense
            expense.delete()
                
        except db.BadKeyError:
            errors.append({"message":"Invalid expense key"})
        except PermissionError:
            errors.append({"message":"You are not authorized to delete that expense"})
        except db.NotSavedError:
            errors.append({"message":"Unable to delete expense"})
        except Exception as e:
            logging.exception(e)
            errors.append({"message":"Unexpected error deleting expense"})
        
        if len(errors) > 0:
            self.response.set_status(400);
            output = json.dumps({"error":errors})
            
        self.response.out.write(output)

class Unpacker:
    """Handles unpacking of POST and PUT request data into a Python object"""
    def __init__(self, scalars=None, vectors=None):
        self.scalars = scalars
        self.vectors = vectors
        
    def unpack_put(self, request):
        """Unpack the request body for a PUT request"""
        
        # TODO: verify that appropriate scalars and vectors are found
        if request.headers['Content-type'] == 'application/json':
            data = json.loads(request.body)
        else:
            raise NotImplementedError("PUT only accepts JSON-formatted data")
        
        return data

    def unpack_post(self, request):
        """Unpack the POST request body whether it's form-encoded or JSON"""
        
        # TODO: it makes me nervous that in my POST functions,
        #       I use an empty string for data not sent by the app.  These
        #       should probably be None instead
        
        if request.headers['Content-type'].startswith('application/json'):
            logging.debug("Unpacking POST as JSON")
            data = json.loads(request.body)
            for key in self.scalars:
                if not key in data:
                    data[key] = ""
            for key in self.vectors:
                if not key in data:
                    data[key] = []
        else:
            logging.debug("Unpacking POST as form-encoded")
            data = dict([(key,request.get(key)) for key in self.scalars])
            data.update( dict([(key,request.get_all(key)) for key in self.vectors]) )
        
        return data

class TripUnpacker(Unpacker):
    """Specialized unpacker for Trip data"""
    def __init__(self):
        Unpacker.__init__(
            self,
            scalars=('name', 'password', 'start_date', 'end_date'),
            vectors=('travelers', )
        )

class ExpenseUnpacker(Unpacker):
    """Specialized unpacker for Expense data"""
    def __init__(self):
        Unpacker.__init__(
            self,
            scalars=('currency', 'description', 'expense_date', 'payer', 'value'),
            vectors=('travelers', )
        )

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
