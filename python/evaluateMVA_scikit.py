#!/usr/bin/env python
from __future__ import print_function
import sys
import ROOT
#suppres the EvalInstace conversion warning bug
import warnings
warnings.filterwarnings( action='ignore', category=RuntimeWarning, message='creating converter.*' )
from optparse import OptionParser
import pickle
from myutils.FileList import FileList
from myutils.FileLocator import FileLocator
from myutils.sampleTree import SampleTree as SampleTree
from sklearn.neural_network import MLPClassifier
from sklearn.externals import joblib
from sklearn import preprocessing
import numpy as np
import math

#CONFIGURE
ROOT.gROOT.SetBatch(True)
parser = OptionParser()
parser.add_option("-D", "--discr", dest="discr", default="", help="discriminators to be added")
parser.add_option("-S", "--sampleIdentifier", dest="sampleIdentifier", default="", help="samples you want to run on")
parser.add_option("-C", "--config", dest="config", default=[], action="append", help="configuration file")
parser.add_option("-f", "--fileList", dest="fileList", default="", help="list of files you want to run on")
parser.add_option("-o","--force", action="store_true", dest="force", default=False, help="force overwriting of already cached files")
(opts, args) = parser.parse_args(sys.argv)
if opts.config == "":
        opts.config = "config"

#Import after configure to get help message
from myutils import BetterConfigParser, ParseInfo, MvaEvaluator
config = BetterConfigParser()
config.read(opts.config)
anaTag = config.get("Analysis", "tag")

# get list of files to process
fileLocator = FileLocator(config=config)
if len(opts.fileList) > 0:
    filelist = FileList.decompress(opts.fileList) if len(opts.fileList) > 0 else None
    print ("len(filelist)", len(filelist))
    if len(filelist) > 0:
        print ("filelist[0]:", filelist[0])
else:
    filelist = SampleTree({'name': opts.sampleIdentifier, 'folder': config.get('Directories', 'MVAin')}, countOnly=True, splitFilesChunkSize=-1, config=config).getSampleFileNameChunks()[0]
    print ("INFO: no file list given, use all files!")
    print (len(filelist), filelist)

# read paths and sample info
samplesinfo = config.get('Directories', 'samplesinfo')
systematics = config.get('systematics', 'systematics')
INpath = config.get('Directories', 'MVAin')
OUTpath = config.get('Directories', 'MVAout')
tmpDir = config.get('Directories', 'scratch')
info = ParseInfo(samplesinfo,INpath)

#load the namespace
VHbbNameSpace = config.get('VHbbNameSpace','library')
ROOT.gSystem.Load(VHbbNameSpace)

# ------------------------------------------------------------------------------------------
# helper class to evaluate scikit classifiers and write MVA score as new branch
# ------------------------------------------------------------------------------------------
class SciKitEvaluator(object):
    def __init__(self, name, sampleTree, classifier, variables, systematics, scaler=None, outputscaler=None):
        self.name = name
        self.sampleTree = sampleTree
        self.clf = joblib.load(classifier)
        self.scaler = joblib.load(scaler) if scaler else None
        self.outputscaler = outputscaler if outputscaler else (lambda x: x)
        self.variables = variables
        self.systematics = systematics

        # add formulas for input variables to sampleTree
        for systematic in systematics:
            for variable in self.variables[systematic]:
                if variable not in self.sampleTree.getFormulas():
                    self.sampleTree.addFormula(variable)

        # define output branches to store MVA scores
        self.sampleTree.addOutputBranch(
                    branchName=self.name,
                    branchType='f',
                    length=len(systematics),
                    formula=self.evaluate,
                    leaflist=':'.join(self.systematics)+'/F',
                )

    def evaluate(self, tree=None, destinationArray=None):
        # now evaluate this MVA for all the systematics and write scores to the array
        for i, systematic in enumerate(self.systematics):

            # fill input vector
            X = np.array([[self.sampleTree.evaluate(variable) for variable in self.variables[systematic]]], dtype=np.float32)

            # preprocessing of input data if necessary
            if self.scaler:
                X = self.scaler.transform(X)

            # evaluate classifier
            destinationArray[i] = self.clf.predict_proba(X)[0][1]


# find matching sample identifier
# TODO: simplify
matchingSamples = [x for x in info if x.identifier==opts.sampleIdentifier and not x.subsample]
if len(matchingSamples) != 1:
    print ("need exactly 1 sample identifier as input with -S !!", matchingSamples)
    exit(1)
sample = matchingSamples[0]

# process all given files
for fileName in filelist:
    localFileName = fileName.split('/')[-1] #TODO! # fileLocator.getFilenameAfterPrep(fileName)
    inputFileName = "{path}/{subfolder}/{filename}".format(path=INpath, subfolder=sample.identifier, filename=localFileName)
    outputFileName = "{path}/{subfolder}/{filename}".format(path=OUTpath, subfolder=sample.identifier, filename=localFileName)
    tmpFileName = "{path}/{subfolder}/{filename}".format(path=tmpDir, subfolder=sample.identifier, filename=localFileName)
    outputFolder = '/'.join(outputFileName.split('/')[:-1])
    tmpFolder = '/'.join(tmpFileName.split('/')[:-1])
    fileLocator.makedirs(tmpFolder)
    fileLocator.makedirs(outputFolder)
    if not fileLocator.isValidRootFile(outputFileName) or opts.force:
        # load sample tree
        sampleTree = SampleTree([inputFileName], config=config)
        if not sampleTree.tree:
            print ("\x1b[31mERROR: file does not exist or is broken, will be SKIPPED!\x1b[0m")
            continue

        systematics = config.get('systematics','systematics').split(' ')
        print("systematics:", systematics)

        classifiers = opts.discr.split(',')
        for classifier in classifiers:
            varset = config.get(classifier, 'treeVarSet')
            if sample.type == 'DATA':
                variables = {x: config.get(varset, systematics[0]).split(' ') for x in systematics}
            else:
                variables = {x: config.get(varset,x).split(' ') for x in systematics}
            sciKitEvaluator = SciKitEvaluator(
                        name=classifier,
                        sampleTree=sampleTree,
                        classifier=config.get(classifier, 'classifier'),
                        scaler=config.get(classifier, 'scaler'),
                        outputscaler=config.get(classifier, 'outputscaler'),
                        variables=variables,
                        systematics=systematics,
                    )

        # define output file
        sampleTree.addOutputTree(tmpFileName, cut='1', branches='*')
        sampleTree.process()

        # copy temporary file to output folder
        if opts.force and fileLocator.exists(outputFileName):
            fileLocator.rm(outputFileName)

        if fileLocator.isValidRootFile(tmpFileName):
            fileLocator.cp(tmpFileName, outputFileName)
            #fileLocator.rm(tmpFileName)
            print ("copy: ", tmpFileName, " --> ", outputFileName)
            if fileLocator.isValidRootFile(outputFileName):
                fileLocator.rm(tmpFileName)
            else:
                print("TMP:", tmpFileName)
                print("OUT:", outputFileName)
                print("\x1b[31mERROR: copy from tmp to output failed!\x1b[0m")
        else:
            print("\x1b[31mERROR: temporary file is zombie or disappeared!", tmpFileName ,"\x1b[0m")
    else:
        print("SKIP: ", localFileName)
