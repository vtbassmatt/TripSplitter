#!/usr/bin/env python
# 
# (C) 2011 Matt Cooper <vtbassmatt@gmail.com>
# TripSplitter Models

from google.appengine.api import users
from google.appengine.ext import db

class Trip(db.Model):
    name = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    owner = db.UserProperty(required=True)
    start_date = db.DateProperty()
    end_date = db.DateProperty()
    create_date = db.DateProperty(auto_now_add=True)
    modify_date = db.DateProperty(auto_now=True)
    travelers = db.StringListProperty()

class Expense(db.Model):
    creator = db.UserProperty(required=True)
    payer = db.StringProperty()
    description = db.StringProperty(required=True)
    create_date = db.DateProperty(auto_now_add=True)
    modify_date = db.DateProperty(auto_now=True)
    expense_date = db.DateProperty(auto_now_add=True)
    value = db.IntegerProperty(required=True)
    currency = db.StringProperty(required=True)
    travelers = db.StringListProperty()
