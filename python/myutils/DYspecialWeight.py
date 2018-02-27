#!/usr/bin/env python
import ROOT

# DY stitching weight
#  defined as 'specialweight' in samples_nosplit.ini
class DYspecialWeight(object):

    def __init__(self):
        self.branches = [{'name': 'DY_specialWeight', 'formula': self.getDYspecialWeight}]

    def customInit(self, initVars):
        self.sample = initVars['sample']
        self.specialWeightFormula =  ROOT.TTreeFormula('specialWeight', self.sample.specialweight, initVars['tree'])

    def getBranches(self):
        return self.branches

    def getDYspecialWeight(self, tree=None):
        specialWeight = 1.0
        if self.sample.specialweight:
            specialWeight = self.specialWeightFormula.EvalInstance()
        return specialWeight

