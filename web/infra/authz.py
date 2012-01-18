#!/usr/bin/env python
# 
# (C) 2011 Matt Cooper <vtbassmatt@gmail.com>
# TripSplitter auth-z module

import logging

from google.appengine.api import users
from google.appengine.ext import db

from models import Trip, Expense, TripAccess

class Authz():
    """Authorization manager.  Member methods allow other aspects of the
    application to check permissions for various functions.  The method
    will either silently return if the action is allowed, or throw a
    PermissionError if disallowed"""
    def __init__(self, user = None):
        if user == None:
            self.user = users.get_current_user()
        else:
            self.user = user
        
        if not isinstance(self.user, users.User):
            raise Exception('Authz requires a logged-in user')
    
    def useApp(self):
        """Determines whether the user can access the app"""
        # could block people out entirely here - simply raise PermissionError
        return
    
    def listTrips(self):
        """Give back a list of trips the user can read"""
        # pull 10 of the user's own trips
        my_trips_query = Trip.all()
        my_trips_query.filter('owner = ', self.user)        
        my_trips = my_trips_query.fetch(limit=10)
        
        # pull 10 more trips the user can read
        tripaccess_query = TripAccess.all()
        tripaccess_query.filter('user = ', self.user)
        tripaccess = tripaccess_query.fetch(limit=10)
        for access in tripaccess:
            my_trips.append(access.trip)
        
        return my_trips
    
    def readTrip(self, trip):
        """Determines whether the user is allowed to read a particular trip
        
        trip can be a trip key or a trip object"""
        
        if isinstance(trip, Trip):
            pass
        else:
            trip = Trip.get(trip)
        
        # logic determining whether the user can read the trip
        # if the user is the owner, OK
        if self.user == trip.owner:
            return
        # if there is a TripAccess object, OK
        tripaccess_query = TripAccess.all()
        tripaccess_query.filter('user = ', self.user)
        tripaccess_query.filter('trip = ', trip)
        tripaccess = tripaccess_query.fetch(limit=10)
        if len(tripaccess) > 0:
            return
        
        raise PermissionError('User not allowed to read this trip')
    
    def createTrip(self):
        """Determines whether the user is allowed to create trips"""
        try:
            self.useApp()
        except PermissionError:
            raise PermissionError('User cannot create trips')
    
    def updateTrip(self, trip):
        """Determines whether the user is allowed to update a particular trip
        
        trip can be a trip key or a trip object"""
        if isinstance(trip, Trip):
            pass
        else:
            trip = Trip.get(trip)
        
        # logic determining whether the user can update the trip
        # if the user is the owner, OK
        if self.user == trip.owner:
            return
        # if there is a TripAccess object, OK
        tripaccess_query = TripAccess.all()
        tripaccess_query.filter('user = ', self.user)
        tripaccess_query.filter('trip = ', trip)
        tripaccess = tripaccess_query.fetch(limit=10)
        if len(tripaccess) > 0:
            return
        
        raise PermissionError('User not allowed to update this trip')
    
    def deleteTrip(self, trip):
        """Determines whether the user is allowed to delete a particular trip
        
        trip can be a trip key or a trip object"""
        if isinstance(trip, Trip):
            pass
        else:
            trip = Trip.get(trip)
        
        # logic determining whether the user can delete the trip
        if self.user == trip.owner:
            return
        
        raise PermissionError('User not allowed to delete this trip')
    
    def createExpense(self, trip):
        """Determines whether the user is allowed to create expenses for a trip"""
        try:
            self.updateTrip(trip)
        except PermissionError:
            raise PermissionError('User cannot create expenses for this trip')
    
    def deleteExpense(self, expense):
        """Determines whether the user is allowed to delete an expense"""
        if isinstance(expense, Expense):
            pass
        else:
            expense = Expense.get(expense)
        
        # determine if the user owns the related trip
        try:
            trip = Trip.get(expense.parent_key())
        except db.BadKeyError:
            raise PermissionError('User cannot delete this expense because the trip could not be loaded')
            
        if self.user == trip.owner:
            return

        raise PermissionError('User cannot delete this expense')
    


class PermissionError(Exception):
    pass