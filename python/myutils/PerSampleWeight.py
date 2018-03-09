#!/usr/bin/env python
from __future__ import print_function
import os

# ------------------------------------------------------------------------------
# this class can be used to set a branch to a fixed value for certain samples
# ------------------------------------------------------------------------------
class PerSampleWeight(object):

    def __init__(self, branchName, sample=None, affectedSampleNames=None, weightAffected=1.0, weightUnaffected=0.0):
        self.branchName = branchName
        self.affectedSampleNames = affectedSampleNames
        self.sample = sample
        self.weightAffected = weightAffected
        self.weightUnaffected = weightUnaffected

    def customInit(self, initVars):
        self.sample = initVars['sample']
        self.weight = weightAffected if self.sample.name in self.affectedSampleNames else self.weightUnaffected
        self.branches = [{'name': self.branchName, 'formula': self.getTheWeight}]
        self.debug = 'XBBDEBUG' in os.environ
        if self.debug:
            print("DEBUG: sample {sampleName} will get the weight {branchName}={weight}".format(sampleName=self.sample.name, weight=self.weight, branchName=self.branchName))

    def getBranches(self):
        return self.branches

    def getTheWeight(self, tree):
        return self.weight

