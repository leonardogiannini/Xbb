#!/usr/bin/env python
import ROOT
import math

class TTWeights(object):

    def __init__(self, nano=False):
        self.nano = nano
        self.branches = []

    def customInit(self, initVars):
        self.sample = initVars['sample']
        self.sampleTree = initVars['sampleTree']
        if self.sample.isMC():
            if self.nano:
                self.sampleTree.addFormula("nTop", "Sum$(GenPart_pdgId==6)")
                self.sampleTree.addFormula("top0_pt","MinIf$(GenPart_pt,GenPart_pdgId==6)")
                self.sampleTree.addFormula("top1_pt","MaxIf$(GenPart_pt,GenPart_pdgId==6)")
            else:
                self.sampleTree.addFormula("nTop", "nGenTop")
                self.sampleTree.addFormula("top0_pt","GenTop_pt[0]")
                self.sampleTree.addFormula("top1_pt","GenTop_pt[1]")
            self.branches.append({'name': 'TTW', 'formula': self.getTTW})

    def getBranches(self):
        return self.branches

    def getTTW(self, tree):
        TTW = 1

        if self.sampleTree.evaluate("nTop") == 2:
            sf_top1 = math.exp(0.0615 - 0.0005*self.sampleTree.evaluate("top0_pt"))
            sf_top2 = math.exp(0.0615 - 0.0005*self.sampleTree.evaluate("top1_pt"))

            TTW = math.sqrt(sf_top1*sf_top2)

        return TTW

