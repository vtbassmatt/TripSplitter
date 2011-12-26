#!/usr/bin/env python
# 
# (C) 2011 Matt Cooper <vtbassmatt@gmail.com>
# TripSplitter configuration

class ConfigObj():
    pass

Config = ConfigObj()
Config.limits = ConfigObj()
#Config.api = ConfigObj()

Config.limits.travelers_per_trip = 10