#!/usr/bin/env python

__author__      = "Vishal Patil"
__copyright__   = "Copyright 2010 - 2011, Vishal Patil"
__license__     = "New-style BSD"

class Action(object):
	def execute(self, parameter):
		raise NotImplementedError
