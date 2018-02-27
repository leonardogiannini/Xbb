#!/usr/bin/env python
import ROOT
import numpy as np
import array
import sys

class ApplySkim(object):

    def __init__(self, tree, skim = '1'):
        #self.skim = skim
        self.lastEntry = -1
        self.n_vtype_events_skipped = 0
        self.branchBuffers = {}
        self.branches = []

        #Define fromula
        self.SkimFormula = ROOT.TTreeFormula("SkimFormula", skim, tree)

    # evaluate skim, return false to skip the event if event does not pass the skim cut
    def processEvent(self, event):
        isGoodEvent = True
        currentEntry = event.GetReadEntry()
        if currentEntry != self.lastEntry:
            #Evaluate formula
            isGoodEvent = self.SkimFormula.EvalInstance()
            self.lastEntry = currentEntry
        return isGoodEvent
