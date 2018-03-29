import json
import os
import array

class ElectronSFfromJSON(object):
    
    def __init__(self, jsonFiles=None):
        self.jsonFiles = jsonFiles
        self.debug = 'XBBDEBUG' in os.environ

        self.data = {}
        for jsonFileName in self.jsonFiles:
            with open(jsonFileName, 'r') as jsonFile:
                self.data.update(json.load(jsonFile))

        self.idIsoSfName = 'doubleEleIDISO2017'
        self.triggerLegNames = ['doubleEleTriggerLeg1', 'doubleEleTriggerLeg2']

        self.idIsoSf = self.getEtaPtTable(self.idIsoSfName)
        self.triggerSf = [self.getEtaPtTable(x) for x in self.triggerLegNames]

    def customInit(self, initVars):
        sample = initVars['sample']
        self.isData = sample.type == 'DATA'
        self.branches = []
        self.branchBuffers = {}
        self.lastEntry = -1
        if not self.isData:
            for branchName in ['electronSF', 'electronSF_IdIso', 'electronSF_trigger']:
                self.branchBuffers[branchName] = array.array('f', [0])
                self.branches.append({'name': branchName, 'formula': self.getBranch, 'arguments': branchName}) 

    def getBranches(self):
        return self.branches

    # read from buffers which have been filled in processEvent()    
    def getBranch(self, event, arguments=None):
        self.processEvent(event)
        if arguments:
            return self.branchBuffers[arguments][0]

    def processEvent(self, tree):
        currentEntry = tree.GetReadEntry()
        # if current entry has not been processed yet
        if currentEntry != self.lastEntry and not self.isData:
            self.lastEntry = currentEntry

            # require two electrons      
            if tree.nElectron >= 2:
                sfIdIso = self.getIdIsoSf(tree.Electron_eta[0], tree.Electron_pt[0]) * self.getIdIsoSf(tree.Electron_eta[1], tree.Electron_pt[1]) 
                sfTrigger = self.getTriggerSf(tree.Electron_eta[0], tree.Electron_pt[0], tree.Electron_eta[1], tree.Electron_pt[1])
                self.branchBuffers['electronSF'][0] = sfIdIso * sfTrigger
                self.branchBuffers['electronSF_IdIso'][0] = sfIdIso
                self.branchBuffers['electronSF_trigger'][0] = sfTrigger
            else:
                self.branchBuffers['electronSF'][0] = 1.0
                self.branchBuffers['electronSF_IdIso'][0] = 1.0
                self.branchBuffers['electronSF_trigger'][0] = 1.0
        return True


    def getEtaPtTable(self, tableName):
        table = []
        if tableName in self.data:
            for etaKey in self.data[tableName]['eta_pt_ratio'].keys():
                etaName = etaKey.split(':')[0]
                if etaName != "eta":
                    raise Exception("JsonFileError")
                etaRange = eval(etaKey.split(':')[1])
                for ptKey in self.data[tableName]['eta_pt_ratio'][etaKey].keys():
                    ptName = ptKey.split(':')[0]
                    if ptName != "pt":
                        raise Exception("JsonFileError")
                    ptRange = eval(ptKey.split(':')[1])
                    table.append({'eta_min': etaRange[0], 'eta_max': etaRange[1], 'pt_min': ptRange[0], 'pt_max': ptRange[1], 'value': self.data[tableName]['eta_pt_ratio'][etaKey][ptKey]['value']})
        return table

    def find(self, table, eta, pt, default=1.0):
        for sfBin in table:
            if sfBin['eta_min'] <= eta and eta < sfBin['eta_max'] and sfBin['pt_min'] <= pt and pt < sfBin['pt_max']:
                return sfBin['value']
        if self.debug:
            print "not found in table: eta:", eta, "pt:", pt, "->returning default =", default
        return default

    def getIdIsoSf(self, eta, pt):
        sf = self.find(self.idIsoSf, eta, pt)
        if self.debug:
            print "id/iso eta:", eta, "pt:", pt, "->", sf
        return sf
    
    def getTriggerSf(self, eta1, pt1, eta2, pt2):
        leg1 = self.find(self.triggerSf[0], eta1, pt1)
        leg2 = self.find(self.triggerSf[1], eta2, pt2)
        if self.debug:
            print "leg1: eta:", eta1, " pt:", pt1, "->", leg1
            print "leg2: eta:", eta2, " pt:", pt2, "->", leg2
            print "-->", leg1*leg2
        return leg1*leg2

if __name__ == "__main__":
    sfObject = ElectronSFfromJSON([
            'weights/Zll/Electrons/VHbb2ElectronIDISO2017.json',
            'weights/Zll/Electrons/VHbb2ElectronTriggerLeg12017.json',
            'weights/Zll/Electrons/VHbb2ElectronTriggerLeg22017.json',
        ])
    print sfObject.getIdIsoSf(0.5, 50)
    print sfObject.getIdIsoSf(-2.5, 50)
    print sfObject.getIdIsoSf(2.5, 250)
    print sfObject.getIdIsoSf(-0.5, 250)
    print sfObject.getTriggerSf(0.5, 50, 1.1, 40)
