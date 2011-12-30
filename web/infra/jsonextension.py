#!/usr/bin/env python
# 
# (C) 2011 Matt Cooper <vtbassmatt@gmail.com>
# TripSplitter Model2Json
# Thanks to http://stackoverflow.com/questions/2114659/how-to-serialize-db-model-objects-to-json

import datetime
import time
import json
from google.appengine.api import users
from google.appengine.ext import db

class GqlEncoder(json.JSONEncoder):
    """Extend JSONEncoder to understand GQL results and properties"""
    
    def default(self, obj):
        if hasattr(obj, '__json__'):
            return getattr(obj, '__json__')()
        
        if isinstance(obj, db.GqlQuery):
            return list(obj)
        
        elif isinstance(obj, db.Model):
            properties = obj.properties().items()
            output = {}
            for field, value in properties:
                output[field] = getattr(obj, field)
            output["key"] = "%s" % obj.key()
            return output
        
        elif isinstance(obj, datetime.datetime):
            output = {}
            fields = ['day', 'hour', 'microsecond', 'minute', 'month', 'second', 'year']
            #methods = ['ctime', 'isocalendar', 'isoformat', 'isoweekday', 'timetuple']
            for field in fields:
                output[field] = getattr(obj, field)
            #for method in methods:
            #    output[method] = getattr(obj, method)()
            #output['epoch'] = time.mktime(obj.timetuple())
            return output
        
        elif isinstance(obj, datetime.date):
            output = {}
            fields = ['day', 'month', 'year']
            #methods = ['ctime', 'isocalendar', 'isoformat', 'isoweekday', 'timetuple']
            for field in fields:
                output[field] = getattr(obj, field)
            #for method in methods:
            #    output[method] = getattr(obj, method)()
            #output['epoch'] = time.mktime(obj.timetuple())
            return output
        
        elif isinstance(obj, time.struct_time):
            return list(obj)
        
        elif isinstance(obj, users.User):
            output = {}
            methods = ['nickname', 'email', 'auth_domain']
            for method in methods:
                output[method] = getattr(obj, method)()
            return output
        
        return json.JSONEncoder.default(self, obj)
