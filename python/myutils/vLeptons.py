#!/usr/bin/env python

# well there is no 'vLeptons' in post-processed NanoAOD anymore, so recompute what has been thrown away...

class lepton(object):
    def __init__(self, pt, eta, phi, mass, charge):
        self.pt = pt
        self.eta = eta
        self.phi = phi
        self.mass = mass
        self.charge = charge

class vLeptonSelector(object):

    def __init__(self, tree):
        zMuons = []
        zElectrons = []
        wElectrons = []
        wMuons = []
        for i in range(tree.nMuon):
            if tree.Muon_pt[i]>20 and tree.Muon_pfRelIso04_all[i]<0.25 and tree.Muon_dxy[i]<0.05 and tree.Muon_dz[i]<0.2:
                zMuons.append(lepton(pt=tree.Muon_pt[i], eta=tree.Muon_eta[i], phi=tree.Muon_phi[i], mass=tree.Muon_mass[i], charge=tree.Muon_charge[i]))
        for i in range(tree.nElectron):
            if tree.Electron_pt[i]>20 and tree.Electron_mvaSpring16GP_WP90[i] and tree.Electron_pfRelIso03_all[i]<0.15:
                zElectrons.append(lepton(pt=tree.Electron_pt[i], eta=tree.Electron_eta[i], phi=tree.Electron_phi[i], mass=tree.Electron_mass[i], charge=tree.Electron_charge[i]))
        for i in range(tree.nMuon):
            if tree.Muon_pt[i]>25 and tree.Muon_tightId[i] >= 1 and tree.Muon_pfRelIso04_all[i]<0.15 and tree.Muon_dxy[i]<0.05 and tree.Muon_dz[i]<0.2:
                wMuons.append(lepton(pt=tree.Muon_pt[i], eta=tree.Muon_eta[i], phi=tree.Muon_phi[i], mass=tree.Muon_mass[i], charge=tree.Muon_charge[i]))
        for i in range(tree.nElectron):
            if tree.Electron_pt[i]>25 and tree.Electron_mvaSpring16GP_WP90[i] and tree.Electron_pfRelIso03_all[i]<0.12:
                wElectrons.append(lepton(pt=tree.Electron_pt[i], eta=tree.Electron_eta[i], phi=tree.Electron_phi[i], mass=tree.Electron_mass[i], charge=tree.Electron_charge[i]))

        vLeptons = [] 
        Vtype = 0 
        if len(zMuons) >= 2:
            if zMuons[0].pt > 20:
                for i in xrange(1,len(zMuons)):
                    if zMuons[0].charge * zMuons[i].charge < 0:
                        Vtype = 0
                        vLeptons = [zMuons[0],zMuons[i]]
                        break
        elif len(zElectrons) >= 2:
            if zElectrons[0].pt > 20:
                for i in xrange(1,len(zElectrons)):
                    if zElectrons[0].charge * zElectrons[i].charge < 0:
                        Vtype = 1
                        vLeptons = [zElectrons[0],zElectrons[i]]
                        break
        elif len(wElectrons) + len(wMuons) == 1:
            if len(wMuons) == 1:
                Vtype = 2
                vLeptons = [wMuons[0]]
            if len(wElectrons) == 1:
                Vtype = 3
                vLeptons = [wElectrons[0]]
        elif len(zElectrons) + len(zMuons) > 0:
            Vtype = 5
        else:
            Vtype = 4
            if tree.MET_pt < 150:
                Vtype = -1
        self.Vtype = Vtype
        self.vLeptons = vLeptons
        self.zMuons = zMuons
        self.zElectrons = zElectrons

    def getVleptons(self):
        return self.vLeptons
    
    def getVtype(self):
        return self.Vtype
    
    def getZelectrons(self):
        return self.zElectrons

    def getZmuons(self):
        return self.zMuons
