#!/usr/bin/env python

__author__      = "Vishal Patil"
__copyright__   = "Copyright 2010 - 2011, Vishal Patil"
__license__     = "New-style BSD"

class StateRuntimeData(object):

    def __init__(self):
        self.current_state = None
        self.state_set = list()

class RuntimeData(object):

    def __init__(self):
        self.active_states = {}
        self.history_states = {}
        self.transition = None
        self.event = None

    def is_active(self, state):
        status = False

        if state in self.active_states:
            status = True 

        return status

    def activate(self, state):
        if not (state in self.active_states):
            self.active_states[state] = StateRuntimeData()

        data = self.active_states[state]			
        data.current_state = None

        if state.context:
            assert self.active_states.has_key(state.context),\
                "Activate record not present for parent"

            data = self.active_states[state.context]
            data.current_state = state

    def deactivate(self, state):
        if state in self.active_states:
            data = self.active_states[state]
            data.current_state = None
            data = None
            del self.active_states[state]

    def has_history_info(self, history_state):
        status = False

        if history_state in self.history_states:
            status = True

        return status

    def get_history_state(self, history_state):
        assert self.has_history_info(history_state),\
            "Record not found for history state"
        
        return self.history_states[history_state]

    def store_history_info(self, history_state, actual_state): 
        self.history_states[history_state] = actual_state

    def reset(self):
        self.active_states.clear()
        self.history_states.clear()
