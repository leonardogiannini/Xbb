#! /usr/bin/env python
import os, pickle, sys, ROOT
ROOT.gROOT.SetBatch(True)
from optparse import OptionParser
from myutils import BetterConfigParser, copytree, copytreePSI, ParseInfo
from myutils.FileList import FileList

print 'start prepare_environment_with_config.py'

import os
if os.path.exists("../interface/DrawFunctions_C.so"):
    print 'ROOT.gROOT.LoadMacro("../interface/DrawFunctions_C.so")'
    ROOT.gROOT.LoadMacro("../interface/DrawFunctions_C.so")

argv = sys.argv

#get files info from config
parser = OptionParser()
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="directory config")
parser.add_option("-S", "--sampleIdentifier", dest="sampleIdentifier", default="",
                              help="samples you want to run on")
parser.add_option("-f", "--fileList", dest="fileList", default="",
                              help="list of files you want to run on")
parser.add_option("-l", "--limit", dest="limit", default=None,
                              help="max number of files to process")
(opts, args) = parser.parse_args(argv)
config = BetterConfigParser()
config.read(opts.config)

fileList = FileList.decompress(opts.fileList) if len(opts.fileList)>0 else None

pathOUT = config.get('Directories','PREPout')
samplesinfo=config.get('Directories','samplesinfo')
samplefiles = config.get('Directories','samplefiles')
sampleconf = BetterConfigParser()
sampleconf.read(samplesinfo)

whereToLaunch = config.get('Configuration','whereToLaunch')

info = ParseInfo(samplesinfo, None)
samples = [x for x in info if not x.subsample and (len(opts.sampleIdentifier) == 0 or x.identifier in opts.sampleIdentifier.split(','))]
treeCopier = copytreePSI.CopyTreePSI(config=config)
if opts.limit and len(samples) > int(opts.limit):
    samples= samples[:int(opts.limit)]
for sample in samples:
    treeCopier.copytreePSI(pathIN=samplefiles, pathOUT=pathOUT, folderName=sample.identifier, skimmingCut=sample.addtreecut, fileList=fileList)
    
print 'end prepare_environment_with_config.py'
