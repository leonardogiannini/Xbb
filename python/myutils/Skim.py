#!/usr/bin/env python
from __future__ import print_function
import os
import ROOT

# ------------------------------------------------------------------------------
# this class can be used to apply and additional cut during sys step
# ------------------------------------------------------------------------------
class Skim(object):

    def __init__(self, cut):
        self.cut = cut
        self.cutFormula = None
        self.debug = 'XBBDEBUG' in os.environ

    # return True => keep event, return False => discard event
    def processEvent(self, tree):

        # initialize formula on the first event
        if self.cutFormula is None:
            self.tree = tree
            self.cutFormula = ROOT.TTreeFormula("sysnew_skim_cut", self.cut, self.tree)
            if self.debug:
                print("DEBUG: initialized TTreeFormula for addtional cut during sys: {cut}".format(cut=self.cut))

        # apply cut
        if self.cutFormula.GetNdata():
            return True if self.cutFormula.EvalInstance() else False
        else:
            return False

