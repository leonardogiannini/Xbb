#!/usr/bin/env python
import ROOT
import numpy as np
import array
import sys

class VtypeCorrector(object):

    def __init__(self, tree=None, channel='all'):
        self.channel = channel
        self.lastEntry = -1
        self.n_vtype_unchanged = 0
        self.n_vtype_changed = 0
        self.n_vtype_events_skipped = 0
        self.branchBuffers = {}
        self.branches = []
        ### new branches for Vtype correction ###
        self.branchBuffers['Vtype_new'] = array.array('f', [0])
        self.branches.append({'name': 'Vtype_new', 'formula': self.getBranch, 'arguments': 'Vtype_new'})

        self.vLeptonsvar = ['pt', 'eta', 'phi', 'mass', 'relIso03', 'relIso04']
        for var in self.vLeptonsvar:
            branchName = 'vLeptons_new_%s'%var
            self.branchBuffers[branchName] = np.zeros(21, dtype=np.float32)
            self.branches.append({'name': branchName, 'formula': self.getVectorBranch, 'arguments': {'branch': branchName, 'length':2}, 'length': 2})

        ##define Vleptons branch
        self.Vvar = ['pt', 'eta', 'phi', 'mass']
        self.LorentzDic = {'pt':'Pt', 'eta':'Eta', 'phi':'Phi', 'mass':'M'}
        for var in self.Vvar:
            branchName = 'V_new_%s'%var
            self.branchBuffers[branchName] = np.zeros(21, dtype=np.float32)
            self.branches.append({'name': branchName, 'formula': self.getBranch, 'arguments': branchName})

        if tree:
            self.setTree(tree)

    def customInit(self, initVars):
        tree = initVars['tree']
        #include the Vytpe reco here
        self.zEleSelection = lambda x : tree.selLeptons_pt[x] > 15 and tree.selLeptons_eleMVAIdSppring16GenPurp[x] >= 1
        self.zMuSelection = lambda x : tree.selLeptons_pt[x] > 15 and  tree.selLeptons_looseIdPOG[x] and tree.selLeptons_relIso04[x] < 0.25    

    # recompute Vtype, return false to skip the event if Vtype does not match channel
    def processEvent(self, event):
        isGoodEvent = True
        currentEntry = event.GetReadEntry()
        if currentEntry != self.lastEntry:
            # do processing

            #Variable to store Vtype and leptons info
            Vtype_new_ = -1
            self.branchBuffers['V_new_mass'][0] = -1

            vLeptons_new = []
            #get all the lepton index
            lep_index = range(len(event.selLeptons_pt))
            selectedElectrons = [i for i in  lep_index if abs(event.selLeptons_pdgId[i]) == 11]
            selectedMuons = [i for i in lep_index if abs(event.selLeptons_pdgId[i]) == 13]

            zElectrons = [x for x in selectedElectrons if self.zEleSelection(x)]
            zMuons = [x for x in selectedMuons if self.zMuSelection(x)]

            zMuons.sort(key=lambda x:event.selLeptons_pt[x], reverse=True)
            zElectrons.sort(key=lambda x:event.selLeptons_pt[x], reverse=True)
            
            tree=event
            #Zll case. Recompute lepton branches
            if len(zMuons) >=  2 :
                if tree.selLeptons_pt[zMuons[0]] > 20:
                    for i in zMuons[1:]:
                        if  tree.selLeptons_charge[zMuons[0]]*tree.selLeptons_charge[i] < 0:
                            Vtype_new_ = 0
                            for var in self.vLeptonsvar:
                                self.branchBuffers['vLeptons_new_'+var][0] = getattr(tree,'selLeptons_%s'%var)[0]
                                self.branchBuffers['vLeptons_new_'+var][1] = getattr(tree,'selLeptons_%s'%var)[i]
                            break
            elif len(zElectrons) >=  2 :
                if tree.selLeptons_pt[zElectrons[0]] > 20:
                    for i in zElectrons[1:]:
                        if  tree.selLeptons_charge[zElectrons[0]]*tree.selLeptons_charge[i] < 0:
                            Vtype_new_ = 1
                            for var in self.vLeptonsvar:
                                self.branchBuffers['vLeptons_new_'+var][0] = getattr(tree,'selLeptons_%s'%var)[0]
                                self.branchBuffers['vLeptons_new_'+var][1] = getattr(tree,'selLeptons_%s'%var)[i]
                            break
            else:
                if tree.Vtype == 0 or tree.Vtype == 1:
                    print '@ERROR: This is impossible, the new ele cut should be losser...'
                    print 'selected mu/e:',selectedMuons, selectedElectrons, ' z mu:', zMuons, ' z e:', zElectrons
                    sys.exit(1)
                #Wlv case. Recompute lepton branches
                if tree.Vtype == 2 or tree.Vtype == 3:
                    Vtype_new_ = tree.Vtype
                    for var in self.vLeptonsvar:
                        self.branchBuffers['vLeptons_new_'+var][0] = getattr(tree,'vLeptons_%s'%var)[0]
                #to handle misassigned Vtype 4 or -1 because of additional electron cut
                elif (tree.Vtype == 4 or tree.Vtype == -1) and len(zElectrons) + len(zMuons) > 0:
                    Vtype_new_ = 5
                #to handle misassigned Vtype 5 because of additional electron cut
                elif tree.Vtype == 5 and len(zElectrons) + len(zMuons) == 0:
                    if tree.met_pt < 80:
                        Vtype_new_ = -1
                    else:
                        Vtype_new_ = 4
                #if none of the exception above happen, it is save to copy the Vtype
                else:
                    Vtype_new_ = tree.Vtype

            # skip event, if vtype_new doesn't correspond to channel
            if self.channel.lower() == 'zll': 
                if Vtype_new_ != 0 and Vtype_new_ != 1:
                    self.n_vtype_events_skipped += 1
                    isGoodEvent = False
            elif self.channel.lower() == 'wlv':
                if Vtype_new_ != 2 and Vtype_new_ != 3:
                    self.n_vtype_events_skipped += 1
                    isGoodEvent = False
            elif self.channel.lower() == 'zvv':
                if (Vtype_new_ != 2 and Vtype_new_ != 3 and Vtype_new_ != 4) or tree.V_pt < 170:
                    self.n_vtype_events_skipped += 1
                    isGoodEvent = False

            if isGoodEvent:
                if Vtype_new_ == tree.Vtype:
                    self.n_vtype_unchanged += 1
                else:
                    self.n_vtype_changed += 1

            V = ROOT.TLorentzVector()

            #Recompute combined lepton variables for Zll
            if Vtype_new_ == 0 or Vtype_new_ == 1:
                lep1 = ROOT.TLorentzVector()
                lep2 = ROOT.TLorentzVector()
                lep1.SetPtEtaPhiM(self.branchBuffers['vLeptons_new_pt'][0], self.branchBuffers['vLeptons_new_eta'][0], self.branchBuffers['vLeptons_new_phi'][0], self.branchBuffers['vLeptons_new_mass'][0])
                lep2.SetPtEtaPhiM(self.branchBuffers['vLeptons_new_pt'][1], self.branchBuffers['vLeptons_new_eta'][1], self.branchBuffers['vLeptons_new_phi'][1], self.branchBuffers['vLeptons_new_mass'][1])
                V = lep1+lep2
                for var in self.Vvar:
                    self.branchBuffers['V_new_'+var][0] = getattr(V, self.LorentzDic[var])()
            #Use "old" lepton variables for Wlv and Zvv. i.e. only Vtype -> Vtype_new change, other _new variables are copy
            else:
                for var in self.Vvar:
                    self.branchBuffers['V_new_'+var][0] = getattr(tree,'V_%s'%var)

            self.branchBuffers['Vtype_new'][0] = Vtype_new_

            # mark current entry as processed
            self.lastEntry = currentEntry
        return isGoodEvent

    def getBranch(self, event, arguments=None):
        self.processEvent(event)
        if arguments:
            return self.branchBuffers[arguments][0]

    def getVectorBranch(self, event, arguments=None, destinationArray=None):
        self.processEvent(event)
        # TODO: avoid this additional copy step
        for i in range(arguments['length']):
            destinationArray[i] =  self.branchBuffers[arguments['branch']][i]
    
    def getBranches(self):
        return self.branches

    def printStatistics(self):
        print 'Vtype correction statistics:' 
        print ' #skipped:', self.n_vtype_events_skipped
        print ' #unchanged:', self.n_vtype_unchanged
        print ' #changed:', self.n_vtype_changed
