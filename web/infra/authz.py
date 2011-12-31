#!/usr/bin/env python
# 
# (C) 2011 Matt Cooper <vtbassmatt@gmail.com>
# TripSplitter auth-z module

import logging

from google.appengine.api import users
from google.appengine.ext import db

from models import Trip

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
    
    def readTrip(self, trip):
        """Determines whether the user is allowed to read a particular trip
        
        trip can be a trip key or a trip object"""
        
        if isinstance(trip, Trip):
            pass
        else:
            trip = Trip.get(trip)
        
        # logic determining whether the user can read the trip
        if self.user == trip.owner:
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
        if self.user == trip.owner:
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
    


class PermissionError(Exception):
    pass