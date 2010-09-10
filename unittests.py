#!/usr/bin/env python

__author__      = "Vishal Patil"
__copyright__   = "Copyright 2010 - 2011, Vishal Patil"
__license__     = "New-style BSD"

import re
import unittest

from states import State
from states import HierarchicalState
from states import ConcurrentState
from states import Transition
from states import Statechart
from pseudostates import StartState 
from pseudostates import EndState 
from pseudostates import HistoryState 
from action import Action
from transition import Event

class TestParam(object):

    def __init__(self):
        self.path = str() 

class TestTransitionAction(Action):

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def execute(self, parameter):
        transition = "%s:%s" % (self.start, self.end)
        parameter.path = ("%s %s" % (parameter.path, transition))
        parameter.path.strip()

class TestTransition(Transition):
    
    def __init__(self, start, start_name, end, end_name, event, guard):
        transition_action = TestTransitionAction(start_name, end_name)
        Transition.__init__(self, start, end, event, guard,
                                transition_action)

class TestClassAction(Action):

     def __init__(self, state_name):
        self.state_name = state_name

     def execute(self, parameter):
        action = "%s:%s" % (self.state_name, self.action_name)
        parameter.path = ("%s %s" % (parameter.path, action)).strip()
       
class TestEntryClassAction(TestClassAction):
    
    def __init__(self, state_name): 
        TestClassAction.__init__(self, state_name)
        self.action_name = "entry" 

class TestDoClassAction(TestClassAction):
    
    def __init__(self, state_name): 
        TestClassAction.__init__(self, state_name)
        self.action_name = "do" 

class TestExitClassAction(TestClassAction):
    
    def __init__(self, state_name): 
        TestClassAction.__init__(self, state_name)
        self.action_name = "exit" 

class Base(unittest.TestCase):

    def create_statechart(self, param):       
        raise NotImplementedError("Create statechart not implemented")

    def dispatch_events(self, events, expected_path):
        param   = TestParam()
        state_chart = self.create_statechart(param)
        state_chart.start()
        for event in events:
            state_chart.dispatch(Event(event))
        self.assertEquals(param.path, expected_path)    

class FSMTest(Base):

    def create_statechart(self, param):       

        state_chart = Statechart(param) 

        start = StartState(state_chart)
        A = State(state_chart, TestEntryClassAction("A"), 
                TestDoClassAction("A"), TestExitClassAction("A"))
        B = State(state_chart, TestEntryClassAction("B"), 
                TestDoClassAction("B"), TestExitClassAction("B"))
        C = State(state_chart, TestEntryClassAction("C"),
                TestDoClassAction("C"), TestExitClassAction("C"))
        end = EndState(state_chart)

        TestTransition(start, 'start', A, 'A', None, None) 
        TestTransition(A, 'A', B, 'B', Event(1), None) 
        TestTransition(B, 'B', B, 'B', Event(2), None)       
        TestTransition(B, 'B', end, 'end', Event(3), None)
        TestTransition(B, 'B', C, 'C', Event(4), None)
        TestTransition(C, 'C', C, 'C', Event(5), None)
        TestTransition(C, 'C', B, 'B', Event(6), None)
        TestTransition(C, 'C', A, 'A', Event(7), None)
        TestTransition(C, 'C', A, 'A', Event(8), None)
        return state_chart

    def testSimpleFSM1(self):
        events = [1, 2, 3]        
        expected_path = ("start:A A:entry A:do " + 
                         "A:exit A:B B:entry B:do " + 
                         "B:exit B:B B:entry B:do " + 
                         "B:exit B:end")
        self.dispatch_events(events, expected_path)

    def testSimpleFSM2(self):
        events = [1, 8, 4, 5, 2, 5, 6, 4, 7, 1, 2, 3]        
        expected_path = ("start:A A:entry A:do " +
                         "A:exit A:B B:entry B:do " +
                         "B:exit B:C C:entry C:do " +
                         "C:exit C:C C:entry C:do " +
                         "C:exit C:C C:entry C:do " +
                         "C:exit C:B B:entry B:do " +
                         "B:exit B:C C:entry C:do " +
                         "C:exit C:A A:entry A:do " +
                         "A:exit A:B B:entry B:do " +
                         "B:exit B:B B:entry B:do " +
                         "B:exit B:end")
        self.dispatch_events(events, expected_path)

