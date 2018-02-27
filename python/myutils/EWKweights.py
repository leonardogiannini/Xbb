#!/usr/bin/env python
import ROOT
import numpy as np
import array

class EWKweights(object):

    def __init__(self, sample=None):
        self.lastEntry = -1
        self.branchBuffers = {}
        self.branches = []
        self.branches.append({'name': 'NLOw', 'formula': self.getNLOw})
        self.branches.append({'name': 'DYw', 'formula': self.getDYw})
        for wName in ['EWKw', 'EWKwSIG', 'EWKwVJets']:
            self.branchBuffers[wName] = np.zeros(3, dtype=np.float32)
            self.branches.append({'name': wName, 'formula': self.getVectorBranch, 'arguments': {'branch': wName, 'length':3}, 'length': 3})
        if sample:
            self.customInit(sample=sample)

    def customInit(self, initVars):
        sample = initVars['sample']
        self.applyEWK = ('DY' in sample.identifier and not '10to50' in sample.identifier) or ('WJet' in sample.identifier)
        self.applyNLO = self.applyEWK and ('amc' not in sample.identifier) 
        self.sys_sample = None
        if 'ZH_HToBB_ZToLL' in sample.identifier and not 'ggZH_HToBB_ZToLL' in sample.identifier:
            self.sys_sample = 'Zll'
        elif 'WminusH' in sample.identifier:
            self.sys_sample = 'Wlvm'
        elif 'WplusH' in sample.identifier:
            self.sys_sample = 'Wlvp'
        elif 'ZH_HToBB_ZToNuNu' in sample.identifier and not 'ggZH_HToBB_ZToNuNu' in sample.identifier:
            self.sys_sample = 'Zvv'

    def getBranches(self):
        return self.branches

    def getNLOw(self, tree):
        NLOw = 1.0
        if self.applyNLO:
            etabb = abs(tree.Jet_eta[tree.hJCidx[0]] - tree.Jet_eta[tree.hJCidx[1]])
            if etabb < 5:
                NLOw = 1.153*(0.940679 + 0.0306119*etabb -0.0134403*etabb*etabb + 0.0132179*etabb*etabb*etabb -0.00143832*etabb*etabb*etabb*etabb)
        return NLOw

    def getDYw(self, tree):
        self.processEvent(tree)
        DYw = self.getNLOw(tree) * self.branchBuffers['EWKw'][0]
        return DYw

    # read from buffers which have been filled in processEvent()    
    def getVectorBranch(self, event, arguments=None, destinationArray=None):
        self.processEvent(event)
        for i in range(arguments['length']):
            destinationArray[i] =  self.branchBuffers[arguments['branch']][i]

    # compute all the EWK weights
    def processEvent(self, tree):
        isGoodEvent = True
        currentEntry = tree.GetReadEntry()
        # if current entry has not been processed yet
        if currentEntry != self.lastEntry:
            self.lastEntry = currentEntry

            self.branchBuffers['EWKwVJets'][0] = 1.0
            self.branchBuffers['EWKwVJets'][1] = 1.0
            self.branchBuffers['EWKwVJets'][2] = 1.0
            if self.applyEWK and len(tree.GenVbosons_pt) > 0 and tree.GenVbosons_pt[0] > 100. and  tree.GenVbosons_pt[0] < 3000:
                self.branchBuffers['EWKwVJets'][0] = -0.1808051+6.04146*(pow((tree.GenVbosons_pt[0]+759.098),-0.242556))
                self.branchBuffers['EWKwVJets'][1] = self.branchBuffers['EWKwVJets'][0]
                self.branchBuffers['EWKwVJets'][2] = self.branchBuffers['EWKwVJets'][0]
            
            if tree.nGenVbosons > 0 and self.sys_sample:
                self.branchBuffers['EWKwSIG'][0] = self.signal_ewk(tree.GenVbosons_pt[0], self.sys_sample, 'nom')
                self.branchBuffers['EWKwSIG'][1] = self.signal_ewk(tree.GenVbosons_pt[0], self.sys_sample, 'down')
                self.branchBuffers['EWKwSIG'][2] = self.signal_ewk(tree.GenVbosons_pt[0], self.sys_sample, 'up')
            else:
                self.branchBuffers['EWKwSIG'][0] = 1.0
                self.branchBuffers['EWKwSIG'][1] = 1.0
                self.branchBuffers['EWKwSIG'][2] = 1.0

            self.branchBuffers['EWKw'][0] = self.branchBuffers['EWKwSIG'][0] * self.branchBuffers['EWKwVJets'][0]    
            self.branchBuffers['EWKw'][1] = self.branchBuffers['EWKwSIG'][1] * self.branchBuffers['EWKwVJets'][1]    
            self.branchBuffers['EWKw'][2] = self.branchBuffers['EWKwSIG'][2] * self.branchBuffers['EWKwVJets'][2]    
            #print isGoodEvent,  self.branchBuffers['EWKw'][0], self.branchBuffers['EWKw'][1], self.branchBuffers['EWKw'][2]
        return isGoodEvent

    def signal_ewk(self, GenVbosons_pt, sample, variation):
        SF = 1.
        EWK = None
        ###
        if sample == 'Zll':
            if variation == 'nom':
                EWK = [0.932072955817,0.924376254386,0.916552449249,0.909654343838,0.90479110736,0.902244634267,0.89957486928,0.902899199569,0.899314861082,0.89204902646,0.886663993587,0.878915415638,0.870241565009,0.863239359219,0.85727925851,0.849770804948,0.83762562793,0.829982098864,0.81108451152,0.821942287438,0.79,0.79,0.79,0.79,0.79]
            elif variation == 'up':
                EWK = [0.933479852292,0.925298220882,0.917622981133,0.91102286158,0.90718076681,0.905350232844,0.90336604675,0.903947932682,0.903377015003,0.897282669087,0.892978480734,0.885729935121,0.878913596976,0.872505666469,0.866859512888,0.860942354659,0.850346790893,0.844431351897,0.829520542725,0.837419206895,0.81,0.81,0.81,0.81,0.81]
            elif variation == 'down':
                EWK = [0.930666059342,0.923454287889,0.915481917365,0.908285826095,0.90240144791,0.89913903569,0.895783691809,0.895150466456,0.895252707162,0.886815383834,0.88034950644,0.872100896154,0.861569533042,0.853973051969,0.847699004132,0.838599255237,0.824904464966,0.815532845831,0.792648480316,0.806465367982,0.79,0.79,0.79,0.79,0.79]
        ###
        elif sample == 'Wlvp':
            if variation == 'nom':
                EWK = [0.953758,0.943779,0.932809,0.923219,0.913354,0.907033,0.899025,0.891828,0.885170,0.875928,0.870571,0.861312,0.863625,0.839608,0.840624,0.834239,0.823789,0.812814,0.811469,0.798847,0.792200,0.772159,0.773921,0.771432,0.774619]
            elif variation == 'up':
                EWK = [0.954816,0.944491,0.933642,0.924281,0.914858,0.908919,0.901691,0.894676,0.888427,0.883749,0.875082,0.866468,0.877642,0.854997,0.847831,0.842350,0.832661,0.822992,0.822964,0.814248,0.805361,0.785587,0.788509,0.786661,0.791773]
            elif variation == 'down':
                EWK = [0.952699,0.943066,0.931975,0.922156,0.911850,0.905147,0.896360,0.888981,0.881914,0.868107,0.866059,0.856157,0.849608,0.824219,0.833417,0.826127,0.814916,0.802635,0.799974,0.783446,0.779040,0.758730,0.759333,0.756202,0.757465]
        ###
        elif sample == 'Wlvm':
            if variation == 'nom':
                EWK = [0.956011,0.946317,0.934955,0.925556,0.915788,0.909425,0.901928,0.892972,0.888332,0.878922,0.869337,0.864740,0.857006,0.847624,0.841988,0.832349,0.828352,0.807816,0.806571,0.798520,0.787103,0.781220,0.778044,0.772675,0.763657]
            elif variation == 'up':
                EWK = [0.957037,0.947053,0.935765,0.926618,0.917058,0.911014,0.903976,0.895419,0.891694,0.882931,0.874269,0.870089,0.863073,0.853876,0.849331,0.840831,0.839799,0.818494,0.819101,0.812004,0.801327,0.795989,0.795559,0.791155,0.780640]
            elif variation == 'down':
                EWK = [0.954985,0.945581,0.934145,0.924494,0.914519,0.907837,0.899881,0.890524,0.884969,0.874912,0.864404,0.859391,0.850939,0.841371,0.834645,0.823868,0.816904,0.797137,0.794042,0.785037,0.772879,0.766451,0.760530,0.754196,0.746675]
        ###
        elif sample == 'Zvv':
            if variation == 'nom':
                EWK = [0.963285,0.960945,0.958126,0.956040,0.954829,0.955710,0.958934,0.960145,0.958798,0.954418,0.950510,0.943227,0.938764,0.929695,0.924761,0.915490,0.906100,0.901215,0.891759,0.882966,0.873852,0.868966,0.866067,0.854245,0.846545]
            elif variation == 'up':
                EWK = [0.963768,0.961256,0.958448,0.956418,0.955289,0.956276,0.959554,0.960861,0.959646,0.955487,0.951777,0.944787,0.940663,0.931997,0.927461,0.918733,0.909847,0.905479,0.896749,0.888549,0.880403,0.875968,0.873633,0.862580,0.855918]
            elif variation == 'down':
                EWK =  [0.962803,0.960634,0.957804,0.955663,0.954370,0.955145,0.958314,0.959429,0.957950,0.953349,0.949243,0.941668,0.936865,0.927393,0.922061,0.912248,0.902353,0.896952,0.886768,0.877383,0.867301,0.861963,0.858501,0.845911,0.837171]


        #print 'GenVbosons_pt is', GenVbosons_pt
        if EWK and GenVbosons_pt > 0. and GenVbosons_pt < 3000:
            #print 'oh yeah baby'
            if GenVbosons_pt > 0 and GenVbosons_pt <= 20:
                SF = EWK[0]
            if GenVbosons_pt > 20 and GenVbosons_pt <= 40:
                SF = EWK[1]
            if GenVbosons_pt > 40 and GenVbosons_pt <= 60:
                SF = EWK[2]
            if GenVbosons_pt > 60 and GenVbosons_pt <= 80:
                SF = EWK[3]
            if GenVbosons_pt > 80 and GenVbosons_pt <= 100:
                SF = EWK[4]
            if GenVbosons_pt > 100 and GenVbosons_pt <= 120:
                SF = EWK[5]
            if GenVbosons_pt > 120 and GenVbosons_pt <= 140:
                SF = EWK[6]
            if GenVbosons_pt > 140 and GenVbosons_pt <= 160:
                SF = EWK[7]
            if GenVbosons_pt > 160 and GenVbosons_pt <= 180:
                SF = EWK[8]
            if GenVbosons_pt > 180 and GenVbosons_pt <= 200:
                SF = EWK[9]
            if GenVbosons_pt > 200 and GenVbosons_pt <= 220:
                SF = EWK[10]
            if GenVbosons_pt > 220 and GenVbosons_pt <= 240:
                SF = EWK[11]
            if GenVbosons_pt > 240 and GenVbosons_pt <= 260:
                SF = EWK[12]
            if GenVbosons_pt > 260 and GenVbosons_pt <= 280:
                SF = EWK[13]
            if GenVbosons_pt > 280 and GenVbosons_pt <= 300:
                SF = EWK[14]
            if GenVbosons_pt > 300 and GenVbosons_pt <= 320:
                SF = EWK[15]
            if GenVbosons_pt > 320 and GenVbosons_pt <= 340:
                SF = EWK[16]
            if GenVbosons_pt > 340 and GenVbosons_pt <= 360:
                SF = EWK[17]
            if GenVbosons_pt > 360 and GenVbosons_pt <= 380:
                SF = EWK[18]
            if GenVbosons_pt > 380 and GenVbosons_pt <= 400:
                SF = EWK[19]
            if GenVbosons_pt > 400 and GenVbosons_pt <= 420:
                SF = EWK[20]
            if GenVbosons_pt > 420 and GenVbosons_pt <= 440:
                SF = EWK[21]
            if GenVbosons_pt > 440 and GenVbosons_pt <= 460:
                SF = EWK[22]
            if GenVbosons_pt > 460 and GenVbosons_pt <= 480:
                SF = EWK[23]
            if GenVbosons_pt > 480:
                SF = EWK[24]
            if GenVbosons_pt <= 0:
                SF = 1
        #print 'SF is', SF
        return SF
