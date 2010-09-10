#!/usr/bin/env python

from action import Action
from states import Statechart

class Event(object):
    def __init__(self, id):
        self.id = id

    def __eq__(self, event):
        if event == None:
            return False                

        return self.id == event.id

    def __ne__(self, event):
        return not self.__eq__(event)

    def __str__(self):
        return "Event:%s" % str(self.id)

class Guard(object):
	def check(self, runtime, param):
		raise NotImplementedError


