#!/usr/bin/env python
from __future__ import print_function
from optparse import OptionParser
import ROOT
ROOT.gROOT.SetBatch(True)
from myutils import NewTreeCache as TreeCache
from myutils.sampleTree import SampleTree as SampleTree
from myutils import BetterConfigParser, ParseInfo
import resource
import os
import sys
import pickle
import glob
import shutil
import math

class MvaTrainingHelper(object):

    def __init__(self, config, mvaName):
        self.config = config
        self.factoryname = config.get('factory', 'factoryname')
        self.factorysettings = config.get('factory', 'factorysettings')
        self.samplesPath = config.get('Directories', 'MVAin')
        self.samplesDefinitions = config.get('Directories','samplesinfo') 
        self.samplesInfo = ParseInfo(self.samplesDefinitions, self.samplesPath)

        self.sampleFilesFolder = config.get('Directories', 'samplefiles')

        self.treeVarSet = config.get(mvaName, 'treeVarSet')
        self.MVAtype = config.get(mvaName, 'MVAtype')
        self.MVAsettings = config.get(mvaName,'MVAsettings')
        self.mvaName = mvaName

        VHbbNameSpace = config.get('VHbbNameSpace', 'library')
        ROOT.gSystem.Load(VHbbNameSpace)

        # variables
        self.MVA_Vars = {}
        self.MVA_Vars['Nominal'] = config.get(self.treeVarSet, 'Nominal').strip().split(' ')

        # samples
        backgroundSampleNames = eval(config.get(mvaName, 'backgrounds'))
        signalSampleNames = eval(config.get(mvaName, 'signals'))
        self.samples = {
            'BKG': self.samplesInfo.get_samples(backgroundSampleNames),
            'SIG': self.samplesInfo.get_samples(signalSampleNames),
        }

        self.treeCutName = config.get(mvaName, 'treeCut')
        self.treeCut = config.get('Cuts', self.treeCutName)

        self.TrainCut = config.get('Cuts', 'TrainCut') 
        self.EvalCut = config.get('Cuts', 'EvalCut')
        print("TRAINING CUT:", self.TrainCut)
        print("EVAL CUT:", self.EvalCut)

        self.globalRescale = 2.0
        
        self.trainingOutputFileName = 'mvatraining_{factoryname}_{region}.root'.format(factoryname=self.factoryname, region=mvaName)
        print("INFO: MvaTrainingHelper class created.")


    def prepare(self):

        self.trainingOutputFile = ROOT.TFile.Open(self.trainingOutputFileName, "RECREATE")
        # ----------------------------------------------------------------------------------------------------------------------
        # create TMVA factory
        # ----------------------------------------------------------------------------------------------------------------------
        self.factory = ROOT.TMVA.Factory(self.factoryname, self.trainingOutputFile, self.factorysettings)
        if self.trainingOutputFile and self.factory:
            print ("INFO: initialized MvaTrainingHelper.", self.factory) 
        else:
            print ("\x1b[31mERROR: initialization of MvaTrainingHelper failed!\x1b[0m") 

        # ----------------------------------------------------------------------------------------------------------------------
        # add sig/bkg x training/eval trees
        # ----------------------------------------------------------------------------------------------------------------------
        try:
            addBackgroundTreeMethod = self.factory.AddBackgroundTree
            addSignalTreeMethod = self.factory.AddSignalTree
            self.dataLoader = None
        except:
            print("oh no..")
            # the DataLoader wants to be called '.'
            self.dataLoader = ROOT.TMVA.DataLoader(".")
            addBackgroundTreeMethod = self.dataLoader.AddBackgroundTree
            addSignalTreeMethod = self.dataLoader.AddSignalTree

        self.sampleTrees = []
        for addTreeFcn, samples in [
                    [addBackgroundTreeMethod, self.samples['BKG']],
                    [addSignalTreeMethod, self.samples['SIG']]
                ]:
            for sample in samples:
                print ('*'*80,'\n%s\n'%sample,'*'*80)
                for additionalCut in [self.TrainCut, self.EvalCut]:
                    # cuts
                    sampleCuts = [sample.subcut]
                    if additionalCut:
                        sampleCuts.append(additionalCut)
                    # cut from the mva region
                    if self.treeCut:
                        sampleCuts.append(self.treeCut)

                    tc = TreeCache.TreeCache(
                            sample=sample,
                            cutList=sampleCuts,
                            inputFolder=self.samplesPath,
                            config=self.config,
                            debug=True
                        )
                    sampleTree = tc.getTree()
                    self.sampleTrees.append(sampleTree)
                    if sampleTree:
                        treeScale = sampleTree.getScale(sample) * self.globalRescale
                        if sampleTree.tree.GetEntries() > 0:
                            addTreeFcn(sampleTree.tree, treeScale, ROOT.TMVA.Types.kTraining if additionalCut == self.TrainCut else ROOT.TMVA.Types.kTesting)
                    else:
                        print ("\x1b[31mERROR: TREE NOT FOUND:", sample.name, " -> not cached??\x1b[0m")
                        raise Exception("CachedTreeMissing")

        if self.dataLoader:
            for var in self.MVA_Vars['Nominal']:
                self.dataLoader.AddVariable(var, 'D')
        else:
            for var in self.MVA_Vars['Nominal']:
                self.factory.AddVariable(var, 'D')

        return self

    # ----------------------------------------------------------------------------------------------------------------------
    # backup old .xml and .info files 
    # ----------------------------------------------------------------------------------------------------------------------
    def backupOldFiles(self):
        success = False
        MVAdir = self.config.get('Directories','vhbbpath')+'/python/weights/'
        backupDir = MVAdir + 'backup/'
        try:
            os.makedirs(backupDir)
        except:
            pass
        freeNumber = 1
        try:
            lastUsedBackupDirectories = sorted(glob.glob(backupDir + '/v*/'), key=lambda x: int(x.strip('/').split('/')[-1][1:]), reverse=True)
            freeNumber = 1 + int(lastUsedBackupDirectories[0].strip('/').split('/')[-1][1:]) if len(lastUsedBackupDirectories) > 0 else 1
        except Exception as e:
            print("\x1b[31mERROR: creating backup of MVA files failed!", e, "\x1b[0m")
            freeNumber = -1
        if freeNumber > -1:
            try:
                fileNamesToBackup = glob.glob(MVAdir + self.factoryname+'_'+self.mvaName + '.*')
                fileNamesToBackup += glob.glob(MVAdir + '/../mvatraining_MVA_ZllBDT_*.root')
                os.makedirs(backupDir + 'v%d/'%freeNumber)
                for fileNameToBackup in fileNamesToBackup:
                    shutil.copy(fileNameToBackup, backupDir + 'v%d/'%freeNumber)
                success = True
            except Exception as e:
                print("\x1b[31mERROR: creating backup of MVA files failed!", e, "\x1b[0m")
        return success


    def run(self):
        print('backing up old BDT files')
        self.backupOldFiles()
        # ----------------------------------------------------------------------------------------------------------------------
        # Execute TMVA
        # ----------------------------------------------------------------------------------------------------------------------
        self.factory.Verbose()
        print('Execute TMVA: factory.BookMethod("%s", "%s", "%s")'%(self.MVAtype, self.mvaName, self.MVAsettings))
        weightF = self.config.get('Weights','weightF')
        try:
            self.factory.BookMethod(self.MVAtype, self.mvaName, self.MVAsettings)
            print("ROOT 5 style TMVA found")
            self.factory.SetSignalWeightExpression(weightF)
            self.factory.SetBackgroundWeightExpression(weightF)
        except:
            print("ROOT 6 style TMVA found, using data loader object!!! >_<")
            print(" weights dir:", ROOT.TMVA.gConfig().GetIONames().fWeightFileDir)
            print(" data loader:", self.dataLoader)
            print(" type:       ", self.MVAtype)
            print(" name:       ", self.mvaName)
            print(" settings:   ", self.MVAsettings)
            ROOT.TMVA.gConfig().GetIONames().fWeightFileDir = 'weights'
            self.dataLoader.SetSignalWeightExpression(weightF)
            self.dataLoader.SetBackgroundWeightExpression(weightF)
            self.factory.BookMethod(self.dataLoader, self.MVAtype, self.mvaName, self.MVAsettings)
        print('Execute TMVA: TrainAllMethods')
        print('max mem used = %d'%(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        self.factory.TrainAllMethods()
        print('Execute TMVA: TestAllMethods')
        print('max mem used = %d'%(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        self.factory.TestAllMethods()
        print('Execute TMVA: EvaluateAllMethods')
        print('max mem used = %d'%(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        self.factory.EvaluateAllMethods()
        print('Execute TMVA: output.Write')
        print('max mem used = %d'%(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        self.trainingOutputFile.Close()
        return self

    def printInfo(self):
        #WRITE INFOFILE
        MVAdir = self.config.get('Directories','vhbbpath')+'/python/weights/'
        infofile = open(MVAdir+self.factoryname+'_'+self.mvaName+'.info','w')
        print ('@DEBUG: output infofile name')
        print (infofile)

        info=mvainfo(self.mvaName)
        info.factoryname=self.factoryname
        info.factorysettings=self.factorysettings
        info.MVAtype=self.MVAtype
        info.MVAsettings=self.MVAsettings
        info.weightfilepath=MVAdir
        info.path=self.samplesPath
        info.varset=self.treeVarSet
        info.vars=self.MVA_Vars['Nominal']
        pickle.dump(info,infofile)
        infofile.close()

    def getExpectedSignificance(self, tree, nBins, xMin, xMax, power=1.0, rescaleSig=1.0, rescaleBkg=1.0):
        hSIG = ROOT.TH1D("hSig","hSig",nBins,xMin,xMax)
        hBKG = ROOT.TH1D("hBkg","hBkg",nBins,xMin,xMax)
        print("INFO: GetEntries() = ", tree.GetEntries())
        if power != 1.0:
            print("INFO: rescale BDT score with power ", power)
        for event in tree:
            if power != 1.0:
                x = (getattr(event, self.mvaName)-xMin)/(xMax-xMin)
                if x<0:
                    x=0
                if x>0.999999:
                    x=0.999999
                value = math.pow(x, power)*(xMax-xMin)+xMin
            else:
                value = max(min(getattr(event, self.mvaName),xMax-0.00001),xMin)

            weight = event.weight
            if event.classID == 1:
                hSIG.Fill(value, weight * rescaleSig)
            else:
                hBKG.Fill(value, weight * rescaleBkg)
        ssbSum = 0.0
        sSum = 0
        bSum = 0
        sbTableFormat = "{bin: <16}{signal: <16}{background: <16}{ssb: <16}"
        print("---- nBins =", nBins, " from ", xMin, "..", xMax, "-----")
        print(sbTableFormat.format(bin="bin", signal="signal", background="background", ssb="S/sqrt(S+B)"))
        for i in range(nBins):
            ssbSum += hSIG.GetBinContent(1+i)*hSIG.GetBinContent(1+i)/(hSIG.GetBinContent(1+i) + hBKG.GetBinContent(1+i)) if (hSIG.GetBinContent(1+i) + hBKG.GetBinContent(1+i)) > 0 else 0
            sSum += hSIG.GetBinContent(1+i)
            bSum += hBKG.GetBinContent(1+i)
            ssb = hSIG.GetBinContent(1+i)/math.sqrt(hSIG.GetBinContent(1+i) + hBKG.GetBinContent(1+i)) if (hSIG.GetBinContent(1+i) + hBKG.GetBinContent(1+i)) > 0 else 0
            print(sbTableFormat.format(bin=i, signal=round(hSIG.GetBinContent(1+i),1), background=round(hBKG.GetBinContent(1+i),1), ssb=round(ssb,3)))
        expectedSignificance = math.sqrt(ssbSum)
        print(sbTableFormat.format(bin="SUM", signal=round(sSum,1), background=round(bSum,1), ssb="\x1b[34mZ=%1.3f\x1b[0m"%expectedSignificance))
        print("-"*40)
        hSIG.Delete()
        hBKG.Delete()
        return expectedSignificance, sSum, bSum

    def estimateExpectedSignificance(self):
        print("INFO: open ", self.trainingOutputFileName)
        rootFile = ROOT.TFile.Open(self.trainingOutputFileName, "READ")
        print("INFO: ->", rootFile)
        testTree = rootFile.Get('./TestTree')

        # run a few tests with different binnings and rescaling of BDT score
        self.getExpectedSignificance(testTree, 15, -0.8, 1.0)
        self.getExpectedSignificance(testTree, 15, -0.8, 0.9)
        self.getExpectedSignificance(testTree, 15, -0.8, 0.8, power=0.5)
        self.getExpectedSignificance(testTree, 15, -0.8, 0.8, power=0.33)
        self.getExpectedSignificance(testTree, 15, -0.8, 0.8, power=1.5)
        self.getExpectedSignificance(testTree, 15, -0.8, 0.8, power=2.0)

        # close to nominal binning
        print("---- ~nominal TEST -----")
        esTest, sTest, bTest = self.getExpectedSignificance(testTree, 15, -0.8, 0.8)
        print("---- ~nominal TRAINING (without correct normalization) -----")
        trainTree = rootFile.Get('./TrainTree')
        esTrain, sTrain, bTrain = self.getExpectedSignificance(trainTree, 15, -0.8, 0.8)

        # the tree ./TrainTree contains the input events for training AFTER re-balancing the classes
        # therefore for SIG/BKG separately the normalization is fixed to the one of the TEST events
        rescaleSig = 1.0*sTest/sTrain
        rescaleBkg = 1.0*bTest/bTrain
        print("---- ~nominal TRAINING -----")
        trainTree = rootFile.Get('./TrainTree')
        esTrain, sTrain, bTrain = self.getExpectedSignificance(trainTree, 15, -0.8, 0.8, rescaleSig=rescaleSig, rescaleBkg=rescaleBkg)

# read arguments
argv = sys.argv
parser = OptionParser()
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                          help="Verbose mode.")
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration file")
parser.add_option("-t","--trainingRegions", dest="trainingRegions", default='',
                      help="cut region identifier")
parser.add_option("-s", "--expectedSignificance" ,action="store_true", dest="expectedSignificance", default=False,
                          help="Compute estimate for expected significance (without systematics)")
(opts, args) = parser.parse_args(argv)
if opts.config =="":
        opts.config = ["config"]

# Import after configure to get help message
from myutils import BetterConfigParser, mvainfo, ParseInfo

# load config
config = BetterConfigParser()
config.read(opts.config)

# initialize
trainingRegions = opts.trainingRegions.split(',')
if len(trainingRegions) > 1:
    print ("ERROR: not implemented!")
    exit(1)
for trainingRegion in trainingRegions:
    th = MvaTrainingHelper(config=config, mvaName=trainingRegion)
    if opts.expectedSignificance:
        th.estimateExpectedSignificance()
    else:
        th.prepare().run()
        th.printInfo()
        try:
            th.estimateExpectedSignificance()
        except:
            pass

