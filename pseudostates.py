#!/usr/bin/env python

__author__      = "Vishal Patil"
__copyright__   = "Copyright 2010 - 2011, Vishal Patil"
__license__     = "New-style BSD"

from states import State
from states import Statechart
from states import HierarchicalState

class PseudoState(State):
    def __init__(self, context):
        State.__init__(self, context, None, None, None)

    def activate(self, runtime, param):
        runtime.activate(self)

        if self.entry:
            self.entry.execute(runtime, param)

        return True

    def dispatch(self, runtime, event, param):
        return State.dispatch(self, runtime, event, param)

class StartState(PseudoState):
    def __init__(self, context):
        PseudoState.__init__(self, context)

        if self.context.start_state:
            assert False, "Start state already present"
        else:
            self.context.start_state = self

    def activate(self, runtime, param):
        self.dispatch(runtime, None, param)

class EndState(PseudoState):
    def __init__(self, context):
        PseudoState.__init__(self, context)
        assert isinstance(self.context, Statechart),\
                "Currently the end state is allowed in only in Statechart" 

	def add_transition(self, transition):
		assert False, "Cannot add transition to the end state"

	def dispatch(self, runtime, event, param):
		assert False, "Cannot dispatch an event to the end state"
		
class HistoryState(PseudoState):

    def __init__(self, context):
        PseudoState.__init__(self, context)
        self.state = None

        if isinstance(self.context, HierarchicalState): 
            if self.context.history:
                assert False, "history state already present" 
            else:
                self.context.history = self
        else:
            assert False, "Parent not a Hierarchical state"

    def activate(self, runtime, param):
        assert len(self.transitions) == 1,\
            "History state cannot have more than 1 transition"
        
        assert ((len(self.transitions[0].deactivate) == 1) and
           (self.transitions[0].deactivate[0] == self)) 

        if runtime.has_history_info(self):
            state = runtime.get_history_state(self)
            state.activate(runtime, param)
        else:
            self.dispatch(runtime, None, param)

