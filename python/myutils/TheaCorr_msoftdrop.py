#!/usr/bin/env python
import ROOT
import math
import numpy as np

#code from https://github.com/asady1/HVH2016/blob/master/miniTreeProducer.py (boosted HH resonant)
def getPUPPIweight( puppipt, puppieta, puppisd_corrGEN=0, puppisd_corrRECO_cen=0, puppisd_corrRECO_for=0 ):
    genCorr  = 1.
    recoCorr = 1.
    totalWeight = 1.

    corrGEN = ROOT.TF1("corrGEN","[0]+[1]*pow(x*[2],-[3])",200,3500)
    corrGEN.SetParameter(0,1.00626)
    corrGEN.SetParameter(1, -1.06161)
    corrGEN.SetParameter(2,0.0799900)
    corrGEN.SetParameter(3,1.20454)
 
    corrRECO_cen = ROOT.TF1("corrRECO_cen","[0]+[1]*x+[2]*pow(x,2)+[3]*pow(x,3)+[4]*pow(x,4)+[5]*pow(x,5)",200,3500)
    corrRECO_cen.SetParameter(0,1.09302)
    corrRECO_cen.SetParameter(1,-0.000150068)
    corrRECO_cen.SetParameter(2,3.44866e-07)
    corrRECO_cen.SetParameter(3,-2.68100e-10)
    corrRECO_cen.SetParameter(4,8.67440e-14)
    corrRECO_cen.SetParameter(5,-1.00114e-17)
 
    corrRECO_for = ROOT.TF1("corrRECO_for","[0]+[1]*x+[2]*pow(x,2)+[3]*pow(x,3)+[4]*pow(x,4)+[5]*pow(x,5)",200,3500)
    corrRECO_for.SetParameter(0,1.27212)
    corrRECO_for.SetParameter(1,-0.000571640)
    corrRECO_for.SetParameter(2,8.37289e-07)
    corrRECO_for.SetParameter(3,-5.20433e-10)
    corrRECO_for.SetParameter(4,1.45375e-13)
    corrRECO_for.SetParameter(5,-1.50389e-17)
    genCorr =  corrGEN.Eval( puppipt )
    if( abs(puppieta)  < 1.3 ):
            recoCorr = corrRECO_cen.Eval( puppipt )
    else:
            recoCorr = corrRECO_for.Eval( puppipt );
#    print(genCorr,recoCorr)
    totalWeight = genCorr*recoCorr
    return totalWeight 


class TheaCorr_msoftdrop(object):

    def __init__(self):
        
        self.branchBuffers = {}
        self.branches = []
        
        bname="FatjetAK08ungroomed_puppi_TheaCorr"
        
        self.branchBuffers[bname] = np.ones(3, dtype=np.float32) #first 3 in pt, usually n.1 is used
        self.branches.append({'name': bname, 'formula': self.getVectorBranch, 'arguments': {'branch': bname, 'length':3}, 'length': 3})
        
        # read from buffers which have been filled in processEvent()    
    def getVectorBranch(self, event, arguments=None, destinationArray=None):
        self.processEvent(event)
        for i in range(arguments['length']):
            destinationArray[i] =  self.branchBuffers[arguments['branch']][i]

    def getBranches(self):
        return self.branches

    def processEvent(self, tree):
        
        #self.branchBuffers['FatjetAK08ungroomed_puppi_TheaCorr'][0] = 1.0
        #self.branchBuffers['FatjetAK08ungroomed_puppi_TheaCorr'][1] = 1.0
        #self.branchBuffers['FatjetAK08ungroomed_puppi_TheaCorr'][2] = 1.0
        
        for i in range(tree.nFatjetAK08ungroomed):
            if i>2: break
            self.branchBuffers['FatjetAK08ungroomed_puppi_TheaCorr'][i] = getPUPPIweight(tree.FatjetAK08ungroomed_puppi_pt[i],tree.FatjetAK08ungroomed_puppi_eta[i])


        return 






