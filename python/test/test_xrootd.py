#!/usr/bin/env python
from __future__ import print_function
import unittest
import sys
import random
sys.path.append('../')
from myutils.sampleTree import SampleTree as SampleTree
from myutils.FileLocator import FileLocator
import os

class TestXrootdMethods(unittest.TestCase):

    scratchDirectory = os.environ['SCRATCH_DIR'] if 'SCRATCH_DIR' in os.environ else '.'

    def getTree(self, path):
        fileNames = ['root://xrootd-cms.infn.it//store/group/phys_higgs/hbb/ntuples/V25/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/VHBB_HEPPY_V25_TT_TuneCUETP8M2T4_13TeV-powheg-Py8__RunIISummer16MAv2-PUMoriond17_80r2as_2016_TrancheIV_v6-v1/170202_212737/0000/tree_100.root']
        return SampleTree(fileNames)

    def test_xrootd(self):
        if 'X509_USER_PROXY' in os.environ and len(os.environ['X509_USER_PROXY'].strip()) > 0:
            path1 = 'root://xrootd-cms.infn.it//store/group/phys_higgs/hbb/ntuples/V25/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/VHBB_HEPPY_V25_TT_TuneCUETP8M2T4_13TeV-powheg-Py8__RunIISummer16MAv2-PUMoriond17_80r2as_2016_TrancheIV_v6-v1/170202_212737/0000/tree_100.root'
            tree1 = self.getTree(path1)
            print ("ENTRIES:", tree1.GetEntries())
            self.assertEqual(tree1.GetEntries(), 48442)

            fileLocator = FileLocator()

            path2 = fileLocator.removeRedirector(path1)
            print ("PATH2:", path2)
            self.assertTrue(path2.startswith('/store/group/phys_higgs/'))
            self.assertTrue(path2.endswith('/tree_100.root'))

            path3 = fileLocator.addRedirector(redirector='root://xrootd-cms.infn.it', fileName=path2)
            self.assertEqual(path1, path3)
        else:
            print("INFO: this test is skipped because no X509 proxy certificate is found which is needed to access the files!")


if __name__ == '__main__':
    unittest.main()
