#!/usr/bin/env python
import ROOT
import numpy as np
import array
import os
import math

class WPtReweight(object):

    def __init__(self):
        self.lastEntry = -1
        self.branchBuffers = {}
        self.branches = []
        branchName = 'FitCorr' 
        self.branchBuffers[branchName] = array.array('f', [1.0, 0.0, 0.0])
        self.branches.append({'name': branchName, 'formula': self.getVectorBranch, 'arguments': {'branch': branchName, 'length':3}, 'length': 3})

    def customInit(self, initVars):
        self.sample = initVars['sample']
        self.channel = initVars['channel']
        self.tree = initVars['tree']
        self.formWHF = ROOT.TTreeFormula('WHF','Sum$(GenJet_pt>20 && abs(GenJet_eta)<2.4 && GenJet_numBHadrons>=2)', self.tree)

    def getBranches(self):
        return self.branches

    # read from buffers which have been filled in processEvent()    
    def getVectorBranch(self, event, arguments=None, destinationArray=None):
        self.processEvent(event)
        for i in range(arguments['length']):
            destinationArray[i] =  self.branchBuffers[arguments['branch']][i]

    def getCorrFactor(self, V_pt, sample):
        CorrFactor = [1, 1, 1]
        if sample == 'TT':
            return [1.064 - 0.000380*V_pt, 1.064 - 0.000469*V_pt, 1.064 - 0.000291*V_pt]
        elif sample == 'WLF':
            return [1.097 - 0.000575*V_pt, 1.097 - 0.000621*V_pt, 1.097 - 0.000529*V_pt]
        elif sample == 'WHF' or sample == 'ST':
            return [1.259 - 0.00167*V_pt, 1.259 - 0.00180*V_pt, 1.259 - 0.00154*V_pt]
        else:
            return CorrFactor

    # compute all the weights
    def processEvent(self, tree):
        isGoodEvent = True
        currentEntry = tree.GetReadEntry()
        # if current entry has not been processed yet
        if currentEntry != self.lastEntry:
            self.lastEntry = currentEntry
            jobFullName = str(self.sample.FullName)
            #Corrections only used in Wlv
            if self.formWHF.GetNdata() == 1:
                isWHF = self.formWHF.EvalInstance()
            else:
                isWHF = False

            ##
            #Add TT,WHF and WLF corrections from data fit
            ##
            corr_sample = None
            if self.channel == 'Wlv':
                if 'TT' in jobFullName:
                    corr_sample = 'TT'
                elif ('WJets' in jobFullName):
                    if isWHF:
                        corr_sample = 'WHF'
                    else:
                        corr_sample = 'WLF'
                elif 'ST' in jobFullName:
                    corr_sample = 'ST'

            if corr_sample:
                FitCorr_ = self.getCorrFactor(tree.V_new_pt, corr_sample)
                self.branchBuffers['FitCorr'][0] = FitCorr_[0]
                self.branchBuffers['FitCorr'][1] = FitCorr_[1]
                self.branchBuffers['FitCorr'][2] = FitCorr_[2]
        return isGoodEvent