class HSMTest(Base):

    def create_statechart(self, param):       
        state_chart = Statechart(param) 

        start = StartState(state_chart)
        A = HierarchicalState(state_chart, TestEntryClassAction("A"),
            TestDoClassAction("A"), TestExitClassAction("A"))
        end = EndState(state_chart)

        start_a = StartState(A)
        B = HierarchicalState(A, TestEntryClassAction("B"), 
            TestDoClassAction("B"), TestExitClassAction("B"))
        E = HierarchicalState(A, TestEntryClassAction("E"),
            TestDoClassAction("E"), TestExitClassAction("E"))

        start_b = StartState(B)
        history_b = HistoryState(B)
        C = State(B, TestEntryClassAction("C"), 
            TestDoClassAction("C"), TestExitClassAction("C"))
        D = State(B, TestEntryClassAction("D"), 
            TestDoClassAction("D"), TestExitClassAction("D"))

        start_e = StartState(E)
        history_e = HistoryState(E)
        F = State(E, TestEntryClassAction("F"), 
            TestDoClassAction("F"), TestExitClassAction("F"))
        G = State(E, TestEntryClassAction("G"), 
            TestDoClassAction("G"), TestExitClassAction("G"))

        TestTransition(start, 'start', A, 'A', None, None)
        TestTransition(start_a, 'start_a', B, 'B', None, None)
        TestTransition(start_b, 'start_b', history_b, 'history_b', 
                               None, None)
        TestTransition(history_b, 'history_b', C, 'C', None, None)
        TestTransition(start_e, 'start_e', history_e, 'history_e', None, None)
        TestTransition(history_e, 'history_e', F, 'F', None, None)
        TestTransition(C, 'C', D, 'D', Event(1), None)
        TestTransition(D, 'D', C, 'C', Event(2), None)
        TestTransition(C, 'C', E, 'E', Event(3), None)
        TestTransition(F, 'F', B, 'B', Event(4), None)
        TestTransition(F, 'F', G, 'G', Event(5), None)
        TestTransition(G, 'G', F, 'F', Event(6), None)
        TestTransition(D, 'D', G, 'G', Event(7), None)
        TestTransition(E, 'E', D, 'D', Event(8), None)
        TestTransition(D, 'D', end, 'end', Event(9), None)
        TestTransition(A, 'A', end, 'end', Event(10), None)

        return state_chart

    def testStart(self):
        events = []
        expected_path = "start:A A:entry A:do start_a:B B:entry B:do start_b:history_b history_b:C C:entry C:do"
        self.dispatch_events(events, expected_path)

    def testHistory(self):
         events = [1, 7, 6, 4, 7, 6, 4, 2, 3, 5]        
         expected_path = ("start:A A:entry A:do start_a:B B:entry B:do start_b:history_b history_b:C C:entry C:do " + 
                          "C:exit C:D D:entry D:do " +
                          "D:exit B:exit D:G E:entry E:do G:entry G:do " + 
                          "G:exit G:F F:entry F:do " +
                          "F:exit E:exit F:B B:entry B:do start_b:history_b D:entry D:do " +
                          "D:exit B:exit D:G E:entry E:do G:entry G:do " +
                          "G:exit G:F F:entry F:do " +
                          "F:exit E:exit F:B B:entry B:do start_b:history_b D:entry D:do " +
                          "D:exit D:C C:entry C:do " +
                          "C:exit B:exit C:E E:entry E:do " +
                          "start_e:history_e F:entry F:do F:exit F:G G:entry G:do")
         self.dispatch_events(events, expected_path)

    def testHSMExit(self):
        events = [1, 7, 8, 9]        
        expected_path = ("start:A A:entry A:do start_a:B B:entry B:do start_b:history_b history_b:C C:entry C:do " + 
                         "C:exit C:D D:entry D:do " + 
                         "D:exit B:exit D:G E:entry E:do G:entry G:do " + 
                         "G:exit E:exit E:D B:entry B:do D:entry D:do " +
                         "D:exit B:exit A:exit D:end")
        self.dispatch_events(events, expected_path)

    def testFinalState(self):
        events = [1, 7, 10]        
        expected_path = ("start:A A:entry A:do start_a:B B:entry B:do start_b:history_b history_b:C C:entry C:do " + 
                         "C:exit C:D D:entry D:do " + 
                         "D:exit B:exit D:G E:entry E:do G:entry G:do " +
                         "G:exit E:exit A:exit A:end")
        self.dispatch_events(events, expected_path)

