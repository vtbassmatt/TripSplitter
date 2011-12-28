#!/usr/bin/env python
# 
# (C) 2011 Matt Cooper <vtbassmatt@gmail.com>
# TripSplitter configuration

class ConfigObj():
    pass

Config = ConfigObj()
Config.limits = ConfigObj()
#Config.api = ConfigObj()
Config.app = ConfigObj()

# How many travelers will the system accept per trip?
Config.limits.travelers_per_trip = 10

# First API setting will go here
#Config.api.<whatever> = <whatever>

# Determines whether to append -min onto some JavaScript files or not
# Should be True in production but can be moved to False for development
Config.app.use_min = False
