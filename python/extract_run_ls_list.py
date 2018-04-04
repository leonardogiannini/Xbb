#!/usr/bin/env python
import ROOT
from myutils.sampleTree import SampleTree

#pp
#sampleTree = SampleTree('VHbbPostNano2017_V2_DoubleEG.txt', 'Events', xrootdRedirector='root://t3dcachedb03.psi.ch:1094/')
sampleTree = SampleTree('VHbbPostNano2017_V2_DoubleMuon.txt', 'Events', xrootdRedirector='root://t3dcachedb03.psi.ch:1094/')
outputFileName = 'existing_lumis_pp_DoubleMuon.txt'

#nano
#sampleTree = SampleTree('2017-94X-Nano01-DoubleEG.txt', 'Events', xrootdRedirector='root://xrootd-cms.infn.it/')
#outputFileName = 'existing_lumis_nano.txt'

sampleTree.tree.SetBranchStatus("*", 0)
sampleTree.tree.SetBranchStatus("run", 1)
sampleTree.tree.SetBranchStatus("luminosityBlock", 1)
runLumi = []
for i in sampleTree:
    #if [i.run, i.luminosityBlock] not in runLumi and i.run>=302030 and i.run <= 303434:
    #    runLumi.append([i.run, i.luminosityBlock])
    if [i.run, i.luminosityBlock] not in runLumi:
        runLumi.append([i.run, i.luminosityBlock])
print runLumi
with open(outputFileName, 'w') as f:
    f.write("%r"%runLumi)