class ConcurrentTest(Base):

    def create_statechart(self, param):       
        state_chart = Statechart(param) 

        start = StartState(state_chart)
        X = ConcurrentState(state_chart, TestEntryClassAction("X"), 
            TestDoClassAction("X"), TestExitClassAction("X"))
        TestTransition(start, 'start', X, 'X', None, None)

        A = HierarchicalState(X, TestEntryClassAction("A"), 
            TestDoClassAction("A"), TestExitClassAction("A"))
        start_a = StartState(A)
        history_a = HistoryState(A)
        D = State(A, TestEntryClassAction("D"), 
            TestDoClassAction("D"), TestExitClassAction("D"))
        E = State(A, TestEntryClassAction("E"), 
            TestDoClassAction("E"), TestExitClassAction("E"))

        TestTransition(start_a, 'start_a', history_a, 'history_a', None, None)
        TestTransition(history_a, 'history_a', D, 'D', None, None)
        TestTransition(D, 'D', E, 'E', Event(1), None)
        TestTransition(E, 'E', D, 'D', Event(2), None)

        B = HierarchicalState(X, TestEntryClassAction("B"), 
            TestDoClassAction("B"), TestExitClassAction("B"))
        start_b = StartState(B)
        history_b = HistoryState(B)
        F = State(B, TestEntryClassAction("F"), 
            TestDoClassAction("F"), TestExitClassAction("F"))
        G = State(B, TestEntryClassAction("G"), 
            TestDoClassAction("G"), TestExitClassAction("G"))
        H = State(B, TestEntryClassAction("H"), 
            TestDoClassAction("H"), TestExitClassAction("H"))

        TestTransition(start_b, 'start_b', history_b, 'history_b', None, None)
        TestTransition(history_b, 'history_b', F, 'F', None, None)
        TestTransition(F, 'F', H, 'H', Event(1), None)
        TestTransition(H, 'H', G, 'G', Event(6), None)
        TestTransition(G, 'G', F, 'F', Event(2), None)
        TestTransition(F, 'F', G, 'G', Event(8), None)

        C = HierarchicalState(state_chart, TestEntryClassAction("C"), 
            TestDoClassAction("C"), TestExitClassAction("C") )
        start_c = StartState(C)
        history_c = HistoryState(C)
        I = State(C, TestEntryClassAction("I"), 
            TestDoClassAction("I"), TestExitClassAction("I"))
        J = State(C, TestEntryClassAction("J"), 
            TestDoClassAction("J"), TestExitClassAction("J"))
        K = State(C, TestEntryClassAction("K"), 
            TestDoClassAction("K"), TestExitClassAction("K"))
        TestTransition(start_c, 'start_c', history_c, 'history_c', None, None)
        TestTransition(history_c, 'history_c', I, 'I', None, None)
        TestTransition(J, 'J', X, 'X', Event(13), None)
        TestTransition(I, 'I', J, 'J', Event(10), None)
        TestTransition(J, 'J', I, 'I', Event(9), None)
        TestTransition(J, 'J', K, 'K', Event(12), None)
        TestTransition(K, 'K', J, 'J', Event(11), None)

        TestTransition(E, 'E', K, 'K', Event(3), None)
        TestTransition(B, 'B', C, 'C', Event(5), None)
        TestTransition(G, 'G', C, 'C', Event(14), None)
        TestTransition(C, 'C', X, 'X', Event(15), None)

        return state_chart

    def testStartStates(self):
        events = []
        expected_path = "start:X X:entry X:do A:entry A:do start_a:history_a history_a:D D:entry D:do B:entry B:do start_b:history_b history_b:F F:entry F:do"
        self.dispatch_events(events, expected_path)

    def testConcurrentStates(self):
        events = [1, 2, 5, 10, 15, 6, 1, 2, 5]
        expected_path = ("start:X X:entry X:do A:entry A:do start_a:history_a history_a:D D:entry D:do B:entry B:do start_b:history_b history_b:F F:entry F:do " +
                        "D:exit D:E E:entry E:do F:exit F:H H:entry H:do " + 
                        "E:exit E:D D:entry D:do " +
                        "H:exit B:exit D:exit A:exit X:exit B:C C:entry C:do start_c:history_c history_c:I I:entry I:do " +
                        "I:exit I:J J:entry J:do " +
                        "J:exit C:exit C:X X:entry X:do A:entry A:do start_a:history_a D:entry D:do B:entry B:do start_b:history_b H:entry H:do " +
                        "H:exit H:G G:entry G:do " +
                        "D:exit D:E E:entry E:do " +
                        "E:exit E:D D:entry D:do G:exit G:F F:entry F:do " +
                        "F:exit B:exit D:exit A:exit X:exit B:C C:entry C:do start_c:history_c J:entry J:do")
        self.dispatch_events(events, expected_path)

if __name__ == "__main__":
    unittest.main()    
