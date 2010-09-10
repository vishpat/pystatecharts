#!/usr/bin/env python

__author__      = "Vishal Patil"
__copyright__   = "Copyright 2010 - 2011, Vishal Patil"
__license__     = "New-style BSD"

from runtime import RuntimeData

class State(object):

    def __init__(self, context, entry, do, exit):

        """ Context can be null only for the statechart """
        if (context == None and (not isinstance(self, Statechart))):
            assert False, "context cannot be null"	

        self.context = context
        parent = context	

        """ Recursively move up to get the statechart object """
        if parent != None:
            while 1:
                if isinstance(parent, Statechart):
                    break

                if parent == None:
                    break

                parent = parent.context
            
            if isinstance(parent, Statechart):
                self.statechart = parent 
            else:
                assert False, "Statechart not found check hierarchy"

        self.entry = entry 
        self.do    = do 
        self.exit  = exit 
        self.transitions = []

    def add_transition(self, transition):
        if transition == None:
            assert False, "Cannot add null transition"

        if (transition.guard):
            self.transitions.insert(0, transition)
        else:
            self.transitions.append(transition)

    def activate(self, runtime, param):
        activated = False

        if not runtime.is_active(self):
            runtime.activate(self)

            if self.entry:
                self.entry.execute(param)
            
            if self.do:
                self.do.execute(param)

            activated = True
            
        return activated


    def deactivate(self, runtime, param):
        if runtime.is_active(self):

            if self.exit:
                self.exit.execute(param)

            runtime.deactivate(self)

    def dispatch(self, runtime, event, param):
        status = False

        for transition in self.transitions:	
            if transition.execute(runtime, event, param):
                status = True
                break

        return status 

class Context(State):

    def __init__(self, parent, entry, do, exit):
        State.__init__(self, parent, entry, do, exit)
        self.start_state = None 

class Transition(object):

    def __init__(self, start, end, event, guard, action):
        self.start = start
        self.end = end
        self.event = event 
        self.guard = guard
        self.action = action

        """ Used to store the states that will get activated """
        self.activate = list() 

        """ Used to store the states that will get de-activated """
        self.deactivate = list() 

        self.calculate_changed_states(start, end)

        start.add_transition(self)

    def calculate_changed_states(self, start, end):
        start_states = list()
        end_states = list()

        """ Recursively get all the context start states """
        s = start
        while s != None:
            start_states.insert(0, s)
            context = s.context
            if context and not isinstance(context, Statechart):
                s = context
            else:
                s = None

        """ Recursively get all the context end states """
        e = end
        while e != None:
            end_states.insert(0, e)
            context = e.context
            if context and not isinstance(context, Statechart):
                e = context
            else:
                e = None

        """ Get the Least Common Ancestor (LCA) of the start and end states """
        min_state_count = min(len(start_states), len(end_states))
        lca = min_state_count - 1

        if (start != end):
            lca = 0
            while lca < min_state_count:
                if (start_states[lca] != end_states[lca]):
                    break
                lca += 1

        """ Starting from the LCA get the states that will be deactivated """
        i = lca 
        while  i < len(start_states):
            self.deactivate.insert(0, start_states[i])
            i += 1

        """ Starting from the LCA get the states that will be activated """
        i = lca 
        while  i < len(end_states):
            self.activate.append(end_states[i])
            i += 1

    def execute(self, runtime, event, param):
        if (self.event and (event == None)):
            return False

        if (self.event and (self.event != event)):
            return False

        if (self.guard and (not self.guard.check(runtime, param))):
            return False

        runtime.event = event
        runtime.transition = self 

        for state in self.deactivate:
            state.deactivate(runtime, param)

        if self.action:
            self.action.execute(param)	

        for state in self.activate:
            state.activate(runtime, param)

        runtime.transition = None 
        runtime.event = None

        return True	

class HierarchicalState(Context):

    def __init__(self, parent, entry, do, exit):

        Context.__init__(self, parent, entry, do, exit)
        self.history = None

        if isinstance(parent, ConcurrentState):
           parent.add_region(self) 

    def activate(self, runtime, param):
        Context.activate(self, runtime, param)

        if (runtime.transition and 
            runtime.transition.end == self):
            self.start_state.activate(runtime, param) 

    def deactivate(self, runtime, param):

        assert (self in runtime.active_states), self
                        
        rdata = runtime.active_states[self]
        if self.history:
            runtime.store_history_info(self.history, rdata.current_state)

        if runtime.is_active(rdata.current_state):
            rdata.current_state.deactivate(runtime, param)

        Context.deactivate(self, runtime, param)

    def dispatch(self, runtime, event, param):
        
        if not runtime.active_states[self]:
            assert False, (("HierarchicalState: " +
                        "trying to dispatch on inactive state"))

        """ See if the current child state can handle the event """
        rdata = runtime.active_states[self]
        if rdata.current_state == None and self.start_state:
            runtime.activate(self.start_state) 
            rdata.current_state.activate(runtime, param)

        if (rdata.current_state and 
            rdata.current_state.dispatch(runtime, event, param)):
            return True
       
        """ 
            Since none of the child states can handle the event, let this 
            state try handling the event.
        """
        for transition in self.transitions: 
            if transition.execute(runtime, event, param):
                return True

        return False                

class ConcurrentState(Context):

    def __init__(self, context, entry, do, exit):
        Context.__init__(self, context, entry, do, exit)
        self.regions = []

    def add_region(self, region):
        self.regions.append(region)

    def activate(self, runtime, param):
        status = False

        if Context.activate(self, runtime, param):
            rdata = runtime.active_states[self]

            for region in self.regions:
                if not (region in rdata.state_set):
                    region.activate(runtime, param)
                    region.start_state.activate(runtime, param)
                    
        return status            

    def deactivate(self, runtime, param):
        for region in self.regions:
            if runtime.is_active(region):
                region.deactivate(runtime, param)

        Context.deactivate(self, runtime, param)

    def dispatch(self, runtime, event, param):

        if not runtime.active_states[self]:
            assert False, "Dispatching an event on inactive state"

        dispatched = False

        """ Check if any of the child regions can handle the event """
        for region in self.regions:
            if region.dispatch(runtime, event, param):
                dispatched = True

        if dispatched:
            return True

        """ Check if this state can handle the event by itself """
        for transition in self.transitions:
            if transition.execute(runtime, event, param):
               dispatched = True
               break

        return dispatched

class Statechart(Context):

    def __init__(self, param):
        Context.__init__(self, None, None, None, None) 
        self.param = param

    def start(self):
        self.runtime = RuntimeData()
        self.runtime.reset()
        self.runtime.activate(self)
        self.runtime.activate(self.start_state)
        self.dispatch(None)

    def dispatch(self, event):
        current_state = self.runtime.active_states[self].current_state
        return current_state.dispatch(self.runtime, event, self.param)	

    def add_transition(self, transition):
        assert False, "Cannot add transition to a statechart"
    
    def shutdown(self):
        pass

